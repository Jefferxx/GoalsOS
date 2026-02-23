from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    
    # Rol en el sistema (Ej: "Admin", "Partner", "Viewer")
    role: str = "Viewer" 

class User(UserBase, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
    # --- NUEVO CAMPO FINANCIERO ---
    bankroll: float = Field(default=1000.00) # Saldo inicial por defecto
    
    created_at: datetime = Field(default_factory=datetime.utcnow)