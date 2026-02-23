import sys
import os



from src.database import engine
from src.models import Base

def rebuild_database():
    print("☢️  INICIANDO PROTOCOLO DE RECONSTRUCCIÓN...")
    print(f"   Base de datos objetivo: {engine.url}")
    
    try:
        # 1. Borrar todas las tablas existentes
        print("   🗑️  Eliminando tablas obsoletas...")
        Base.metadata.drop_all(bind=engine)
        
        # 2. Crear las tablas nuevas con la estructura v2.6
        print("   🏗️  Creando nueva estructura (Optimización + Parleys)...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ ¡ÉXITO! La base de datos está limpia y actualizada.")
        print("🚀 Siguiente paso: Reinicia el servidor y dale a 'Sincronizar Mercado'.")
        
    except Exception as e:
        print(f"❌ Error crítico durante la reconstrucción: {e}")

if __name__ == "__main__":
    rebuild_database()