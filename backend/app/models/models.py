"""
Modèles SQLAlchemy du DWH Postalytics.
Mis à jour après réception des vraies données (juillet 2026).
"""

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


# ── Enums ─────────────────────────────────────────────────────────────────────


class NatureColis(str, enum.Enum):
    MARCHANDISE = "Marchandise"
    DOCUMENT = "Document"


class TypeService(str, enum.Enum):
    NORMAL = "Normal"
    EXPRESS_NORMAL = "Express normal"
    EXPRESS_PERSONNALISE = "Express personnalisé"


class Portee(str, enum.Enum):
    NATIONAL = "National"
    INTERNATIONAL = "International"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    RESPONSABLE = "responsable"
    AGENT_REGIONAL = "agent_regional"


# ── Dimension : Temps ─────────────────────────────────────────────────────────


class DimTemps(Base):
    __tablename__ = "dim_temps"

    id = Column(Integer, primary_key=True, index=True)
    date_complete = Column(Date, unique=True, nullable=False, index=True)
    jour = Column(Integer, nullable=False)
    mois = Column(Integer, nullable=False)
    trimestre = Column(Integer, nullable=False)
    annee = Column(Integer, nullable=False, index=True)
    semaine = Column(Integer, nullable=False)
    num_semaine_mois = Column(Integer, nullable=True)  # ← AJOUT
    jour_semaine = Column(String(20), nullable=False)
    saison = Column(String(20), nullable=True)
    est_weekend = Column(Boolean, default=False)
    est_ferie = Column(Boolean, default=False)  # ← AJOUT
    mois_islamique = Column(String(50), nullable=True)  # ← AJOUT
    num_mois_islamique = Column(Integer, nullable=True)  # ← AJOUT
    annee_hijri = Column(Integer, nullable=True)  # ← AJOUT
    evenement_islamique = Column(String(100), nullable=True)  # ← AJOUT
    impact_islamique = Column(String(20), nullable=True)  # ← AJOUT

    colis = relationship("FaitColis", back_populates="dim_temps")


# ── Dimension : Bureau ────────────────────────────────────────────────────────


class DimBureau(Base):
    __tablename__ = "dim_bureau"

    id = Column(Integer, primary_key=True, index=True)
    id_bureau_src = Column(String(50), unique=True, nullable=False, index=True)
    code_postal = Column(String(20), nullable=True)
    cite = Column(String(100), nullable=True)
    ville = Column(String(100), nullable=True)
    gouvernorat = Column(String(100), nullable=True, index=True)
    type_bureau = Column(String(20), nullable=True)  # ← AJOUT "Bureau" | "Agence"

    colis = relationship("FaitColis", back_populates="bureau")


# ── Dimension : Destination ───────────────────────────────────────────────────


class DimDestination(Base):
    __tablename__ = "dim_destination"

    id = Column(Integer, primary_key=True, index=True)
    code_iso_pays = Column(String(10), nullable=True)
    pays_dest = Column(String(255), nullable=False)
    ville_dest = Column(String(255), nullable=True)
    cite_dest = Column(String(255), nullable=True)
    code_postal_dest = Column(String(50), nullable=True)
    portee = Column(Enum(Portee), nullable=False, index=True)

    colis = relationship("FaitColis", back_populates="destination")


# ── Dimension : Service ───────────────────────────────────────────────────────


class DimService(Base):
    __tablename__ = "dim_service"

    id = Column(Integer, primary_key=True, index=True)
    code_service = Column(String(20), unique=True, nullable=False, index=True)
    type_service = Column(Enum(TypeService), nullable=False)
    portee = Column(Enum(Portee), nullable=True)
    label = Column(String(100), nullable=True)
    description = Column(String(200), nullable=True)  # ← AJOUT
    tarif_base = Column(Float, nullable=True)
    delai_standard = Column(Integer, nullable=True)

    colis = relationship("FaitColis", back_populates="service")


# ── Table de faits : Colis ────────────────────────────────────────────────────


class FaitColis(Base):
    __tablename__ = "fait_colis"

    id = Column(Integer, primary_key=True, index=True)
    num_colis = Column(String(50), unique=True, nullable=False, index=True)
    id_bordereau = Column(Integer, nullable=True)
    poids = Column(Float, nullable=False)
    montant = Column(Float, nullable=False)
    nature = Column(Enum(NatureColis), nullable=True)
    ref_paiement = Column(String(20), nullable=True)
    type_source = Column(String(30), nullable=True)
    heure_formatee = Column(String(10), nullable=True)  # ← AJOUT "09:30 AM"
    tranche_horaire = Column(String(30), nullable=True)  # ← AJOUT "Matin (6h-10h)"
    est_anomalie = Column(Boolean, nullable=True, default=None)

    # Clés étrangères
    temps_id = Column(Integer, ForeignKey("dim_temps.id"), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey("dim_service.id"), nullable=False)
    bureau_id = Column(Integer, ForeignKey("dim_bureau.id"), nullable=False, index=True)
    destination_id = Column(
        Integer, ForeignKey("dim_destination.id"), nullable=False, index=True
    )

    # Relations
    dim_temps = relationship("DimTemps", back_populates="colis")
    service = relationship("DimService", back_populates="colis")
    bureau = relationship("DimBureau", back_populates="colis")
    destination = relationship("DimDestination", back_populates="colis")


# ── Utilisateurs applicatifs ──────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    region_assignee = Column(String(100), nullable=True)
    est_actif = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
