# 📮 Postalytics — La Poste Tunisienne

**Postalytics** est une plateforme d'analyse décisionnelle des flux de colis de
La Poste Tunisienne.

Le projet combine **Data Engineering, Data Warehousing, développement web et
intelligence artificielle** afin de centraliser, analyser et explorer les
données de colis à travers une interface web interactive.

L'application permet notamment de consulter les indicateurs liés aux flux de
colis et d'interagir avec les données en langage naturel grâce à un assistant
basé sur un Large Language Model (LLM).

---

## 🎯 Objectifs

Les principaux objectifs du projet sont :

- Centraliser les données de colis dans une base PostgreSQL
- Explorer, nettoyer et transformer les données sources
- Construire un Data Warehouse selon un schéma en étoile
- Analyser les flux de colis nationaux et internationaux
- Fournir des tableaux de bord décisionnels
- Permettre l'interrogation des données en langage naturel
- Intégrer un Large Language Model (LLM) pour assister l'utilisateur
- Fournir une architecture modulaire et facilement maintenable

---

## ✨ Fonctionnalités

- 📊 Dashboard décisionnel
- 📦 Analyse des flux de colis
- 🏢 Gestion des bureaux et services
- 🗄️ Data Warehouse PostgreSQL
- 🔐 Authentification JWT
- 👥 Gestion des rôles et permissions (RBAC)
- 💬 Assistant conversationnel pour interroger les données
- 🤖 Intégration de GPT-OSS-120B via Groq
- 📈 Visualisation interactive des données
- 🐳 Conteneurisation avec Docker Compose

---

# 🏗️ Architecture

```text
                         ┌──────────────────────┐
                         │    React Frontend    │
                         │   TypeScript / Vite  │
                         └───────────┬──────────┘
                                     │
                                     │ HTTP / REST
                                     ▼
                         ┌──────────────────────┐
                         │    FastAPI Backend   │
                         │       Python         │
                         └───────┬────────┬─────┘
                                 │        │
                    ┌────────────┘        └────────────┐
                    ▼                                 ▼
           ┌─────────────────┐              ┌──────────────────┐
           │   PostgreSQL    │              │       LLM        │
           │  Data Warehouse │              │  GPT-OSS-120B    │
           │   Star Schema   │              │      Groq        │
           └─────────────────┘              └──────────────────┘
                    ▲
                    │
                    │ ETL
                    │
           ┌─────────────────┐
           │   Source Data   │
           │      CSV        │
           └─────────────────┘
```

---

# 🧰 Technologies

| Domaine | Technologie |
|---|---|
| Backend / API | FastAPI |
| Langage backend | Python 3.12 |
| Frontend | React 18 |
| Langage frontend | TypeScript |
| Build tool | Vite |
| CSS | Tailwind CSS |
| Visualisation | Recharts |
| Base de données | PostgreSQL 16 |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Authentification | JWT + bcrypt |
| Data Processing | Pandas / NumPy |
| Data Warehouse | PostgreSQL — Star Schema |
| LLM | OpenAI GPT-OSS-120B |
| LLM Provider | Groq |
| Conteneurisation | Docker / Docker Compose |
| Version Control | Git / GitHub |

---

# 📊 Data Warehouse

Le projet utilise un **Data Warehouse PostgreSQL** organisé selon un
**schéma en étoile (Star Schema)**.

## Table de faits

```text
fait_colis
```

La table de faits contient les informations et mesures principales liées aux
colis.

## Dimensions

```text
dim_temps
dim_bureau
dim_service
dim_destination
```

Architecture simplifiée :

```text
                    dim_temps
                        │
                        │
                        ▼
dim_bureau ─────── fait_colis ─────── dim_service
                        │
                        │
                        ▼
                dim_destination
```

Cette architecture permet d'analyser les flux de colis selon différents axes :

- Temps
- Bureau
- Service
- Destination
- Type de colis
- Flux national / international

---

# 🔄 Pipeline de données

Les données suivent un pipeline de traitement en plusieurs étapes.

```text
                  CSV Sources
                      │
                      ▼
                 Exploration
                      │
                      ▼
                   Cleaning
                      │
                      ▼
                Transformation
                      │
                      ▼
                     ETL
                      │
                      ▼
              PostgreSQL DWH
                      │
                      ▼
                  FastAPI
                      │
                      ▼
                React Frontend
```

## Notebooks

Les notebooks sont organisés selon les différentes étapes du pipeline :

```text
notebooks/
├── 01_exploration.ipynb
├── 02_cleaning.ipynb
├── 03_transformation.ipynb
└── 04_etl_postgresql.ipynb
```

### 1. Exploration

Analyse initiale des données afin d'identifier notamment :

- Valeurs manquantes
- Doublons
- Valeurs incohérentes
- Formats incorrects
- Valeurs aberrantes
- Incohérences dans les identifiants

### 2. Cleaning

Nettoyage et standardisation des données.

### 3. Transformation

Transformation des données nettoyées afin de les adapter au modèle
analytique du Data Warehouse.

### 4. ETL

Chargement des données transformées dans PostgreSQL.

---

# 🤖 Assistant IA

Postalytics intègre un assistant permettant aux utilisateurs de poser des
questions sur les données en langage naturel.

### Exemple

```text
Utilisateur :

Combien de colis ont été envoyés en 2025 ?
```

Le système suit le processus suivant :

```text
Question utilisateur
        │
        ▼
FastAPI
        │
        ▼
GPT-OSS-120B
        │
        ▼
Interprétation / génération de requête
        │
        ▼
PostgreSQL
        │
        ▼
Résultat
        │
        ▼
Réponse utilisateur
```

## Modèle utilisé

```text
OpenAI GPT-OSS-120B
```

Le modèle est utilisé via l'API **Groq**.

Cette architecture permet de conserver le LLM séparé de la logique métier
du backend.

---

# 🔐 Configuration

Les variables sensibles sont stockées dans un fichier `.env` et ne doivent
jamais être publiées dans le repository.

Créer :

```text
backend/.env
```

à partir de :

```text
backend/.env.example
```

Exemple :

```env
DATABASE_URL=postgresql://user:password@db:5432/database

SECRET_KEY=your_secret_key

GROQ_API_KEY=your_groq_api_key
```

> ⚠️ Ne jamais commit le fichier `.env`.
>
> ⚠️ Ne jamais publier une clé API, un token ou un mot de passe dans GitHub.

---

# 🚀 Installation

## Prérequis

Avant de commencer, installer :

- Git
- Docker
- Docker Compose
- Node.js
- Python 3.12

---

# 🐳 Démarrage avec Docker

## 1. Cloner le repository

```bash
git clone <repository-url>
cd postalytics
```

## 2. Configurer l'environnement

Créer le fichier :

```bash
cp backend/.env.example backend/.env
```

Puis renseigner les variables nécessaires dans :

```text
backend/.env
```

## 3. Construire et démarrer les services

```bash
docker compose up --build
```

## 4. Initialiser les données fictives

Pour initialiser la base avec les données mock :

```bash
docker compose exec backend python -m app.db.seed
```

> ⚠️ Le script `seed` est utilisé uniquement pour les données fictives de
> développement et de démonstration.

---

# 🌐 Accès à l'application

Une fois les services démarrés :

### Frontend

```text
http://localhost:5173
```

### Backend API

```text
http://localhost:8000
```

### Documentation Swagger

```text
http://localhost:8000/docs
```

---

# 💻 Développement local

## Backend

Accéder au dossier backend :

```bash
cd backend
```

Créer un environnement virtuel :

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

Installer les dépendances :

```bash
pip install -r requirements.txt
```

Créer le fichier d'environnement :

```bash
cp .env.example .env
```

Lancer le serveur FastAPI :

```bash
uvicorn app.main:app --reload
```

Initialiser les données mock :

```bash
python -m app.db.seed
```

---

## Frontend

Accéder au dossier frontend :

```bash
cd frontend
```

Installer les dépendances :

```bash
npm install
```

Lancer le serveur de développement :

```bash
npm run dev
```

---

# 📁 Structure du projet

```text
postalytics/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── auth.py
│   │   │       ├── dashboard.py
│   │   │       ├── users.py
│   │   │       └── chatbot.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   │
│   │   ├── db/
│   │   │   ├── database.py
│   │   │   └── seed.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   └── llm.py
│   │   │
│   │   └── main.py
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── store/
│   │   └── types/
│   │
│   ├── package.json
│   └── Dockerfile
│
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_cleaning.ipynb
│   ├── 03_transformation.ipynb
│   └── 04_etl_postgresql.ipynb
│
├── data/
│
├── docs/
│
├── tests/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# 🔌 API

Le backend est développé avec FastAPI.

La documentation interactive est disponible à :

```text
http://localhost:8000/docs
```

## Exemple de requête

Endpoint :

```http
POST /query
```

Exemple :

```json
{
  "query": "Combien de colis ont été envoyés en 2025 ?"
}
```

Le backend traite la question, interagit avec le LLM et utilise les données
PostgreSQL pour produire la réponse.

---

# 🧪 Tests

Les tests backend peuvent être exécutés avec :

```bash
pytest
```

---

# 📦 Données

Les données sources utilisées pour le projet peuvent être volumineuses ou
confidentielles et ne sont donc pas nécessairement incluses dans le repository.

Le dossier `data/` est destiné à organiser les données utilisées pendant le
pipeline :

```text
data/
├── raw/
└── processed/
```

Les données brutes et transformées peuvent être exclues du versionnement
Git selon leur taille et leur nature.

---

# 🔒 Sécurité

Les informations sensibles ne doivent jamais être ajoutées au repository.

Les éléments suivants doivent rester dans les variables d'environnement :

- Clés API
- Tokens
- Mots de passe
- Clés secrètes
- Identifiants de base de données

Le fichier suivant doit rester local :

```text
.env
```

Le repository contient uniquement un modèle de configuration :

```text
.env.example
```

---

# 🚧 État du projet

Le projet est actuellement en développement.

## Data Engineering

- [x] Exploration des données
- [x] Nettoyage des données
- [x] Transformation des données
- [x] Conception du Data Warehouse
- [x] Modélisation en schéma en étoile
- [x] ETL vers PostgreSQL

## Backend

- [x] API FastAPI
- [x] Connexion PostgreSQL
- [x] Authentification JWT
- [x] Gestion des rôles
- [x] Endpoints API
- [x] Intégration du LLM

## Frontend

- [x] Interface React
- [x] Authentification
- [x] Dashboard
- [x] Visualisation des données
- [x] Interface chatbot

## Intelligence artificielle

- [x] Intégration d'un LLM
- [x] Intégration de GPT-OSS-120B via Groq
- [ ] Optimisation des prompts
- [ ] Amélioration de la génération des requêtes
- [ ] Tests approfondis du chatbot

## À venir

- [ ] Tests complets de l'application
- [ ] Optimisation des performances
- [ ] Amélioration du système de requêtes en langage naturel
- [ ] Déploiement

---

# 🔮 Évolutions possibles

Les évolutions futures du projet peuvent inclure :

- 📈 Prévision des flux de colis
- 🚨 Détection automatique des anomalies
- 🌍 Analyse géographique avancée
- 📊 Nouveaux indicateurs décisionnels
- 🤖 Amélioration du système de questions en langage naturel
- 🔎 Recherche sémantique dans les données
- ⚡ Optimisation des performances
- ☁️ Déploiement dans le cloud

---

# 👩‍💻 Auteur

**Eya Touati**

Étudiante en Big Data & Data Analytics

Tunisie

---

# 📄 Licence

Ce projet est développé dans un cadre académique.
