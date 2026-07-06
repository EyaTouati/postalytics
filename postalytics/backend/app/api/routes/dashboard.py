"""
Routes dashboard — KPIs Phase 2.

Filtre régional automatique : si l'utilisateur est un agent_regional,
ses requêtes sont automatiquement restreintes à son gouvernorat assigné.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import require_any_dashboard
from app.db.session import get_db
from app.models.models import (
    DimBureau, DimDestination, DimService, DimTemps,
    FaitColis, Portee, User, UserRole,
)
from app.schemas.schemas import (
    CAParDestination, EvolutionMensuelle, KPIResume,
    RepartitionNature, RepartitionService, VolumeParRegion,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard KPIs"])

MOIS_FR = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]


def _apply_region_filter(query, current_user: User):
    """
    Filtre conditionnel RBAC :
    - admin / responsable → aucun filtre
    - agent_regional      → filtre sur gouvernorat du bureau d'origine
    """
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        query = query.join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        query = query.filter(DimBureau.gouvernorat == current_user.region_assignee)
    return query


# ── KPIs globaux ──────────────────────────────────────────────────────────────

@router.get("/resume", response_model=KPIResume)
def get_resume(
    annee: Optional[int] = Query(None, description="Filtrer par année"),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = db.query(FaitColis)
    q = _apply_region_filter(q, current_user)

    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id)
        q = q.filter(DimTemps.annee == annee)

    total = q.count()

    ca_q = db.query(func.sum(FaitColis.montant))
    ca_q = _apply_region_filter(ca_q, current_user)
    if annee:
        ca_q = ca_q.join(DimTemps, FaitColis.temps_id == DimTemps.id)
        ca_q = ca_q.filter(DimTemps.annee == annee)
    ca_total = ca_q.scalar() or 0.0

    intl_q = q.join(DimDestination, FaitColis.destination_id == DimDestination.id)
    intl = intl_q.filter(DimDestination.portee == Portee.INTERNATIONAL).count()

    anomalies = q.filter(FaitColis.est_anomalie == True).count()

    return KPIResume(
        total_colis=total,
        total_ca=round(ca_total, 2),
        colis_international=intl,
        taux_international=round(intl / total * 100, 1) if total else 0.0,
        colis_anomalie=anomalies,
    )


# ── Volume par gouvernorat ────────────────────────────────────────────────────

@router.get("/volume-par-region", response_model=List[VolumeParRegion])
def volume_par_region(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            DimBureau.gouvernorat,
            DimDestination.portee,
            func.count(FaitColis.id).label("total_colis"),
            func.sum(FaitColis.montant).label("total_montant"),
        )
        .join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        .join(DimDestination, FaitColis.destination_id == DimDestination.id)
    )

    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)

    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id)
        q = q.filter(DimTemps.annee == annee)

    rows = q.group_by(DimBureau.gouvernorat, DimDestination.portee).all()

    return [
        VolumeParRegion(
            region=r.gouvernorat or "Inconnu",
            portee=r.portee.value,
            total_colis=r.total_colis,
            total_montant=round(r.total_montant or 0, 2),
        )
        for r in rows
    ]


# ── Répartition par nature ────────────────────────────────────────────────────

@router.get("/repartition-nature", response_model=List[RepartitionNature])
def repartition_nature(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = db.query(FaitColis.nature, func.count(FaitColis.id).label("total"))
    q = _apply_region_filter(q, current_user)

    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id)
        q = q.filter(DimTemps.annee == annee)

    rows = q.group_by(FaitColis.nature).all()
    total = sum(r.total for r in rows)

    return [
        RepartitionNature(
            nature=r.nature.value if r.nature else "Inconnu",
            total=r.total,
            pourcentage=round(r.total / total * 100, 1) if total else 0.0,
        )
        for r in rows
    ]


# ── Répartition par service ───────────────────────────────────────────────────

@router.get("/repartition-service", response_model=List[RepartitionService])
def repartition_service(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            DimService.type_service,
            func.count(FaitColis.id).label("total"),
            func.sum(FaitColis.montant).label("ca"),
        )
        .join(DimService, FaitColis.service_id == DimService.id)
    )

    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)

    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id)
        q = q.filter(DimTemps.annee == annee)

    rows = q.group_by(DimService.type_service).all()
    total = sum(r.total for r in rows)

    return [
        RepartitionService(
            type_service=r.type_service.value,
            total=r.total,
            pourcentage=round(r.total / total * 100, 1) if total else 0.0,
            ca_total=round(r.ca or 0, 2),
        )
        for r in rows
    ]


# ── CA par destination ────────────────────────────────────────────────────────

@router.get("/ca-par-destination", response_model=List[CAParDestination])
def ca_par_destination(
    annee: Optional[int] = Query(None),
    top: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            DimDestination.pays_dest,
            DimDestination.portee,
            func.sum(FaitColis.montant).label("ca"),
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimDestination, FaitColis.destination_id == DimDestination.id)
    )

    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)

    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id)
        q = q.filter(DimTemps.annee == annee)

    rows = (
        q.group_by(DimDestination.pays_dest, DimDestination.portee)
        .order_by(func.sum(FaitColis.montant).desc())
        .limit(top)
        .all()
    )

    return [
        CAParDestination(
            pays=r.pays_dest,
            portee=r.portee.value,
            ca_total=round(r.ca or 0, 2),
            volume=r.volume,
        )
        for r in rows
    ]


# ── Évolution mensuelle ───────────────────────────────────────────────────────

@router.get("/evolution-mensuelle", response_model=List[EvolutionMensuelle])
def evolution_mensuelle(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            DimTemps.annee,
            DimTemps.mois,
            func.count(FaitColis.id).label("volume"),
            func.sum(FaitColis.montant).label("ca"),
        )
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
    )

    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)

    if annee:
        q = q.filter(DimTemps.annee == annee)

    rows = (
        q.group_by(DimTemps.annee, DimTemps.mois)
        .order_by(DimTemps.annee, DimTemps.mois)
        .all()
    )

    return [
        EvolutionMensuelle(
            annee=r.annee,
            mois=r.mois,
            label=f"{MOIS_FR[r.mois - 1]} {r.annee}",
            volume=r.volume,
            ca=round(r.ca or 0, 2),
        )
        for r in rows
    ]