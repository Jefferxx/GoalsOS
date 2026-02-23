import os
import re

def verify_git_safety():
    print("🛡️ Verificando seguridad para GitHub...")
    
    # 1. Verificar .gitignore
    if not os.path.exists(".gitignore"):
        print("❌ ERROR: No existe .gitignore")
        return
    
    # Añadimos encoding="utf-8" para evitar el error de charmap
    with open(".gitignore", "r", encoding="utf-8") as f:
        content = f.read()
        if ".env" not in content:
            print("❌ ERROR: .env NO está en .gitignore. ¡Peligro de baneo!")
            return
        else:
            print("✅ .env está protegido en .gitignore")

    # 2. Escanear archivos en busca de llaves "hardcoded"
    # Buscamos patrones de API Keys (letras y números largos entre comillas)
    key_pattern = re.compile(r'["\'][a-zA-Z0-9]{30,60}["\']')
    
    bad_files = []
    for root, dirs, files in os.walk("."):
        # Ignorar carpetas pesadas o de sistema
        if any(x in root for x in ["venv", ".git", "node_modules", ".next", "__pycache__"]):
            continue
            
        for file in files:
            if file.endswith((".py", ".ts", ".tsx", ".env")):
                if file == ".env": continue # .env puede tener llaves
                
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        if key_pattern.search(f.read()):
                            bad_files.append(path)
                except Exception as e:
                    print(f"⚠️ No se pudo leer {path}: {e}")

    if bad_files:
        print(f"❌ PELIGRO: Se encontraron posibles llaves expuestas en:")
        for bf in bad_files:
            print(f"   -> {bf}")
    else:
        print("✅ No se detectaron llaves expuestas en el código fuente.")

if __name__ == "__main__":
    verify_git_safety()