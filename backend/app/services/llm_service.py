import json
import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.schemas.schemas import ChatMessage, ChatResponse

# ── Schéma du Data Warehouse ──────────────────────────────────────────────────
DW_SCHEMA = """
Tables PostgreSQL disponibles :

fait_colis : id, poids, montant, type_source ('normal'|'express'),
             heure_formatee, tranche_horaire, est_anomalie,
             temps_id, bureau_id, service_id, destination_id

dim_temps : id, date_complete, jour, mois INT(1-12), trimestre INT(1-4),
            annee INT, jour_semaine, saison, est_weekend, est_ferie,
            mois_islamique, evenement_islamique

dim_bureau : id, id_bureau_src, ville, gouvernorat, type_bureau

dim_destination : id, code_iso_pays, pays_dest, ville_dest,
                  portee ('NATIONAL'|'INTERNATIONAL')

dim_service : id, code_service ('CP'|'UP'|'RR'|'NOR'|'EMS-N'|'EMS-I'|'RPP-I'),
              type_service ('NORMAL'|'EXPRESS_NORMAL'|'EXPRESS_PERSONNALISE'),
              label, portee ('NATIONAL'|'INTERNATIONAL')
"""

# ── Règles SQL strictes ───────────────────────────────────────────────────────
SQL_RULES = """
REGLES ABSOLUES :
1. ENUMs — valeurs EXACTES :
   portee       → 'NATIONAL' | 'INTERNATIONAL'
   type_service → 'NORMAL' | 'EXPRESS_NORMAL' | 'EXPRESS_PERSONNALISE'
   type_source  → 'normal' | 'express'
   NE JAMAIS utiliser ILIKE sur ces colonnes.

2. Gouvernorats — toujours ILIKE :
   WHERE db.gouvernorat ILIKE '%Sfax%'
   Valeurs : Tunis, Sfax, Sousse, Bizerte, Nabeul, Monastir, Mahdia,
   Kairouan, Kasserine, Sidi Bouzid, Gabès, Gafsa, Tozeur, Kébili,
   Médenine, Tataouine, Béja, Jendouba, Kef, Siliana, Zaghouan,
   Ariana, Ben Arous, Manouba

3. Colonnes temporelles INTEGER :
   annee → WHERE dt.annee = 2026  (JAMAIS EXTRACT)
   mois  → WHERE dt.mois = 6
   "cette année" = 2026 | "l'année dernière" = 2025

4. Volume vs CA :
   "combien de colis" | "volume" → COUNT(fc.id)
   "chiffre d'affaires" | "CA"   → SUM(fc.montant)

5. Pays :
   WHERE dd.code_iso_pays = 'FR'
   Codes : FR=France, IT=Italie, DE=Allemagne, GB=Royaume-Uni,
           SA=Arabie Saoudite, AE=Émirats, CA=Canada, MA=Maroc

6. Jointures selon le filtre :
   Date  → JOIN dim_temps dt ON fc.temps_id = dt.id
   Région → JOIN dim_bureau db ON fc.bureau_id = db.id
   Service → JOIN dim_service ds ON fc.service_id = ds.id
   Destination → JOIN dim_destination dd ON fc.destination_id = dd.id

7. LIMIT 50 obligatoire.
8. Sans année explicite → pas de filtre temporel.
9. Question impossible en SQL → sql: null
"""

# ── Prompt système ────────────────────────────────────────────────────────────
SYSTEM_PROMPT = f"""Tu es un assistant analytique expert SQL pour La Poste Tunisienne.

{DW_SCHEMA}

{SQL_RULES}

Réponds UNIQUEMENT avec ce JSON sur une seule ligne :
{{"sql": "SELECT ... LIMIT 50", "answer": "réponse courte en français", "confidence": "high|low"}}
Si impossible : {{"sql": null, "answer": "explication", "confidence": "none"}}
"""

# ── Réponses mock ─────────────────────────────────────────────────────────────
MOCK_RESPONSES = [
    {
        "keywords": ["volume", "combien", "total", "colis"],
        "sql": "SELECT COUNT(*) as total FROM fait_colis",
        "answer": "Le volume total est de 1 247 651 colis sur 2023-2026.",
    },
    {
        "keywords": ["france"],
        "sql": "SELECT COUNT(*) as nb FROM fait_colis fc JOIN dim_destination dd ON fc.destination_id = dd.id WHERE dd.code_iso_pays = 'FR'",
        "answer": "La France est la première destination internationale.",
    },
    {
        "keywords": ["gouvernorat", "region"],
        "sql": "SELECT db.gouvernorat, COUNT(*) as total FROM fait_colis fc JOIN dim_bureau db ON fc.bureau_id = db.id GROUP BY db.gouvernorat ORDER BY total DESC LIMIT 10",
        "answer": "Classement des gouvernorats par volume.",
    },
]

# ── Sécurité SQL ──────────────────────────────────────────────────────────────
FORBIDDEN = ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER"]

def is_safe(sql: str) -> bool:
    sql_upper = sql.upper()
    return not any(kw in sql_upper for kw in FORBIDDEN)


class LLMService:

    def __init__(self):
        self.groq_key   = settings.GROQ_API_KEY
        self.groq_model = settings.GROQ_MODEL
        self.provider   = settings.LLM_PROVIDER

    # ── Point d'entrée principal ──────────────────────────────────────────────

    async def text_to_sql_and_answer(
        self, question: str, history: list, region_context: str, db: Session
    ) -> ChatResponse:

        # Mode mock si pas de clé
        if not self.groq_key or self.provider == "mock":
            return self._mock_response(question)

        try:
            # Étape 1 — Générer le SQL via Groq
            raw = await self._call_groq(question, history, region_context)

            # Étape 2 — Parser la réponse JSON
            sql_query, answer, confidence = self._parse(raw)

            # Sécurité
            if sql_query and not is_safe(sql_query):
                return ChatResponse(answer="⚠️ Requête non autorisée.", sql_query=None)

            # Pas de SQL généré
            if not sql_query:
                return ChatResponse(answer=answer or "Je ne peux pas répondre.", sql_query=None)

            # Étape 3 — Exécuter le SQL
            try:
                result  = db.execute(text(sql_query))
                rows    = result.fetchall()
                cols    = list(result.keys())
                data    = [dict(zip(cols, row)) for row in rows[:20]]
            except Exception as e:
                return ChatResponse(
                    answer=f"❌ Erreur SQL : {str(e)[:150]}",
                    sql_query=sql_query,
                )

            # Résultat vide
            if not data or all(v in (None, 0, "") for row in data for v in row.values()):
                return ChatResponse(
                    answer="🔍 Aucune donnée trouvée. Vérifiez les filtres ou reformulez.",
                    sql_query=sql_query,
                )

            # Étape 4 — Reformuler en français naturel
            answer = await self._reformuler(question, data, region_context)
            return ChatResponse(answer=answer, sql_query=sql_query)

        except Exception as e:
            return ChatResponse(
                answer=f"❌ Service IA indisponible : {str(e)[:100]}",
                sql_query=None,
            )

    # ── Appel Groq ────────────────────────────────────────────────────────────

    async def _call_groq(self, question: str, history: list, region_context: str) -> str:
        # Construire les messages
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT + f"\nContexte : {region_context}"}
        ]
        # Ajouter les 4 derniers messages de l'historique
        for msg in history[-4:]:
            messages.append({"role": msg.role, "content": msg.content})
        # Ajouter la question actuelle
        messages.append({"role": "user", "content": question})

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model":       self.groq_model,
                    "messages":    messages,
                    "temperature": 0.0,
                    "max_tokens":  600,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    # ── Reformulation en français ─────────────────────────────────────────────

    async def _reformuler(self, question: str, data: list, region_context: str) -> str:
        # Résumé des données
        if len(data) == 1 and len(data[0]) == 1:
            val     = list(data[0].values())[0]
            data_str = f"Résultat : {val}"
        else:
            data_str = f"Top résultats : {str(data[:5])}"

        prompt = (
            f"Question : {question}\n"
            f"Données : {data_str}\n"
            f"Contexte : {region_context}\n\n"
            f"Reformule en UNE phrase claire en français. "
            f"Cite les chiffres précis. Ne mentionne pas SQL."
        )

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.groq_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model":       self.groq_model,
                    "messages":    [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens":  200,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()

    # ── Parser la réponse JSON ────────────────────────────────────────────────

    def _parse(self, raw: str):
        clean = raw.strip()

        # Retirer markdown
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()

        # Extraire le JSON
        import re
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if match:
            try:
                parsed     = json.loads(match.group())
                sql        = parsed.get("sql")
                answer     = parsed.get("answer", "")
                confidence = parsed.get("confidence", "high")
                return sql, answer, confidence
            except Exception:
                pass

        return None, clean, "none"

    # ── Mock ──────────────────────────────────────────────────────────────────

    def _mock_response(self, question: str) -> ChatResponse:
        q = question.lower()
        for mock in MOCK_RESPONSES:
            if any(kw in q for kw in mock["keywords"]):
                return ChatResponse(answer=mock["answer"], sql_query=mock["sql"])
        return ChatResponse(
            answer="Mode démonstration. Configurez GROQ_API_KEY pour activer l'assistant.",
            sql_query=None,
        )