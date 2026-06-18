import sys
sys.path.append("/app")

from sqlmodel import Session, select
from src.db.session import engine
from src.models.user import User

def list_all_users():
    print("\n👤 LISTADO DE USUARIOS EN BASE DE DATOS")
    print("="*110)
    print(f"{'ID':<4} | {'EMAIL':<28} | {'ROL':<10} | {'SUPERUSER':<10} | {'ACTIVO':<7} | {'BANKROLL':<10} | CREADO")
    print("="*110)

    with Session(engine) as session:
        users = session.exec(select(User).order_by(User.id)).all()

        for u in users:
            print(f"{u.id:<4} | {u.email:<28} | {u.role:<10} | {str(u.is_superuser):<10} | {str(u.is_active):<7} | {u.bankroll:<10} | {u.created_at}")

    print("="*110)
    print(f"Total de usuarios encontrados: {len(users)}\n")

if __name__ == "__main__":
    list_all_users()
