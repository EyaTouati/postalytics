# Postalytics — Intelligent Postal Data Analytics

**Postalytics** est une plateforme décisionnelle intelligente dédiée à l’analyse des flux d’envois postaux de **La Poste Tunisienne**.

Le projet transforme des données brutes de colis en informations exploitables à travers un pipeline combinant **Data Engineering, Data Warehousing, Data Analytics, Machine Learning et Intelligence Artificielle**.

L'objectif est de permettre aux utilisateurs d'explorer les flux postaux, suivre les indicateurs clés et interroger les données en langage naturel à travers une interface web interactive.

---

## 🎯 Problem & Solution

Les données de flux postaux proviennent de différentes sources et nécessitent plusieurs étapes avant de pouvoir être exploitées pour l'analyse décisionnelle.

Postalytics met en place une chaîne complète :

```text
Raw Data
   ↓
Exploration & Cleaning
   ↓
Transformation & ETL
   ↓
PostgreSQL Data Warehouse
   ↓
Analytics & Machine Learning
   ↓
FastAPI
   ↓
React Dashboard
   ↓
AI Assistant
```

La plateforme permet ainsi de passer de **données brutes à des indicateurs, analyses et prédictions accessibles aux utilisateurs**.

---

## ✨ Key Features

### 📊 Decision Support

* Interactive dashboards
* KPI monitoring
* Analysis of postal flows
* National / international analysis
* Analysis by time, bureau, service and destination
* Interactive visualizations

### 🔄 Data Engineering

* Data exploration
* Data cleaning
* Data transformation
* ETL pipeline
* Data Warehouse construction
* Star Schema modelling

### 🤖 Machine Learning

Postalytics intègre plusieurs approches de Machine Learning pour l'analyse des flux :

* **K-Means** — segmentation des données
* **Prophet** — prévision des séries temporelles
* **Isolation Forest** — détection d'anomalies

### 💬 AI Assistant

Un assistant conversationnel permet d'interroger les données en langage naturel.

Exemple :

```text
"Combien de colis ont été envoyés en 2025 ?"
```

Le système traite la question, exploite le contexte des données et retourne une réponse à l'utilisateur.

### 🔐 Security & Access Control

* JWT authentication
* Password hashing with bcrypt
* Role-Based Access Control (RBAC)
* Environment-based configuration
* Sensitive credentials excluded from Git

### 🐳 Deployment

* Docker
* Docker Compose
* Containerized backend, frontend and PostgreSQL services

---

# 🏗️ Architecture

```text
                         ┌─────────────────────────┐
                         │     React Frontend      │
                         │   TypeScript / Vite     │
                         └────────────┬────────────┘
                                      │
                                  HTTP / REST
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │      FastAPI Backend    │
                         │        Python 3.12      │
                         └───────┬─────────┬───────┘
                                 │         │
                                 │         │
                                 ▼         ▼
                    ┌────────────────┐  ┌───────────────┐
                    │   PostgreSQL   │  │  AI Assistant │
                    │ Data Warehouse │  │      LLM      │
                    │  Star Schema   │  │    via Groq   │
                    └───────▲────────┘  └───────────────┘
                            │
                            │ ETL
                            │
                    ┌───────┴────────┐
                    │   Source Data  │
                    │      CSV       │
                    └────────────────┘
```

---

# 🔄 Data Pipeline

The data pipeline is organized into four main stages:

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
PostgreSQL Data Warehouse
```

### 1. Exploration

Initial analysis of the source datasets to identify:

* Missing values
* Duplicates
* Inconsistent values
* Incorrect formats
* Outliers
* Identifier inconsistencies

### 2. Cleaning

Standardization and preparation of the data before loading it into the analytical model.

### 3. Transformation

Transformation of the cleaned data into structures compatible with the Data Warehouse.

### 4. ETL

Loading the transformed data into PostgreSQL.

The data-processing work is documented through notebooks located in:

```text
data_pipeline/notebooks/
```

---

# 🗄️ Data Warehouse

Postalytics uses **PostgreSQL** as its analytical database and implements a **Star Schema**.

### Fact Table

```text
fait_colis
```

The fact table contains the main measures and references associated with postal shipments.

### Dimensions

```text
dim_temps
dim_bureau
dim_service
dim_destination
```

Simplified model:

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

This structure allows analysis by:

* Time
* Bureau
* Service
* Destination
* Shipment type
* National / international flow

---

# 🤖 Machine Learning

Postalytics integrates Machine Learning into the analytical workflow.

### K-Means

Used to identify groups or segments within the postal data.

### Prophet

Used for time-series forecasting of postal flows.

### Isolation Forest

Used to identify potentially abnormal observations in the data.

The ML components are designed to complement the BI layer by moving from descriptive analysis toward **segmentation, forecasting and anomaly detection**.

---

# 💬 AI Assistant

The platform includes a conversational interface for querying postal data using natural language.

Simplified workflow:

```text
User Question
      │
      ▼
FastAPI
      │
      ▼
LLM
      │
      ▼
Query / Data Processing
      │
      ▼
PostgreSQL
      │
      ▼
Result
      │
      ▼
User Response
```

The project uses **GPT-OSS-120B through Groq** for the LLM component.

The LLM remains separated from the main business logic through the backend service layer.

---

# 🛠️ Technology Stack

| Area             | Technologies               |
| ---------------- | -------------------------- |
| Backend          | FastAPI, Python 3.12       |
| Frontend         | React 18, TypeScript, Vite |
| Styling          | Tailwind CSS               |
| Visualization    | Recharts                   |
| Database         | PostgreSQL 16              |
| ORM              | SQLAlchemy                 |
| Validation       | Pydantic                   |
| Authentication   | JWT, bcrypt                |
| Data Processing  | Pandas, NumPy              |
| Machine Learning | Scikit-learn, Prophet      |
| LLM              | GPT-OSS-120B               |
| LLM Provider     | Groq                       |
| Containers       | Docker, Docker Compose     |
| Version Control  | Git, GitHub                |

---

# 📁 Project Structure

```text
postalytics/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
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
│   └── Dockerfile.dev
│
├── data_pipeline/
│   ├── data/
│   ├── etl/
│   ├── notebooks/
│   └── requirements_datascience.txt
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

# 🚀 Getting Started

## Prerequisites

* Git
* Docker Desktop
* Docker Compose

## 1. Clone the repository

```bash
git clone https://github.com/EyaTouati/postalytics.git
cd postalytics
```

## 2. Configure environment variables

Create your local environment file from the provided template:

```bash
cp .env.example .env
```

Then configure the required variables locally.

> Never commit `.env` or expose API keys, passwords or secret keys.

## 3. Start the application

```bash
docker compose up --build
```

The application starts the main services:

```text
PostgreSQL
FastAPI Backend
React Frontend
```

---

# 🌐 Application

Once the containers are running:

**Frontend**

```text
http://localhost:5173
```

**Backend API**

```text
http://localhost:8000
```

**Swagger API Documentation**

```text
http://localhost:8000/docs
```

---

# 📊 Data & Analytics

The project works with postal shipment datasets covering national and international flows.

The pipeline is designed to support:

```text
Data Collection
      ↓
Data Quality
      ↓
Data Warehouse
      ↓
Descriptive Analytics
      ↓
Machine Learning
      ↓
Decision Support
```

This architecture separates the different stages of the data lifecycle while keeping them connected through the analytical database.

---

# 🔐 Security

Sensitive configuration is handled through environment variables.

The repository does **not** contain:

* API keys
* Passwords
* Database credentials
* Secret keys

Only the configuration template is versioned:

```text
.env.example
```

---

# 🚧 Project Status

The main application architecture is implemented and running locally through Docker Compose.

### Implemented

* Data exploration and preprocessing
* ETL pipeline
* PostgreSQL Data Warehouse
* Star Schema
* FastAPI backend
* React frontend
* Interactive dashboards
* JWT authentication
* RBAC
* Machine Learning components
* AI assistant
* Dockerized development environment

### Possible Future Improvements

* Automated data ingestion
* Advanced forecasting
* More anomaly detection scenarios
* Geographic analytics
* Semantic search
* Performance optimization
* Cloud deployment

---

# 🎓 Academic Context

Postalytics was developed as an academic project around the analysis of postal shipment flows, with the objective of applying an end-to-end data architecture combining:

**Data Engineering → Data Warehousing → Analytics → Machine Learning → AI**

---

# 👩‍💻 Author

**Eya Touati**

Licence Sciences Informatiques — Big Data & Data Analytics
ISAMM — Tunisia

[GitHub](https://github.com/EyaTouati) · [LinkedIn](https://linkedin.com/in/eya-touati-6777a531)

---

## 📄 License

This project was developed in an academic context.
