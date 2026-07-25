"""
Routes dashboard — KPIs Phase 2.
Analyse complète des flux de colis La Poste Tunisienne.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from app.core.deps import require_any_dashboard
from app.db.session import get_db
from app.models.models import (
    DimBureau,
    DimDestination,
    DimService,
    DimTemps,
    FaitColis,
    Portee,
    User,
    UserRole,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard KPIs"])

MOIS_FR = [
    "Jan",
    "Fév",
    "Mar",
    "Avr",
    "Mai",
    "Jun",
    "Jul",
    "Aoû",
    "Sep",
    "Oct",
    "Nov",
    "Déc",
]


def _region_filter(q, current_user: User):
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)
    return q


# ── Page 1 : Vue Globale ──────────────────────────────────────────────────────


@router.get("/kpis-globaux")
def kpis_globaux(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """6 KPI cards + comparaison année précédente."""

    def base_query(an=None):
        q = db.query(FaitColis)
        q = _region_filter(q, current_user)
        q = q.join(DimTemps, FaitColis.temps_id == DimTemps.id)
        if an:
            q = q.filter(DimTemps.annee == an)
        return q

    q = base_query(annee)
    total = q.count()
    ca = db.query(func.sum(FaitColis.montant))
    ca = _region_filter(ca, current_user)
    ca = ca.join(DimTemps, FaitColis.temps_id == DimTemps.id)
    if annee:
        ca = ca.filter(DimTemps.annee == annee)
    ca_total = ca.scalar() or 0.0

    # International
    intl = (
        q.join(DimDestination, FaitColis.destination_id == DimDestination.id)
        .filter(DimDestination.portee == Portee.INTERNATIONAL)
        .count()
    )

    # Année précédente pour croissance
    an_prec = (annee - 1) if annee else None
    total_prec = base_query(an_prec).count() if an_prec else None
    croissance = (
        round((total - total_prec) / total_prec * 100, 1) if total_prec else None
    )

    # Moyenne par jour
    nb_jours = db.query(func.count(func.distinct(DimTemps.date_complete)))
    nb_jours = nb_jours.join(FaitColis, FaitColis.temps_id == DimTemps.id)
    if annee:
        nb_jours = nb_jours.filter(DimTemps.annee == annee)
    nb_jours = nb_jours.scalar() or 1
    moy_jour = round(total / nb_jours, 1)

    return {
        "total_colis": total,
        "ca_total": round(ca_total, 2),
        "colis_international": intl,
        "taux_international": round(intl / total * 100, 2) if total else 0,
        "croissance_vs_precedent": croissance,
        "moyenne_par_jour": moy_jour,
        "annee_precedente": an_prec,
    }


@router.get("/evolution-annuelle")
def evolution_annuelle(
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Volume et CA par année — toutes les années sur un seul graphique."""
    q = db.query(
        DimTemps.annee,
        func.count(FaitColis.id).label("volume"),
        func.sum(FaitColis.montant).label("ca"),
    ).join(DimTemps, FaitColis.temps_id == DimTemps.id)
    q = _region_filter(q, current_user)
    rows = q.group_by(DimTemps.annee).order_by(DimTemps.annee).all()
    return [
        {
            "annee": r.annee,
            "volume": r.volume,
            "ca": round(r.ca or 0, 2),
        }
        for r in rows
    ]


@router.get("/repartition-services")
def repartition_services(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Répartition par service avec label, volume, CA, %."""
    q = (
        db.query(
            DimService.code_service,
            DimService.label,
            DimService.portee,
            func.count(FaitColis.id).label("volume"),
            func.sum(FaitColis.montant).label("ca"),
        )
        .join(DimService, FaitColis.service_id == DimService.id)
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
    )
    q = _region_filter(q, current_user)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = (
        q.group_by(DimService.code_service, DimService.label, DimService.portee)
        .order_by(func.count(FaitColis.id).desc())
        .all()
    )

    total = sum(r.volume for r in rows)
    return [
        {
            "code": r.code_service,
            "label": r.label,
            "portee": r.portee.value if r.portee else None,
            "volume": r.volume,
            "ca": round(r.ca or 0, 2),
            "pourcentage": round(r.volume / total * 100, 1) if total else 0,
        }
        for r in rows
    ]


@router.get("/top-gouvernorats")
def top_gouvernorats(
    annee: Optional[int] = Query(None),
    top: int = Query(10),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Top gouvernorats expéditeurs."""
    q = (
        db.query(
            DimBureau.gouvernorat,
            func.count(FaitColis.id).label("volume"),
            func.sum(FaitColis.montant).label("ca"),
        )
        .join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimBureau.gouvernorat != None)
        .filter(DimBureau.gouvernorat != "Inconnu")
    )
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = (
        q.group_by(DimBureau.gouvernorat)
        .order_by(func.count(FaitColis.id).desc())
        .limit(top)
        .all()
    )
    total = sum(r.volume for r in rows)
    return [
        {
            "gouvernorat": r.gouvernorat,
            "volume": r.volume,
            "ca": round(r.ca or 0, 2),
            "pourcentage": round(r.volume / total * 100, 1) if total else 0,
        }
        for r in rows
    ]


# ── Page 2 : Analyse Temporelle ──────────────────────────────────────────────


@router.get("/evolution-mensuelle")
def evolution_mensuelle(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Volume mensuel — toutes années ou année filtrée."""
    q = db.query(
        DimTemps.annee,
        DimTemps.mois,
        func.count(FaitColis.id).label("volume"),
        func.sum(FaitColis.montant).label("ca"),
    ).join(DimTemps, FaitColis.temps_id == DimTemps.id)
    q = _region_filter(q, current_user)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = (
        q.group_by(DimTemps.annee, DimTemps.mois)
        .order_by(DimTemps.annee, DimTemps.mois)
        .all()
    )
    return [
        {
            "annee": r.annee,
            "mois": r.mois,
            "label": f"{MOIS_FR[r.mois - 1]} {r.annee}",
            "label_court": MOIS_FR[r.mois - 1],
            "volume": r.volume,
            "ca": round(r.ca or 0, 2),
        }
        for r in rows
    ]


@router.get("/heatmap-mois-annee")
def heatmap_mois_annee(
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Heatmap mois × année pour visualiser la saisonnalité."""
    q = db.query(
        DimTemps.annee,
        DimTemps.mois,
        func.count(FaitColis.id).label("volume"),
    ).join(DimTemps, FaitColis.temps_id == DimTemps.id)
    q = _region_filter(q, current_user)
    rows = (
        q.group_by(DimTemps.annee, DimTemps.mois)
        .order_by(DimTemps.annee, DimTemps.mois)
        .all()
    )

    # Structurer pour heatmap : {annee: {mois: volume}}
    data = {}
    for r in rows:
        if r.annee not in data:
            data[r.annee] = {}
        data[r.annee][r.mois] = r.volume

    return {
        "annees": sorted(data.keys()),
        "mois": MOIS_FR,
        "data": [
            {"annee": annee, "valeurs": [data[annee].get(m + 1, 0) for m in range(12)]}
            for annee in sorted(data.keys())
        ],
    }


@router.get("/volume-par-jour-semaine")
def volume_jour_semaine(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Volume par jour de la semaine."""
    ORDRE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    q = db.query(
        DimTemps.jour_semaine,
        func.count(FaitColis.id).label("volume"),
    ).join(DimTemps, FaitColis.temps_id == DimTemps.id)
    q = _region_filter(q, current_user)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = q.group_by(DimTemps.jour_semaine).all()
    result = {r.jour_semaine: r.volume for r in rows}
    total = sum(result.values()) or 1
    return [
        {
            "jour": j,
            "volume": result.get(j, 0),
            "pourcentage": round(result.get(j, 0) / total * 100, 1),
        }
        for j in ORDRE
    ]


@router.get("/volume-par-tranche-horaire")
def volume_tranche_horaire(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Volume par tranche horaire — colis normaux uniquement."""
    ORDRE = [
        "Matin (6h-10h)",
        "Milieu matin (10h-13h)",
        "Après-midi (13h-15h)",
        "Fin après-midi (15h-18h)",
        "Soir (18h-21h)",
        "Hors horaires",
    ]
    q = (
        db.query(
            FaitColis.tranche_horaire,
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(FaitColis.type_source == "normal")
        .filter(FaitColis.tranche_horaire != None)
    )
    q = _region_filter(q, current_user)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = q.group_by(FaitColis.tranche_horaire).all()
    result = {r.tranche_horaire: r.volume for r in rows}
    total = sum(result.values()) or 1
    return [
        {
            "tranche": t,
            "volume": result.get(t, 0),
            "pourcentage": round(result.get(t, 0) / total * 100, 1),
            "dans_horaires": t not in ["Hors horaires"],
        }
        for t in ORDRE
        if result.get(t, 0) > 0
    ]


@router.get("/volume-islamique")
def volume_islamique(
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Volume par événement islamique et par mois islamique."""
    # Par événement
    q_event = (
        db.query(
            DimTemps.evenement_islamique,
            DimTemps.annee,
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimTemps.evenement_islamique != None)
    )
    q_event = _region_filter(q_event, current_user)
    rows_event = (
        q_event.group_by(DimTemps.evenement_islamique, DimTemps.annee)
        .order_by(DimTemps.annee)
        .all()
    )

    # Par mois islamique
    q_mois = (
        db.query(
            DimTemps.mois_islamique,
            DimTemps.num_mois_islamique,
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimTemps.mois_islamique != None)
    )
    q_mois = _region_filter(q_mois, current_user)
    rows_mois = (
        q_mois.group_by(DimTemps.mois_islamique, DimTemps.num_mois_islamique)
        .order_by(DimTemps.num_mois_islamique)
        .all()
    )

    return {
        "par_evenement": [
            {
                "evenement": r.evenement_islamique,
                "annee": r.annee,
                "volume": r.volume,
            }
            for r in rows_event
        ],
        "par_mois": [
            {
                "mois": r.mois_islamique,
                "num": r.num_mois_islamique,
                "volume": r.volume,
            }
            for r in rows_mois
        ],
    }


# ── Page 3 : Analyse Géographique ────────────────────────────────────────────


@router.get("/volume-par-gouvernorat")
def volume_gouvernorat(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Volume complet par gouvernorat avec portée."""
    q = (
        db.query(
            DimBureau.gouvernorat,
            DimDestination.portee,
            func.count(FaitColis.id).label("volume"),
            func.sum(FaitColis.montant).label("ca"),
        )
        .join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        .join(DimDestination, FaitColis.destination_id == DimDestination.id)
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimBureau.gouvernorat != None)
        .filter(DimBureau.gouvernorat != "Inconnu")
    )
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = (
        q.group_by(DimBureau.gouvernorat, DimDestination.portee)
        .order_by(func.count(FaitColis.id).desc())
        .all()
    )
    return [
        {
            "gouvernorat": r.gouvernorat,
            "portee": r.portee.value,
            "volume": r.volume,
            "ca": round(r.ca or 0, 2),
        }
        for r in rows
    ]


@router.get("/pression-bureaux")
def pression_bureaux(
    annee: Optional[int] = Query(None),
    top: int = Query(20),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Pression des bureaux = volume / nombre de jours actifs."""
    q = (
        db.query(
            DimBureau.id_bureau_src,
            DimBureau.ville,
            DimBureau.gouvernorat,
            DimBureau.type_bureau,
            func.count(FaitColis.id).label("volume_total"),
            func.count(func.distinct(DimTemps.date_complete)).label("jours_actifs"),
            func.sum(FaitColis.montant).label("ca"),
        )
        .join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimBureau.gouvernorat != None)
    )
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = (
        q.group_by(
            DimBureau.id_bureau_src,
            DimBureau.ville,
            DimBureau.gouvernorat,
            DimBureau.type_bureau,
        )
        .order_by(func.count(FaitColis.id).desc())
        .limit(top)
        .all()
    )

    # Calcul pression moyenne pour badge
    pressions = [r.volume_total / max(r.jours_actifs, 1) for r in rows]
    moy_pression = sum(pressions) / len(pressions) if pressions else 1

    return [
        {
            "bureau": r.id_bureau_src,
            "ville": r.ville,
            "gouvernorat": r.gouvernorat,
            "type": r.type_bureau,
            "volume_total": r.volume_total,
            "jours_actifs": r.jours_actifs,
            "colis_par_jour": round(r.volume_total / max(r.jours_actifs, 1), 1),
            "ca": round(r.ca or 0, 2),
            "surcharge": r.volume_total / max(r.jours_actifs, 1) > moy_pression * 1.5,
        }
        for r in rows
    ]


@router.get("/heatmap-region-mois")
def heatmap_region_mois(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Heatmap croisée Gouvernorat × Mois."""
    q = (
        db.query(
            DimBureau.gouvernorat,
            DimTemps.mois,
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimBureau.gouvernorat != None)
        .filter(DimBureau.gouvernorat != "Inconnu")
    )
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = q.group_by(DimBureau.gouvernorat, DimTemps.mois).all()

    # Structurer : {gouvernorat: {mois: volume}}
    data = {}
    for r in rows:
        if r.gouvernorat not in data:
            data[r.gouvernorat] = {}
        data[r.gouvernorat][r.mois] = r.volume

    # Trier par volume total décroissant
    gouvernorats = sorted(
        data.keys(), key=lambda g: sum(data[g].values()), reverse=True
    )

    return {
        "gouvernorats": gouvernorats,
        "mois": MOIS_FR,
        "data": [
            {
                "gouvernorat": g,
                "valeurs": [data[g].get(m + 1, 0) for m in range(12)],
                "total": sum(data[g].values()),
            }
            for g in gouvernorats
        ],
    }


# ── Page 4 : Analyses Croisées ────────────────────────────────────────────────


@router.get("/service-par-gouvernorat")
def service_gouvernorat(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Quel service est utilisé dans chaque gouvernorat."""
    q = (
        db.query(
            DimBureau.gouvernorat,
            DimService.code_service,
            DimService.label,
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        .join(DimService, FaitColis.service_id == DimService.id)
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimBureau.gouvernorat != None)
        .filter(DimBureau.gouvernorat != "Inconnu")
    )
    if current_user.role == UserRole.AGENT_REGIONAL and current_user.region_assignee:
        q = q.filter(DimBureau.gouvernorat == current_user.region_assignee)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = q.group_by(
        DimBureau.gouvernorat, DimService.code_service, DimService.label
    ).all()
    return [
        {
            "gouvernorat": r.gouvernorat,
            "code_service": r.code_service,
            "label": r.label,
            "volume": r.volume,
        }
        for r in rows
    ]


@router.get("/analyse-diaspora")
def analyse_diaspora(
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Effet diaspora : flux international juillet-août vs reste de l'année."""
    q = (
        db.query(
            DimTemps.annee,
            DimTemps.mois,
            DimDestination.pays_dest,
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .join(DimDestination, FaitColis.destination_id == DimDestination.id)
        .filter(DimDestination.portee == Portee.INTERNATIONAL)
        .filter(DimTemps.mois.in_([6, 7, 8]))
    )
    q = _region_filter(q, current_user)
    rows = (
        q.group_by(DimTemps.annee, DimTemps.mois, DimDestination.pays_dest)
        .order_by(func.count(FaitColis.id).desc())
        .all()
    )

    return [
        {
            "annee": r.annee,
            "mois": r.mois,
            "label_mois": MOIS_FR[r.mois - 1],
            "pays": r.pays_dest,
            "volume": r.volume,
        }
        for r in rows
    ]


@router.get("/analyse-dattes")
def analyse_dattes(
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Effet dattes : flux du Sud en octobre-novembre."""
    GOUVERNORATS_SUD = ["Tozeur", "Kébili", "Gafsa", "Médenine", "Tataouine", "Gabès"]
    q = (
        db.query(
            DimTemps.annee,
            DimTemps.mois,
            DimBureau.gouvernorat,
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .join(DimBureau, FaitColis.bureau_id == DimBureau.id)
        .filter(DimBureau.gouvernorat.in_(GOUVERNORATS_SUD))
    )
    rows = (
        q.group_by(DimTemps.annee, DimTemps.mois, DimBureau.gouvernorat)
        .order_by(DimTemps.annee, DimTemps.mois)
        .all()
    )

    return [
        {
            "annee": r.annee,
            "mois": r.mois,
            "label_mois": MOIS_FR[r.mois - 1],
            "gouvernorat": r.gouvernorat,
            "volume": r.volume,
            "periode_dattes": r.mois in [10, 11],
        }
        for r in rows
    ]


# ── Page 5 : Destinations ────────────────────────────────────────────────────


@router.get("/top-destinations-international")
def top_destinations_intl(
    annee: Optional[int] = Query(None),
    top: int = Query(20),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Top pays de destination internationale."""
    q = (
        db.query(
            DimDestination.pays_dest,
            DimDestination.code_iso_pays,
            func.count(FaitColis.id).label("volume"),
            func.sum(FaitColis.montant).label("ca"),
        )
        .join(DimDestination, FaitColis.destination_id == DimDestination.id)
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimDestination.portee == Portee.INTERNATIONAL)
    )
    q = _region_filter(q, current_user)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = (
        q.group_by(DimDestination.pays_dest, DimDestination.code_iso_pays)
        .order_by(func.count(FaitColis.id).desc())
        .limit(top)
        .all()
    )
    total = sum(r.volume for r in rows)
    return [
        {
            "pays": r.pays_dest,
            "code_iso": r.code_iso_pays,
            "volume": r.volume,
            "ca": round(r.ca or 0, 2),
            "pourcentage": round(r.volume / total * 100, 1) if total else 0,
        }
        for r in rows
    ]


@router.get("/flux-national-gouvernorat")
def flux_national_gouvernorat(
    annee: Optional[int] = Query(None),
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Flux national : top gouvernorats de destination."""
    q = (
        db.query(
            DimDestination.ville_dest,
            func.count(FaitColis.id).label("volume"),
        )
        .join(DimDestination, FaitColis.destination_id == DimDestination.id)
        .join(DimTemps, FaitColis.temps_id == DimTemps.id)
        .filter(DimDestination.portee == Portee.NATIONAL)
        .filter(DimDestination.ville_dest != "INCONNU")
        .filter(DimDestination.ville_dest != None)
    )
    q = _region_filter(q, current_user)
    if annee:
        q = q.filter(DimTemps.annee == annee)
    rows = (
        q.group_by(DimDestination.ville_dest)
        .order_by(func.count(FaitColis.id).desc())
        .limit(15)
        .all()
    )
    return [{"ville": r.ville_dest, "volume": r.volume} for r in rows]


# ── Prévisions Prophet ────────────────────────────────────────────────────────


@router.get("/previsions")
def get_previsions(
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Retourne l'historique mensuel + prévisions Prophet depuis PostgreSQL."""
    from sqlalchemy import text

    rows = db.execute(
        text("""
        SELECT label, annee, mois, volume_reel, volume_prevu,
               borne_inf, borne_sup, est_prevision
        FROM previsions_mensuelles
        ORDER BY annee, mois
    """)
    ).fetchall()

    return [
        {
            "label": r[0],
            "annee": r[1],
            "mois": r[2],
            "volume_reel": int(r[3]) if r[3] is not None else None,
            "volume_prevu": int(r[4]) if r[4] is not None else None,
            "borne_inf": int(r[5]) if r[5] is not None else None,
            "borne_sup": int(r[6]) if r[6] is not None else None,
            "est_prevision": bool(r[7]),
        }
        for r in rows
    ]


@router.get("/segmentation-bureaux")
def segmentation_bureaux(
    current_user: User = Depends(require_any_dashboard),
    db: Session = Depends(get_db),
):
    """Résultats de la segmentation K-Means des bureaux."""
    import os
    import pandas as pd

    chemin = "/app/../data_pipeline/data/processed/bureaux_segmentes.csv"

    if not os.path.exists(chemin):
        return {
            "error": "Segmentation non disponible — lancer 04_ml_segmentation.ipynb"
        }

    df = pd.read_csv(chemin)

    # Profil par cluster
    profil = (
        df.groupby("segment")
        .agg(
            nb_bureaux=("bureau_id", "count"),
            nb_colis_moy=("nb_colis", "mean"),
            ca_par_colis=("ca_par_colis", "mean"),
            taux_intl=("taux_intl", "mean"),
            taux_ems_n=("taux_ems_n", "mean"),
            taux_rpp_i=("taux_rpp_i", "mean"),
            taux_normal=("taux_normal", "mean"),
        )
        .round(3)
        .reset_index()
    )

    # Top bureaux par segment
    top_bureaux = (
        df.sort_values("nb_colis", ascending=False)
        .groupby("segment")
        .head(3)[["segment", "bureau_id", "gouvernorat", "nb_colis", "ca_total"]]
        .to_dict(orient="records")
    )

    return {
        "profil": profil.to_dict(orient="records"),
        "top_bureaux": top_bureaux,
        "total_bureaux": int(len(df)),
    }
