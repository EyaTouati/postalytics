"""
Dépendances FastAPI — injection de l'utilisateur courant dans les routes.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Retourne l'utilisateur actif depuis le JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id), User.est_actif == True).first()
    if user is None:
        raise credentials_exception
    return user


def require_role(*roles: UserRole):
    """Factory — génère une dépendance qui exige un rôle parmi la liste."""
    def _check(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès réservé aux rôles : {[r.value for r in roles]}",
            )
        return current_user
    return _check


# Raccourcis courants
require_admin = require_role(UserRole.ADMIN)
require_any_dashboard = require_role(
    UserRole.RESPONSABLE, UserRole.AGENT_REGIONAL, UserRole.ADMIN
)
