# PostalBI — La Poste Tunisienne

Plateforme d'analyse prédictive et décisionnelle des flux de colis.

## Stack

| Couche | Technologie |
|--------|-------------|
| Backend / API | FastAPI (Python 3.12) |
| Frontend | React 18 + TypeScript + Vite |
| Style | Tailwind CSS |
| Graphiques | Recharts |
| Base de données | PostgreSQL 16 (schéma en étoile) |
| Auth | JWT + bcrypt (RBAC 3 rôles) |
| Conteneurisation | Docker Compose |

## Démarrage rapide

### Avec Docker (recommandé)

```bash
cp backend/.env.example backend/.env
# Éditer backend/.env si nécessaire (clés LLM, etc.)

docker compose up --build
```

Puis initialiser les données mock :
```bash
docker compose exec backend python -m app.db.seed
```

L'application est disponible sur :
- **Frontend** : http://localhost:5173
- **API + Swagger** : http://localhost:8000/docs

### Sans Docker (développement local)

**Backend :**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # adapter DATABASE_URL
uvicorn app.main:app --reload
python -m app.db.seed
```

**Frontend :**
```bash
cd frontend
npm install
npm run dev
```

## Comptes de test

| Utilisateur | Mot de passe | Rôle | Périmètre |
|-------------|--------------|------|-----------|
| admin | Admin@2024 | Administrateur | — |
| responsable | Responsable@2024 | Responsable décisionnel | National |
| agent_tunis | Agent@2024 | Agent régional | Tunis |
| agent_sfax | Agent@2024 | Agent régional | Sfax |

## Structure du projet

```
postalytics/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # auth, dashboard, users, chatbot
│   │   ├── core/           # config, security, deps
│   │   ├── db/             # session, seed (données mock)
│   │   ├── models/         # modèles SQLAlchemy
│   │   ├── schemas/        # schémas Pydantic
│   │   ├── services/       # llm_service (Phase 4)
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── src/
│       ├── components/     # layout, auth
│       ├── pages/          # Login, Dashboard, Chatbot, Prévisions, Admin
│       ├── services/       # axios client
│       ├── store/          # Zustand (auth)
│       └── types/          # TypeScript types
└── docker-compose.yml
```

## Activer l'assistant IA (Phase 4)

1. Obtenir une clé OpenAI ou Mistral
2. Dans `backend/.env` :
   ```
   OPENAI_API_KEY=sk-...
   LLM_PROVIDER=openai
   ```
3. Redémarrer le backend — aucune autre modification nécessaire

## Brancher les vraies données

1. Adapter le script ETL pour peupler les tables `dim_*` et `fait_colis`
2. Pointer `DATABASE_URL` vers la vraie base PostgreSQL
3. Ne pas relancer le seed mock

Le code de l'application ne change pas — seule la source de données change.
