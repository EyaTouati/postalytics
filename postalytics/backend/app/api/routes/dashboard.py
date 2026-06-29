"""
Routes dashboard — KPIs Phase 2.

Filtre régional automatique : si l'utilisateur est un agent_regional,
ses requêtes sont automatiquement restreintes à sa région assignée.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_any_dashboard
from app.db.session import get_db
from app.models.models import (
    DimClient, DimDestination, DimOrigine, DimService, DimTemps,
    FaitColis, NatureColis, Portee, User, UserRole,
)
from app.schemas.schemas import (
    CAParDestination, EvolutionMensuelle, KPIResume,
    RepartitionNature, RepartitionService, VolumeParRegion,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard KPIs"])

MOIS_FR = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]


def _apply_region_filter(query, current_user: User, db: Session):
    """
    Filtre conditionnel RBAC :
    - admin / responsable → aucun filtre géographique
    - agent_regional → jointure sur dim_origine et filtre sur region_assignee
    """
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        query = query.join(DimOrigine, FaitColis.origine_id == DimOrigine.id)
        query = query.filter(DimOrigine.region == current_user.region_assignee)
    return query


@router.get("/resume", response_model=KPIResume)
def get_resume(
    annee: Optional[int] = Query(None, description="Filtrer par année"),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Carte de résumé globale — haut du dashboard."""
    q = db.query(FaitColis)
    q = _apply_region_filter(q, current_user, db)

    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id)
        q = q.filter(DimTemps.annee == annee)

    total = q.count()
    ca = db.query(func.sum(FaitColis.montant))
    ca = _apply_region_filter(ca, current_user, db)
    if annee:
        ca = ca.join(DimTemps, FaitColis.temps_id == DimTemps.id).filter(DimTemps.annee == annee)
    ca_total = ca.scalar() or 0.0

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


@router.get("/volume-par-region", response_model=List[VolumeParRegion])
def volume_par_region(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            DimOrigine.region,
            DimDestination.portee,
            func.count(FaitColis.id).label("total_colis"),
            func.sum(FaitColis.montant).label("total_montant"),
        )
        .join(DimOrigine, FaitColis.origine_id == DimOrigine.id)
        .join(DimDestination, FaitColis.destination_id == DimDestination.id)
    )
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.filter(DimOrigine.region == current_user.region_assignee)
    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id).filter(DimTemps.annee == annee)

    rows = q.group_by(DimOrigine.region, DimDestination.portee).all()
    return [
        VolumeParRegion(
            region=r.region,
            portee=r.portee.value,
            total_colis=r.total_colis,
            total_montant=round(r.total_montant or 0, 2),
        )
        for r in rows
    ]


@router.get("/repartition-nature", response_model=List[RepartitionNature])
def repartition_nature(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = db.query(FaitColis.nature, func.count(FaitColis.id).label("total"))
    q = _apply_region_filter(q, current_user, db)
    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id).filter(DimTemps.annee == annee)
    rows = q.group_by(FaitColis.nature).all()
    total = sum(r.total for r in rows)
    return [
        RepartitionNature(
            nature=r.nature.value,
            total=r.total,
            pourcentage=round(r.total / total * 100, 1) if total else 0.0,
        )
        for r in rows
    ]


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
        q = q.join(DimOrigine, FaitColis.origine_id == DimOrigine.id)
        q = q.filter(DimOrigine.region == current_user.region_assignee)
    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id).filter(DimTemps.annee == annee)
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


@router.get("/ca-par-destination", response_model=List[CAParDestination])
def ca_par_destination(
    annee: Optional[int] = Query(None),
    top: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    q = (
        db.query(
            DimDestination.pays,
            DimDestination.portee,
            func.sum(FaitColis.montant).label("ca"),
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimDestination, FaitColis.destination_id == DimDestination.id)
    )
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.join(DimOrigine, FaitColis.origine_id == DimOrigine.id)
        q = q.filter(DimOrigine.region == current_user.region_assignee)
    if annee:
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id).filter(DimTemps.annee == annee)
    rows = (
        q.group_by(DimDestination.pays, DimDestination.portee)
        .order_by(func.sum(FaitColis.montant).desc())
        .limit(top)
        .all()
    )
    return [
        CAParDestination(
            pays=r.pays,
            portee=r.portee.value,
            ca_total=round(r.ca or 0, 2),
            volume=r.volume,
        )
        for r in rows
    ]


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
        q = q.join(DimOrigine, FaitColis.origine_id == DimOrigine.id)
        q = q.filter(DimOrigine.region == current_user.region_assignee)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = q.group_by(DimTemps.annee, DimTemps.mois).order_by(DimTemps.annee, DimTemps.mois).all()
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
