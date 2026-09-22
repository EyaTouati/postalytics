"""
Générateur de données fictives — La Poste Tunisienne.

Ce module est le SEUL endroit où les données fictives sont définies.
Quand les vraies données arrivent : remplacer l'appel à seed_mock_data()
par le script ETL réel — rien d'autre ne change.

Usage :
    python -m app.db.seed
"""

import random
import os
import secrets
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

# ── Référentiels ──────────────────────────────────────────────────────────────

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

SERVICES = [
    {
        "code_service": "NOR",
        "type_service": TypeService.NORMAL,
        "portee": Portee.NATIONAL,
        "label": "Normal",
        "description": "Colis normal",
        "tarif_base": 3.5,
        "delai_standard": 5,
    },
    {
        "code_service": "EMS-N",
        "type_service": TypeService.EXPRESS_NORMAL,
        "portee": Portee.NATIONAL,
        "label": "Express normal",
        "description": "Express Mail Service National",
        "tarif_base": 7.0,
        "delai_standard": 2,
    },
    {
        "code_service": "EMS-I",
        "type_service": TypeService.EXPRESS_PERSONNALISE,
        "portee": Portee.INTERNATIONAL,
        "label": "Express personnalisé international",
        "description": "Express Mail Service International",
        "tarif_base": 12.0,
        "delai_standard": 3,
    },
    {
        "code_service": "RPP-I",
        "type_service": TypeService.EXPRESS_PERSONNALISE,
        "portee": Portee.INTERNATIONAL,
        "label": "Remise contre preuve international",
        "description": "Livré par DHL Express",
        "tarif_base": 10.0,
        "delai_standard": 4,
    },
]

# Jours fériés tunisiens (MM-DD)
JOURS_FERIES = [
    "01-01",
    "03-20",
    "04-09",
    "05-01",
    "07-25",
    "08-13",
    "10-15",
]

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]


def _seed_password(role: str) -> str:
    return os.getenv(f"SEED_{role.upper()}_PASSWORD") or secrets.token_urlsafe(18)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_saison(mois: int) -> str:
    if mois in (3, 4, 5):
        return "Printemps"
    elif mois in (6, 7, 8):
        return "Été"
    elif mois in (9, 10, 11):
        return "Automne"
    else:
        return "Hiver"


def _get_tranche(heure_int: int) -> str:
    h = heure_int // 100
    if 6 <= h < 10:
        return "Matin (6h-10h)"
    elif 10 <= h < 13:
        return "Milieu matin (10h-13h)"
    elif 13 <= h < 15:
        return "Après-midi (13h-15h)"
    elif 15 <= h < 18:
        return "Fin après-midi (15h-18h)"
    elif 18 <= h < 21:
        return "Soir (18h-21h)"
    else:
        return "Hors horaires"


def _format_heure(heure_int: int) -> str:
    h = heure_int // 100
    m = heure_int % 100
    if h < 12:
        return f"{h:02d}:{m:02d} AM"
    elif h == 12:
        return f"12:{m:02d} PM"
    else:
        return f"{h - 12:02d}:{m:02d} PM"


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


# ── Seed principal ────────────────────────────────────────────────────────────


def seed_mock_data(n_colis: int = 3000):
    db: Session = SessionLocal()
    try:
        print("Création du schéma…")
        Base.metadata.create_all(bind=engine)

        if db.query(FaitColis).count() > 0:
            print("Base déjà initialisée — seed ignoré.")
            return

        # ── 1. Services ───────────────────────────────────────────────────────
        services = []
        for s in SERVICES:
            svc = DimService(**s)
            db.add(svc)
            services.append(svc)
        db.flush()

        # ── 2. Bureaux ────────────────────────────────────────────────────────
        bureaux = []
        compteur = 1
        for gouvernorat, villes in VILLES_PAR_GOUVERNORAT.items():
            for ville in villes:
                bureau = DimBureau(
                    id_bureau_src=f"BUR{str(compteur).zfill(3)}",
                    code_postal=f"{random.randint(1000, 9999)}",
                    cite=ville,
                    ville=ville,
                    gouvernorat=gouvernorat,
                    type_bureau="Bureau",  # ← AJOUT
                )
                db.add(bureau)
                bureaux.append(bureau)
                compteur += 1
        db.flush()

        # ── 3. Destinations ───────────────────────────────────────────────────
        destinations = []
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
                destinations.append(dest)

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
            destinations.append(dest)
        db.flush()

        # ── 4. Dimension Temps (2023-2026) ────────────────────────────────────
        start_date = date(2023, 1, 1)
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
                num_semaine_mois=(d.day - 1) // 7 + 1,  # ← AJOUT
                jour_semaine=JOURS_FR[d.weekday()],
                saison=_get_saison(d.month),
                est_weekend=d.weekday() >= 5,
                est_ferie=d.strftime("%m-%d") in JOURS_FERIES,  # ← AJOUT
                mois_islamique=None,  # ← AJOUT (simplifié pour mock)
                num_mois_islamique=None,  # ← AJOUT
                annee_hijri=None,  # ← AJOUT
                evenement_islamique=None,  # ← AJOUT
                impact_islamique=None,  # ← AJOUT
            )
            db.add(t)
            temps_map[d] = t
        db.flush()

        # ── 5. Faits Colis ────────────────────────────────────────────────────
        all_dates = list(temps_map.keys())
        weights = [
            3.0
            if d.month in (11, 12, 7, 8)
            else 1.5
            if d.month in (3, 4, 5, 6)
            else 1.0
            for d in all_dates
        ]
        dest_nationales = [d for d in destinations if d.portee == Portee.NATIONAL]
        dest_intl = [d for d in destinations if d.portee == Portee.INTERNATIONAL]
        dest_weights = [
            0.7 / len(dest_nationales)
            if d.portee == Portee.NATIONAL
            else 0.3 / len(dest_intl)
            for d in destinations
        ]

        for i in range(n_colis):
            chosen_date = random.choices(all_dates, weights=weights, k=1)[0]
            service = random.choices(
                services,
                weights=[0.5, 0.2, 0.2, 0.1],
                k=1,
            )[0]
            destination = random.choices(destinations, weights=dest_weights, k=1)[0]
            poids = round(random.uniform(0.1, 25.0), 2)

            # Heure mock entre 6h00 et 18h00
            heure_int = random.choice(
                [h * 100 + m for h in range(6, 19) for m in [0, 15, 30, 45]]
            )

            colis = FaitColis(
                num_colis=f"TN{str(i + 1).zfill(7)}",
                id_bordereau=random.randint(100000, 999999),
                poids=poids,
                montant=_montant_from_service(service.type_service, poids),
                nature=None,
                ref_paiement=random.choice(["C", "P", None]),
                type_source="normal" if service.code_service == "NOR" else "express",
                heure_formatee=_format_heure(heure_int),  # ← AJOUT
                tranche_horaire=_get_tranche(heure_int),  # ← AJOUT
                est_anomalie=None,
                temps_id=temps_map[chosen_date].id,
                service_id=service.id,
                bureau_id=random.choice(bureaux).id,
                destination_id=destination.id,
            )
            db.add(colis)
        db.flush()

        # ── 6. Utilisateurs ───────────────────────────────────────────────────
        seed_passwords = {
            role: _seed_password(role)
            for role in ["admin", "responsable", "agent_tunis", "agent_sfax"]
        }
        seed_users = [
            User(
                username="admin",
                email="admin@poste.tn",
                hashed_password=get_password_hash(seed_passwords["admin"]),
                role=UserRole.ADMIN,
                region_assignee=None,
            ),
            User(
                username="responsable",
                email="responsable@poste.tn",
                hashed_password=get_password_hash(seed_passwords["responsable"]),
                role=UserRole.RESPONSABLE,
                region_assignee=None,
            ),
            User(
                username="agent_tunis",
                email="agent.tunis@poste.tn",
                hashed_password=get_password_hash(seed_passwords["agent_tunis"]),
                role=UserRole.AGENT_REGIONAL,
                region_assignee="Tunis",
            ),
            User(
                username="agent_sfax",
                email="agent.sfax@poste.tn",
                hashed_password=get_password_hash(seed_passwords["agent_sfax"]),
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
        for username, password in seed_passwords.items():
            print(f"  {username} / {password}")

    except Exception as e:
        db.rollback()
        print(f"❌ Erreur seed : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_mock_data()
