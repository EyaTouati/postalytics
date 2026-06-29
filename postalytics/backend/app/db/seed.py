"""
Générateur de données fictives — La Poste Tunisienne.

Respecte EXACTEMENT la structure des classes (section 3 du brief).
Ce module est le SEUL endroit où les données fictives sont définies.
Quand les vraies données arrivent : remplacer l'appel à seed_mock_data()
par le script ETL réel — rien d'autre ne change.

Usage :
    python -m app.db.seed
"""
import random
from datetime import date, timedelta

from faker import Faker
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.db.session import SessionLocal, engine
from app.models.models import (
    Base, DimClient, DimDestination, DimOrigine, DimService, DimTemps,
    FaitColis, NatureColis, Portee, TypeService, User, UserRole,
)

fake = Faker("fr_FR")
random.seed(42)

# ── Référentiels fixes ──────────────────────────────────────────────────────────

REGIONS_TUNISIE = [
    "Tunis", "Sfax", "Sousse", "Bizerte", "Gabès",
    "Ariana", "Gafsa", "Kairouan", "Monastir", "Nabeul",
]

VILLES_PAR_REGION = {
    "Tunis": ["Tunis", "La Marsa", "Le Bardo"],
    "Sfax": ["Sfax", "Sakiet Ezzit", "Chihia"],
    "Sousse": ["Sousse", "Hammam Sousse", "Msaken"],
    "Bizerte": ["Bizerte", "Menzel Bourguiba", "Mateur"],
    "Gabès": ["Gabès", "El Hamma", "Matmata"],
    "Ariana": ["Ariana", "La Soukra", "Raoued"],
    "Gafsa": ["Gafsa", "Métlaoui", "El Ksar"],
    "Kairouan": ["Kairouan", "Sbikha", "Haffouz"],
    "Monastir": ["Monastir", "Ksar Hellal", "Jemmal"],
    "Nabeul": ["Nabeul", "Hammamet", "Kelibia"],
}

# Destinations internationales fréquentes
DESTINATIONS_INTL = [
    {"pays": "France", "region": "Île-de-France"},
    {"pays": "France", "region": "Provence-Alpes-Côte d'Azur"},
    {"pays": "Allemagne", "region": "Bavière"},
    {"pays": "Italie", "region": "Lombardie"},
    {"pays": "Espagne", "region": "Catalogne"},
    {"pays": "Belgique", "region": "Bruxelles"},
    {"pays": "Canada", "region": "Québec"},
    {"pays": "Maroc", "region": "Grand Casablanca"},
    {"pays": "Algérie", "region": "Alger"},
    {"pays": "Arabie Saoudite", "region": "Riyad"},
    {"pays": "Émirats Arabes Unis", "region": "Dubaï"},
    {"pays": "Sénégal", "region": "Dakar"},
]

SERVICES = [
    {"type_service": TypeService.NORMAL, "tarif_base": 3.5, "delai_standard": 5},
    {"type_service": TypeService.EXPRESS_NORMAL, "tarif_base": 7.0, "delai_standard": 2},
    {"type_service": TypeService.EXPRESS_PERSONNALISE, "tarif_base": 12.0, "delai_standard": 1},
]


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _montant_from_service(type_service: TypeService, poids: float) -> float:
    tarifs = {
        TypeService.NORMAL: 3.5,
        TypeService.EXPRESS_NORMAL: 7.0,
        TypeService.EXPRESS_PERSONNALISE: 12.0,
    }
    return round(tarifs[type_service] * max(1.0, poids), 2)


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


# ── Seed principal ──────────────────────────────────────────────────────────────

def seed_mock_data(n_colis: int = 3000):
    db: Session = SessionLocal()
    try:
        # Vérifier si déjà seedé
        if db.query(User).count() > 0:
            print("Base déjà initialisée — seed ignoré.")
            return

        print("Création du schéma…")
        Base.metadata.create_all(bind=engine)

        # ── 1. Services ─────────────────────────────────────────────────────────
        services = []
        for s in SERVICES:
            svc = DimService(**s)
            db.add(svc)
            services.append(svc)
        db.flush()

        # ── 2. Origines (combinaisons région/ville tunisienne) ──────────────────
        origines = []
        for region, villes in VILLES_PAR_REGION.items():
            for ville in villes:
                orig = DimOrigine(ville=ville, region=region, pays="Tunisie")
                db.add(orig)
                origines.append(orig)
        db.flush()

        # ── 3. Destinations ─────────────────────────────────────────────────────
        destinations_nationales = []
        for region, villes in VILLES_PAR_REGION.items():
            for ville in villes:
                dest = DimDestination(
                    pays="Tunisie", region=region, portee=Portee.NATIONAL
                )
                db.add(dest)
                destinations_nationales.append(dest)

        destinations_intl = []
        for d in DESTINATIONS_INTL:
            dest = DimDestination(
                pays=d["pays"], region=d["region"], portee=Portee.INTERNATIONAL
            )
            db.add(dest)
            destinations_intl.append(dest)
        db.flush()

        all_destinations = destinations_nationales + destinations_intl

        # ── 4. Clients ──────────────────────────────────────────────────────────
        clients = []
        for _ in range(500):
            region = random.choice(REGIONS_TUNISIE)
            c = DimClient(
                nom=fake.name(),
                ville=random.choice(VILLES_PAR_REGION[region]),
            )
            db.add(c)
            clients.append(c)
        db.flush()

        # ── 5. Dimension Temps (2 ans) ──────────────────────────────────────────
        start_date = date(2023, 1, 1)
        end_date = date(2024, 12, 31)
        temps_map: dict[date, DimTemps] = {}

        for d in _date_range(start_date, end_date):
            t = DimTemps(
                date_complete=d,
                jour=d.day,
                mois=d.month,
                trimestre=(d.month - 1) // 3 + 1,
                annee=d.year,
                semaine=d.isocalendar()[1],
                jour_semaine=JOURS_FR[d.weekday()],
                est_weekend=d.weekday() >= 5,
            )
            db.add(t)
            temps_map[d] = t
        db.flush()

        # ── 6. Faits Colis ──────────────────────────────────────────────────────
        all_dates = list(temps_map.keys())
        # Saisonnalité : plus de colis en nov-déc et en été
        weights = [
            3.0 if d.month in (11, 12, 7, 8) else
            1.5 if d.month in (3, 4, 5, 6) else 1.0
            for d in all_dates
        ]

        # 70% national, 30% international
        dest_weights = [
            0.7 / len(destinations_nationales) if d.portee == Portee.NATIONAL
            else 0.3 / len(destinations_intl)
            for d in all_destinations
        ]

        for i in range(n_colis):
            chosen_date = random.choices(all_dates, weights=weights, k=1)[0]
            service = random.choices(
                services,
                weights=[0.5, 0.3, 0.2],  # Normal > Express normal > Express perso
                k=1,
            )[0]
            destination = random.choices(all_destinations, weights=dest_weights, k=1)[0]
            poids = round(random.uniform(0.1, 25.0), 2)

            colis = FaitColis(
                num_colis=f"TN{str(i + 1).zfill(7)}",
                poids=poids,
                montant=_montant_from_service(service.type_service, poids),
                nature=random.choices(
                    [NatureColis.MARCHANDISE, NatureColis.DOCUMENT],
                    weights=[0.65, 0.35],
                )[0],
                temps_id=temps_map[chosen_date].id,
                service_id=service.id,
                expediteur_id=random.choice(clients).id,
                destinataire_id=random.choice(clients).id,
                origine_id=random.choice(origines).id,
                destination_id=destination.id,
            )
            db.add(colis)

        db.flush()

        # ── 7. Utilisateurs applicatifs ─────────────────────────────────────────
        seed_users = [
            User(
                username="admin",
                email="admin@poste.tn",
                hashed_password=get_password_hash("Admin@2024"),
                role=UserRole.ADMIN,
                region_assignee=None,
            ),
            User(
                username="responsable",
                email="responsable@poste.tn",
                hashed_password=get_password_hash("Responsable@2024"),
                role=UserRole.RESPONSABLE,
                region_assignee=None,
            ),
            User(
                username="agent_tunis",
                email="agent.tunis@poste.tn",
                hashed_password=get_password_hash("Agent@2024"),
                role=UserRole.AGENT_REGIONAL,
                region_assignee="Tunis",
            ),
            User(
                username="agent_sfax",
                email="agent.sfax@poste.tn",
                hashed_password=get_password_hash("Agent@2024"),
                role=UserRole.AGENT_REGIONAL,
                region_assignee="Sfax",
            ),
        ]
        for u in seed_users:
            db.add(u)

        db.commit()
        print(f"✅ Seed terminé — {n_colis} colis + {len(seed_users)} utilisateurs créés.")
        print("\nComptes de test :")
        print("  admin / Admin@2024")
        print("  responsable / Responsable@2024")
        print("  agent_tunis / Agent@2024  (région : Tunis)")
        print("  agent_sfax  / Agent@2024  (région : Sfax)")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur seed : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_mock_data()
