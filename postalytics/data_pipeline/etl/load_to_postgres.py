"""
Script ETL — Chargement des données La Poste Tunisienne dans PostgreSQL.

Charge les 5 tables du Data Warehouse dans l'ordre correct :
1. dim_temps
2. dim_bureau
3. dim_service
4. dim_destination
5. fait_colis

Usage :
    cd data_pipeline
    python etl/load_to_postgres.py

Prérequis :
    - Docker doit tourner (docker compose up -d)
    - Les CSV doivent être dans data/processed/
    - La base doit être vide (docker compose down -v puis docker compose up -d)
"""

import sys
import os
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# ── Ajouter le backend au path pour utiliser les modèles ─────────────────────
sys.path.append(os.path.join(os.path.dirname(__file__), "../../backend"))

from app.models.models import (
    Base,
    DimTemps,
    DimBureau,
    DimService,
    DimDestination,
    FaitColis,
    Portee,
    TypeService,
    User,
    UserRole,
)
from app.core.security import get_password_hash

# ── Configuration ─────────────────────────────────────────────────────────────
DATABASE_URL = "postgresql://USER:PASSWORD@HOST:5432/DATABASE"
PATH_CSV = os.path.join(os.path.dirname(__file__), "../data/processed/")

# Taille des lots pour l'insertion (évite les timeouts sur 1.2M lignes)
BATCH_SIZE = 5000

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# ── Helpers ───────────────────────────────────────────────────────────────────


def log(msg: str):
    print(f"  {msg}")


def load_csv(nom: str) -> pd.DataFrame:
    chemin = PATH_CSV + f"{nom}.csv"
    df = pd.read_csv(chemin, encoding="utf-8", low_memory=False)
    log(f"{nom}.csv chargé — {len(df):,} lignes")
    return df


def insert_batch(db: Session, objects: list, nom: str):
    """Insère en lots pour éviter les problèmes mémoire."""
    total = len(objects)
    for i in range(0, total, BATCH_SIZE):
        batch = objects[i : i + BATCH_SIZE]
        db.bulk_save_objects(batch)
        db.flush()
        pct = min(100, round((i + BATCH_SIZE) / total * 100))
        print(f"\r    {nom} : {pct}%", end="", flush=True)
    print()


# ── Étape 0 — Créer le schéma ─────────────────────────────────────────────────


def create_schema():
    print("\n[0/6] Création du schéma PostgreSQL...")
    Base.metadata.drop_all(bind=engine)  # reset complet
    Base.metadata.create_all(bind=engine)
    log(" Schéma créé")


# ── Étape 1 — dim_temps ───────────────────────────────────────────────────────


def load_dim_temps(db: Session):
    print("\n[1/6] Chargement dim_temps...")
    df = load_csv("dim_temps")

    objects = []
    for _, row in df.iterrows():
        objects.append(
            DimTemps(
                id=int(row["id"]),
                date_complete=pd.to_datetime(row["date_complete"]).date(),
                jour=int(row["jour"]),
                mois=int(row["mois"]),
                trimestre=int(row["trimestre"]),
                annee=int(row["annee"]),
                semaine=int(row["semaine"]),
                num_semaine_mois=int(row["num_semaine_mois"])
                if pd.notna(row.get("num_semaine_mois"))
                else None,
                jour_semaine=str(row["jour_semaine"]),
                saison=str(row["saison"]),
                est_weekend=bool(row["est_weekend"]),
                est_ferie=bool(row["est_ferie"])
                if pd.notna(row.get("est_ferie"))
                else False,
                mois_islamique=str(row["mois_islamique"])
                if pd.notna(row.get("mois_islamique"))
                else None,
                num_mois_islamique=int(row["num_mois_islamique"])
                if pd.notna(row.get("num_mois_islamique"))
                else None,
                annee_hijri=int(row["annee_hijri"])
                if pd.notna(row.get("annee_hijri"))
                else None,
                evenement_islamique=str(row["evenement_islamique"])
                if pd.notna(row.get("evenement_islamique"))
                else None,
                impact_islamique=str(row["impact_islamique"])
                if pd.notna(row.get("impact_islamique"))
                else None,
            )
        )

    insert_batch(db, objects, "dim_temps")
    log(f" {len(objects):,} dates chargées")


# ── Étape 2 — dim_bureau ─────────────────────────────────────────────────────


def load_dim_bureau(db: Session):
    print("\n[2/6] Chargement dim_bureau...")
    df = load_csv("dim_bureau")

    objects = []
    for _, row in df.iterrows():
        objects.append(
            DimBureau(
                id=int(row["id"]),
                id_bureau_src=str(row["id_bureau_src"]),
                code_postal=str(row["code_postal"])
                if pd.notna(row.get("code_postal"))
                else None,
                cite=str(row["cite"]) if pd.notna(row.get("cite")) else None,
                ville=str(row["ville"]) if pd.notna(row.get("ville")) else None,
                gouvernorat=str(row["gouvernorat"])
                if pd.notna(row.get("gouvernorat"))
                else None,
                type_bureau=str(row["type_bureau"])
                if pd.notna(row.get("type_bureau"))
                else None,
            )
        )

    insert_batch(db, objects, "dim_bureau")
    log(f" {len(objects):,} bureaux chargés")


# ── Étape 3 — dim_service ────────────────────────────────────────────────────


def load_dim_service(db: Session):
    print("\n[3/6] Chargement dim_service...")
    df = load_csv("dim_service")

    # Mapping code_service → TypeService enum
    mapping_type = {
        "CP": TypeService.NORMAL,
        "UP": TypeService.NORMAL,
        "RR": TypeService.NORMAL,
        "NOR": TypeService.NORMAL,
        "EMS-N": TypeService.EXPRESS_NORMAL,
        "EMS-I": TypeService.EXPRESS_PERSONNALISE,
        "RPP-I": TypeService.EXPRESS_PERSONNALISE,
    }

    mapping_portee = {
        "National": Portee.NATIONAL,
        "International": Portee.INTERNATIONAL,
    }

    objects = []
    for _, row in df.iterrows():
        objects.append(
            DimService(
                id=int(row["id"]),
                code_service=str(row["code_service"]),
                type_service=mapping_type.get(
                    str(row["code_service"]), TypeService.NORMAL
                ),
                portee=mapping_portee.get(str(row["portee"]), Portee.NATIONAL),
                label=str(row["label"]) if pd.notna(row.get("label")) else None,
                description=str(row["description"])
                if pd.notna(row.get("description"))
                else None,
                tarif_base=float(row["tarif_base"])
                if pd.notna(row.get("tarif_base"))
                else None,
                delai_standard=int(row["delai_standard"])
                if pd.notna(row.get("delai_standard"))
                else None,
            )
        )

    insert_batch(db, objects, "dim_service")
    log(f" {len(objects):,} services chargés")


# ── Étape 4 — dim_destination ────────────────────────────────────────────────


def load_dim_destination(db: Session):
    print("\n[4/6] Chargement dim_destination...")
    df = load_csv("dim_destination")

    mapping_portee = {
        "National": Portee.NATIONAL,
        "International": Portee.INTERNATIONAL,
    }

    objects = []
    for _, row in df.iterrows():
        objects.append(
            DimDestination(
                id=int(row["id"]),
                code_iso_pays=str(row["code_iso_pays"])
                if pd.notna(row.get("code_iso_pays"))
                else None,
                pays_dest=str(row["pays_dest"]),
                ville_dest=str(row["ville_dest"])
                if pd.notna(row.get("ville_dest"))
                else None,
                cite_dest=str(row["cite_dest"])
                if pd.notna(row.get("cite_dest"))
                else None,
                code_postal_dest=str(row["code_postal_dest"])
                if pd.notna(row.get("code_postal_dest"))
                else None,
                portee=mapping_portee.get(str(row["portee"]), Portee.NATIONAL),
            )
        )

    insert_batch(db, objects, "dim_destination")
    log(f" {len(objects):,} destinations chargées")


# ── Étape 5 — fait_colis ─────────────────────────────────────────────────────


def load_fait_colis(db: Session):
    print("\n[5/6] Chargement fait_colis...")
    df = load_csv("fait_colis")

    # Supprimer les doublons sur num_colis avant insertion
    avant = len(df)
    df = df.drop_duplicates(subset=["num_colis"], keep="first")
    apres = len(df)
    log(f"Doublons supprimés : {avant - apres:,} | Lignes à insérer : {apres:,}")
    log(f"Début insertion par lots de {BATCH_SIZE:,}...")

    total = len(df)
    nb_erreurs = 0

    for i in range(0, total, BATCH_SIZE):
        batch_df = df.iloc[i : i + BATCH_SIZE]
        objects = []

        for _, row in batch_df.iterrows():
            try:
                objects.append(
                    FaitColis(
                        id=int(row["id"]),
                        num_colis=str(row["num_colis"]),
                        id_bordereau=int(row["id_bordereau"])
                        if pd.notna(row.get("id_bordereau"))
                        else None,
                        poids=float(row["poids"]),
                        montant=float(row["montant"]),
                        nature=None,
                        ref_paiement=str(row["ref_paiement"])
                        if pd.notna(row.get("ref_paiement"))
                        else None,
                        type_source=str(row["type_source"])
                        if pd.notna(row.get("type_source"))
                        else None,
                        heure_formatee=str(row["heure_formatee"])
                        if pd.notna(row.get("heure_formatee"))
                        else None,
                        tranche_horaire=str(row["tranche_horaire"])
                        if pd.notna(row.get("tranche_horaire"))
                        else None,
                        est_anomalie=None,
                        temps_id=int(row["temps_id"]),
                        service_id=int(row["service_id"]),
                        bureau_id=int(row["bureau_id"]),
                        destination_id=int(row["destination_id"]),
                    )
                )
            except Exception as e:
                nb_erreurs += 1

        db.bulk_save_objects(objects)
        db.flush()
        pct = min(100, round((i + BATCH_SIZE) / total * 100))
        print(
            f"\r    fait_colis : {pct}% ({min(i + BATCH_SIZE, total):,}/{total:,})",
            end="",
            flush=True,
        )

    print()
    log(f" {total - nb_erreurs:,} colis chargés | {nb_erreurs} erreurs ignorées")


# ── Étape 6 — Utilisateurs ───────────────────────────────────────────────────


def load_users(db: Session):
    print("\n[6/6] Création des comptes utilisateurs...")

    users = [
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
    for u in users:
        db.add(u)
    db.flush()
    log(f" {len(users)} comptes créés")


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    print("=" * 60)
    print("  PostalBI — ETL La Poste Tunisienne")
    print("=" * 60)

    with Session(engine) as db:
        try:
            create_schema()
            load_dim_temps(db)
            load_dim_bureau(db)
            load_dim_service(db)
            load_dim_destination(db)
            load_fait_colis(db)
            load_users(db)

            db.commit()

            print("\n" + "=" * 60)
            print("   ETL terminé avec succès !")
            print("=" * 60)
            print("\nRésumé :")

            print(f"  dim_temps       : {db.query(DimTemps).count():,} lignes")
            print(f"  dim_bureau      : {db.query(DimBureau).count():,} lignes")
            print(f"  dim_service     : {db.query(DimService).count():,} lignes")
            print(f"  dim_destination : {db.query(DimDestination).count():,} lignes")
            print(f"  fait_colis      : {db.query(FaitColis).count():,} lignes")
            print(f"  users           : {db.query(User).count():,} lignes")

        except Exception as e:
            db.rollback()
            print(f"\n Erreur ETL : {e}")
            raise


if __name__ == "__main__":
    main()
