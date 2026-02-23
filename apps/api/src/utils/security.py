import os
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

# Configuramos Bcrypt (El estándar de oro en seguridad)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de seguridad Bearer Token
bearer_scheme = HTTPBearer()

# ─── CONSTANTES JWT ────────────────────────────────────────────────────────────
# SECRET_KEY: en producción, setear como variable de entorno segura
# Ejemplo .env: SECRET_KEY=una-clave-larga-y-aleatoria-de-256-bits
SECRET_KEY = os.getenv("SECRET_KEY", "goalos-secret-dev-key-change-in-production")
ALGORITHM = "HS256"
# ──────────────────────────────────────────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña escrita coincide con el hash guardado."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Transforma '123456' en una cadena encriptada imposible de revertir."""
    return pwd_context.hash(password)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Dependencia de FastAPI. Valida el Bearer Token JWT en cada request protegido.
    Lanza HTTP 401 si el token es inválido, expirado o malformado.

    Uso en cualquier endpoint:
        current_user: dict = Depends(get_current_user)

    El payload retornado incluye: sub (email), role, name, exp, iat.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado. Acceso denegado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception