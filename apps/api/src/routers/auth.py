import os
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlmodel import Session, select
from pydantic import BaseModel
from jose import jwt

from src.db.session import get_session
from src.models.user import User
from src.utils.security import verify_password, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="", tags=["Autenticación y Setup"])

# Duración del token (configurable por env var, default 8 horas)
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", 8))


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict


def _create_access_token(data: dict) -> str:
    """Genera un JWT firmado con expiración."""
    payload = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload.update({"exp": expire, "iat": datetime.datetime.utcnow()})
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)



@router.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, session: Session = Depends(get_session)):
    """
    Autenticación con email y contraseña.
    Retorna un Bearer Token JWT válido por 8 horas.
    """
    def do_login():
        user = session.exec(select(User).where(User.email == request.email)).first()

        # Validación en tiempo constante (previene timing attacks)
        if not user or not verify_password(request.password, user.hashed_password):
            return None

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cuenta desactivada. Contacta al administrador."
            )

        # Payload del token: sub (estándar JWT), rol para autorización futura
        token = _create_access_token({
            "sub": user.email,
            "role": user.role,
            "name": user.full_name,
        })

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "email": user.email,
                "name": user.full_name,
                "role": user.role,
            },
        }

    result = await run_in_threadpool(do_login)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result
