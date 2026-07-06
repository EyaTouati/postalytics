"""
Service LLM — Texte vers SQL (Phase 4).

Pour activer un vrai fournisseur :
  1. Renseigner la clé API dans .env (OPENAI_API_KEY ou MISTRAL_API_KEY)
  2. Mettre LLM_PROVIDER="openai" ou "mistral" dans .env
  3. Le service bascule automatiquement — aucune autre modification nécessaire.

Schéma SQL injecté dans le prompt : toujours synchronisé avec models.py.
"""
import json
from typing import Optional

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.schemas.schemas import ChatMessage, ChatResponse

# Schéma du Data Warehouse injecté dans le system prompt du LLM
DW_SCHEMA = """
TABLE fait_colis (
  id SERIAL PRIMARY KEY,
  num_colis VARCHAR(50),
  id_bordereau INTEGER,
  poids FLOAT,
  montant FLOAT,
  nature VARCHAR(20),
  ref_paiement VARCHAR(5),
  type_source VARCHAR(20),   -- 'normal' | 'express'
  est_anomalie BOOLEAN,
  temps_id INT REFERENCES dim_temps(id),
  service_id INT REFERENCES dim_service(id),
  bureau_id INT REFERENCES dim_bureau(id),
  destination_id INT REFERENCES dim_destination(id)
);

TABLE dim_temps (
  id, date_complete DATE, jour INT, mois INT, trimestre INT,
  annee INT, semaine INT, saison VARCHAR, est_weekend BOOL
);

TABLE dim_bureau (
  id, id_bureau_src VARCHAR, code_postal VARCHAR,
  cite VARCHAR, ville VARCHAR, gouvernorat VARCHAR
);

TABLE dim_destination (
  id, code_iso_pays VARCHAR, pays_dest VARCHAR,
  ville_dest VARCHAR, cite_dest VARCHAR,
  code_postal_dest VARCHAR, portee VARCHAR
);

TABLE dim_service (
  id, code_service VARCHAR, type_service VARCHAR,
  portee VARCHAR, label VARCHAR,
  tarif_base FLOAT, delai_standard INT
);
"""
SYSTEM_PROMPT = f"""Tu es un assistant analytique expert en SQL pour La Poste Tunisienne.
Tu as accès au Data Warehouse suivant :

{DW_SCHEMA}

Règles :
- Génère UNIQUEMENT des requêtes SELECT (jamais INSERT, UPDATE, DELETE, DROP).
- Limite toujours les résultats à 100 lignes maximum (LIMIT 100).
- Réponds en JSON avec deux clés : "sql" (la requête) et "answer" (la réponse en français).
- Si la question ne peut pas être traduite en SQL, mets null dans "sql" et réponds directement.
- {{region_context}}
"""

# Questions/réponses mock pour le mode développement
MOCK_RESPONSES = {
    "volume": {
        "sql": "SELECT COUNT(*) as total FROM fait_colis",
        "answer": "En mode mock : le volume total de colis dans la base est de 3 000 (données fictives). Connectez un LLM réel pour des réponses précises sur vos vraies données."
    },
    "france": {
        "sql": "SELECT COUNT(*) FROM fait_colis JOIN dim_destination ON fait_colis.destination_id = dim_destination.id WHERE dim_destination.pays = 'France'",
        "answer": "En mode mock : environ 450 colis ont été envoyés vers la France sur les données fictives. Configurez OPENAI_API_KEY ou MISTRAL_API_KEY pour des analyses réelles."
    },
    "default": {
        "sql": None,
        "answer": "Je suis en mode mock (aucune clé LLM configurée). Pour activer l'assistant conversationnel, renseignez OPENAI_API_KEY ou MISTRAL_API_KEY dans le fichier .env."
    }
}


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        self.openai_key = settings.OPENAI_API_KEY
        self.mistral_key = settings.MISTRAL_API_KEY

    async def text_to_sql_and_answer(
        self,
        question: str,
        history: list[ChatMessage],
        region_context: str,
        db: Session,
    ) -> ChatResponse:
        # Mode mock si aucune clé configurée
        if not self.openai_key and not self.mistral_key:
            return self._mock_response(question)

        # Appel LLM réel
        raw = await self._call_llm(question, history, region_context)
        parsed = self._parse_llm_response(raw)

        sql_query = parsed.get("sql")
        answer = parsed.get("answer", "")

        # Exécuter la requête SQL si présente
        if sql_query:
            try:
                result = db.execute(text(sql_query))
                rows = result.fetchall()
                # Passer les données brutes au LLM pour reformulation
                answer = await self._reformulate(question, sql_query, rows, region_context)
            except Exception as e:
                answer = f"La requête SQL a échoué : {e}. Reformulez votre question."
                sql_query = None

        return ChatResponse(answer=answer, sql_query=sql_query)

    async def _call_llm(self, question: str, history: list, region_context: str) -> str:
        """Appel au LLM (OpenAI ou Mistral)."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(region_context=region_context)}
        ]
        for msg in history[-6:]:  # 6 derniers messages pour le contexte
            messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": question})

        if self.provider == "openai" and self.openai_key:
            return await self._call_openai(messages)
        elif self.provider == "mistral" and self.mistral_key:
            return await self._call_mistral(messages)
        else:
            raise ValueError("Aucun fournisseur LLM configuré.")

    async def _call_openai(self, messages: list) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": messages,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _call_mistral(self, messages: list) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.mistral_key}"},
                json={
                    "model": "mistral-small-latest",
                    "messages": messages,
                    "temperature": 0.1,
                },
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _reformulate(self, question: str, sql: str, rows: list, region_context: str) -> str:
        """Reformule les résultats bruts en langage naturel."""
        data_str = str(rows[:20])  # Limiter pour le contexte
        prompt = (
            f"Question posée : {question}\n"
            f"SQL exécuté : {sql}\n"
            f"Résultats (20 premières lignes) : {data_str}\n"
            f"Contexte : {region_context}\n\n"
            "Reformule ces résultats en une réponse claire et concise en français."
        )
        return await self._call_llm(prompt, [], region_context)

    def _parse_llm_response(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"sql": None, "answer": raw}

    def _mock_response(self, question: str) -> ChatResponse:
        question_lower = question.lower()
        if "volume" in question_lower or "combien" in question_lower:
            data = MOCK_RESPONSES["volume"]
        elif "france" in question_lower:
            data = MOCK_RESPONSES["france"]
        else:
            data = MOCK_RESPONSES["default"]
        return ChatResponse(answer=data["answer"], sql_query=data["sql"])
