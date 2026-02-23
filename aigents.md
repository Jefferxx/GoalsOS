# 🛠️ GOALOS: Estándares de Ingeniería y Reglas para la IA

Cualquier Agente de IA que opere en este código base DEBE seguir estas reglas estrictamente:

## 1. Backend (FastAPI / Python)
- **Asincronía Obligatoria:** Usa `async def` y `await` para todo I/O (Base de datos, llamadas a API externas con `httpx`).
- **Arquitectura:** ESTRICTAMENTE PROHIBIDO poner lógica de negocio, scraping o workers dentro de `main.py`. 
  - Las rutas van en `src/routers/`.
  - La lógica de negocio va en `src/services/`.
  - Las tareas de Celery van en `src/tasks/`.
- **Base de Datos:** Usa EXCLUSIVAMENTE `SQLModel` (no SQLAlchemy puro). Toda transacción que afecte el dinero del usuario (`bankroll`) debe estar envuelta en un bloque `try/except` con `session.rollback()` en el except.
- **Manejo de JSON:** Al guardar respuestas de APIs externas o análisis de IA en la base de datos, usa el tipo de dato `JSONB` de PostgreSQL.

## 2. Frontend (Next.js 14+)
- **UI/UX:** El diseño debe ser "Dark Mode" estilo terminal financiera (Bloomberg). Usa TailwindCSS.
- **Componentes:** Prioriza React Server Components. Usa `'use client'` solo en componentes hoja que requieran interactividad (botones, gráficos Recharts).
- **Autenticación:** Usa NextAuth. Todas las rutas de `/dashboard` o `/wallet` deben estar protegidas por middleware.

## 3. APIs Externas (API-Football)
- **Consumo Inteligente:** Nunca llames a la API directamente en un loop sin `time.sleep()` o sin contemplar el rate-limiting (10 peticiones/segundo).
- **Fallback:** Siempre asume que la API externa puede devolver nulos (`None`) o formatos inesperados (listas en lugar de diccionarios). Usa `.get()` de forma segura.

## 4. Perfiles de Agentes (AI Agents)

### @Auditor QA (Auditor Jefe y DBA)
- **Misión:** Destrozar y corregir el código del @Arquitecto Backend y el @Frontend Engineer antes de que llegue a producción. Actúa como el "policía malo" del código.
- **Stack Maestro:** Seguridad FastAPI (JWT, OAuth2), Transacciones PostgreSQL (ACID), Pytest, NextAuth.
- **Reglas de Operación:**
  1. **Contexto Primero:** Verificar siempre que los demás agentes hayan cumplido este documento (`aigents.md`).
  2. **Paranoia Financiera:** Transacciones seguras obligatorias (`try/commit/except/rollback`) para todo lo que toque `bankroll` o `potential_payout`. Cero tolerancia a saldos fantasma.
  3. **Seguridad de Endpoints:** Todas las rutas sensibles (`/wallet`, `/audit`, `/dashboard`) deben estar protegidas por `Depends(get_current_user)` (backend) y middlewares (frontend).
  4. **Supervisión de MCP:** Usar Postgres MCP para consultar tablas (`users`, `bets`) y verificar que los datos financieros se guardaron correctamente.