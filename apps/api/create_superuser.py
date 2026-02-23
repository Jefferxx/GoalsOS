from sqlmodel import Session, select
from src.db.session import engine
from src.models.user import User
from src.utils.security import get_password_hash

def create_admin():
    print("🛡️ Creando Usuario Administrador (CEO)...")
    
    # 1. Datos del Admin (TÚ)
    admin_email = "jefferson@goalos.com"  # Puedes cambiarlo
    plain_password = "admin_secure_pass"  # CAMBIA ESTO POR TU CONTRASEÑA REAL
    
    with Session(engine) as session:
        # 2. Verificar si ya existe
        statement = select(User).where(User.email == admin_email)
        existing_user = session.exec(statement).first()
        
        if existing_user:
            print(f"⚠️ El usuario {admin_email} ya existe.")
            return

        # 3. Crear nuevo Admin con contraseña ENCRIPTADA
        new_admin = User(
            email=admin_email,
            full_name="Jefferson Jordan",
            hashed_password=get_password_hash(plain_password),
            role="Admin",
            is_superuser=True
        )
        
        session.add(new_admin)
        session.commit()
        print(f"✅ ¡Usuario {admin_email} creado exitosamente!")

if __name__ == "__main__":
    create_admin()