import sys
import os
sys.path.append("/app")

from sqlmodel import Session, select, delete, col
from src.db.session import engine
from src.models.match import Match

def delete_specific_matches():
    # ---------------------------------------------------------
    # ⚠️ ZONA DE EDICIÓN: IDs CONFIRMADOS PARA BORRAR
    # Borramos fantasmas (19, 20) y partidos pasados sin apuesta (1-14)
    # ---------------------------------------------------------
    ids_to_delete = [
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,  # Pasados/Sin interés
        19, 20                                          # Fantasmas Mock Data
    ] 
    # ---------------------------------------------------------

    if not ids_to_delete:
        print("❌ La lista de IDs está vacía.")
        return

    print(f"🔪 Preparando para eliminar {len(ids_to_delete)} partidos irrelevantes...")
    
    with Session(engine) as session:
        # 1. Verificamos qué vamos a borrar (para tu tranquilidad)
        statement = select(Match).where(col(Match.id).in_(ids_to_delete))
        to_delete = session.exec(statement).all()
        
        if not to_delete:
            print("⚠️ No se encontraron partidos con esos IDs (quizás ya se borraron).")
            return

        print("\n📉 Eliminando historial irrelevante:")
        print("-" * 60)
        for m in to_delete:
            print(f" ❌ [ID {m.id}] {m.home_team} vs {m.away_team} ({m.status})")
        print("-" * 60)
        
        # 2. Ejecutar borrado masivo
        statement_del = delete(Match).where(col(Match.id).in_(ids_to_delete))
        result = session.exec(statement_del)
        session.commit()
        
        print(f"\n✅ LIMPIEZA COMPLETA: Se eliminaron {result.rowcount} partidos.")
        print("✨ Tu Dashboard ahora solo muestra tus apuestas activas y oportunidades futuras.")

if __name__ == "__main__":
    delete_specific_matches()