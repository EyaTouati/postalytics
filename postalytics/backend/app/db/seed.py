"""
Générateur de données fictives — La Poste Tunisienne.

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
    Base,
    DimBureau,
    DimDestination,
    DimService,
    DimTemps,
    FaitColis,
    NatureColis,
    Portee,
    TypeService,
    User,
    UserRole,
)

fake = Faker("fr_FR")
random.seed(42)

# ── Référentiels fixes ────────────────────────────────────────────────────────

GOUVERNORATS = [
    "Tunis",
    "Sfax",
    "Sousse",
    "Bizerte",
    "Gabès",
    "Ariana",
    "Gafsa",
    "Kairouan",
    "Monastir",
    "Nabeul",
]

VILLES_PAR_GOUVERNORAT = {
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

DESTINATIONS_INTL = [
    {"pays_dest": "France", "ville_dest": "Paris", "code_iso_pays": "FR"},
    {"pays_dest": "France", "ville_dest": "Marseille", "code_iso_pays": "FR"},
    {"pays_dest": "Allemagne", "ville_dest": "Munich", "code_iso_pays": "DE"},
    {"pays_dest": "Italie", "ville_dest": "Milan", "code_iso_pays": "IT"},
    {"pays_dest": "Espagne", "ville_dest": "Barcelone", "code_iso_pays": "ES"},
    {"pays_dest": "Belgique", "ville_dest": "Bruxelles", "code_iso_pays": "BE"},
    {"pays_dest": "Canada", "ville_dest": "Montréal", "code_iso_pays": "CA"},
    {"pays_dest": "Maroc", "ville_dest": "Casablanca", "code_iso_pays": "MA"},
    {"pays_dest": "Algérie", "ville_dest": "Alger", "code_iso_pays": "DZ"},
    {"pays_dest": "Arabie Saoudite", "ville_dest": "Riyad", "code_iso_pays": "SA"},
    {"pays_dest": "Émirats Arabes Unis", "ville_dest": "Dubaï", "code_iso_pays": "AE"},
    {"pays_dest": "Sénégal", "ville_dest": "Dakar", "code_iso_pays": "SN"},
]

# Mapping CodeService → TypeService (correspond aux vraies données)
SERVICES = [
    {
        "code_service": "NOR",
        "type_service": TypeService.NORMAL,
        "portee": Portee.NATIONAL,
        "label": "Normal",
        "tarif_base": 3.5,
        "delai_standard": 5,
    },
    {
        "code_service": "EMS-N",
        "type_service": TypeService.EXPRESS_NORMAL,
        "portee": Portee.NATIONAL,
        "label": "Express normal",
        "tarif_base": 7.0,
        "delai_standard": 2,
    },
    {
        "code_service": "EMS-I",
        "type_service": TypeService.EXPRESS_PERSONNALISE,
        "portee": Portee.INTERNATIONAL,
        "label": "Express personnalisé international",
        "tarif_base": 12.0,
        "delai_standard": 3,
    },
    {
        "code_service": "RPP-I",
        "type_service": TypeService.EXPRESS_PERSONNALISE,
        "portee": Portee.INTERNATIONAL,
        "label": "Remise contre preuve international",
        "tarif_base": 10.0,
        "delai_standard": 4,
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────


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


def _get_saison(mois: int) -> str:
    if mois in (3, 4, 5):
        return "Printemps"
    elif mois in (6, 7, 8):
        return "Été"
    elif mois in (9, 10, 11):
        return "Automne"
    else:
        return "Hiver"


JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


# ── Seed principal ────────────────────────────────────────────────────────────


def seed_mock_data(n_colis: int = 3000):
    db: Session = SessionLocal()
    try:
        print("Création du schéma…")
        Base.metadata.create_all(bind=engine)

        print("Aucune donnée de test ajoutée.")
        db.commit()
        bureaux = []
        compteur_bureau = 1
        for gouvernorat, villes in VILLES_PAR_GOUVERNORAT.items():
            for ville in villes:
                bureau = DimBureau(
                    id_bureau_src=f"BUR{str(compteur_bureau).zfill(3)}",
                    code_postal=f"{random.randint(1000, 9999)}",
                    cite=ville,
                    ville=ville,
                    gouvernorat=gouvernorat,
                )
                db.add(bureau)
                bureaux.append(bureau)
                compteur_bureau += 1
        db.flush()

        # ── 3. Destinations ───────────────────────────────────────────────────
        destinations_nationales = []
        for gouvernorat, villes in VILLES_PAR_GOUVERNORAT.items():
            for ville in villes:
                dest = DimDestination(
                    code_iso_pays="TN",
                    pays_dest="Tunisie",
                    ville_dest=ville,
                    cite_dest=ville,
                    code_postal_dest=f"{random.randint(1000, 9999)}",
                    portee=Portee.NATIONAL,
                )
                db.add(dest)
                destinations_nationales.append(dest)

        destinations_intl = []
        for d in DESTINATIONS_INTL:
            dest = DimDestination(
                code_iso_pays=d["code_iso_pays"],
                pays_dest=d["pays_dest"],
                ville_dest=d["ville_dest"],
                cite_dest=d["ville_dest"],
                code_postal_dest=None,
                portee=Portee.INTERNATIONAL,
            )
            db.add(dest)
            destinations_intl.append(dest)
        db.flush()

        all_destinations = destinations_nationales + destinations_intl

        # ── 4. Dimension Temps (3 ans — 2024, 2025, 2026) ────────────────────
        start_date = date(2024, 1, 1)
        end_date = date(2026, 6, 30)
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
                saison=_get_saison(d.month),
                est_weekend=d.weekday() >= 5,
            )
            db.add(t)
            temps_map[d] = t
        db.flush()

        # ── 5. Faits Colis ────────────────────────────────────────────────────
        all_dates = list(temps_map.keys())

        # Saisonnalité : plus de colis en nov-déc et en été
        weights = [
            3.0
            if d.month in (11, 12, 7, 8)
            else 1.5
            if d.month in (3, 4, 5, 6)
            else 1.0
            for d in all_dates
        ]

        # 70% national, 30% international
        dest_weights = [
            0.7 / len(destinations_nationales)
            if d.portee == Portee.NATIONAL
            else 0.3 / len(destinations_intl)
            for d in all_destinations
        ]

        for i in range(n_colis):
            chosen_date = random.choices(all_dates, weights=weights, k=1)[0]
            service = random.choices(
                services,
                weights=[0.5, 0.2, 0.2, 0.1],  # NOR > EMS-N > EMS-I > RPP-I
                k=1,
            )[0]
            destination = random.choices(all_destinations, weights=dest_weights, k=1)[0]
            poids = round(random.uniform(0.1, 25.0), 2)

            colis = FaitColis(
                num_colis=f"TN{str(i + 1).zfill(7)}",
                id_bordereau=random.randint(100000, 999999),
                poids=poids,
                montant=_montant_from_service(service.type_service, poids),
                nature=None,  # absent des vraies données
                ref_paiement=random.choice(["C", "P", None]),
                type_source="normal" if service.code_service == "NOR" else "express",
                est_anomalie=None,  # rempli par ML Phase 3
                temps_id=temps_map[chosen_date].id,
                service_id=service.id,
                bureau_id=random.choice(bureaux).id,
                destination_id=destination.id,
            )
            db.add(colis)

        db.flush()

        # ── 6. Utilisateurs applicatifs ───────────────────────────────────────
        seed_users = [
            User(
                username="admin",
                email="admin@poste.tn",
                hashed_password=get_password_hash("***REDACTED_DEMO_PASSWORD***"),
                role=UserRole.ADMIN,
                region_assignee=None,
            ),
            User(
                username="responsable",
                email="responsable@poste.tn",
                hashed_password=get_password_hash("***REDACTED_DEMO_PASSWORD***"),
                role=UserRole.RESPONSABLE,
                region_assignee=None,
            ),
            User(
                username="agent_tunis",
                email="agent.tunis@poste.tn",
                hashed_password=get_password_hash("***REDACTED_DEMO_PASSWORD***"),
                role=UserRole.AGENT_REGIONAL,
                region_assignee="Tunis",
            ),
            User(
                username="agent_sfax",
                email="agent.sfax@poste.tn",
                hashed_password=get_password_hash("***REDACTED_DEMO_PASSWORD***"),
                role=UserRole.AGENT_REGIONAL,
                region_assignee="Sfax",
            ),
        ]
        for u in seed_users:
            db.add(u)

        db.commit()
        print(
            f"✅ Seed terminé — {n_colis} colis + {len(seed_users)} utilisateurs créés."
        )
        print("\nComptes de test :")
        print("  admin        / ***REDACTED_DEMO_PASSWORD***")
        print("  responsable  / ***REDACTED_DEMO_PASSWORD***")
        print("  agent_tunis  / ***REDACTED_DEMO_PASSWORD***  (gouvernorat : Tunis)")
        print("  agent_sfax   / ***REDACTED_DEMO_PASSWORD***  (gouvernorat : Sfax)")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur seed : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_mock_data()
