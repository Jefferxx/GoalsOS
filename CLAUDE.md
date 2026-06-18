# CLAUDE.md — GoalOS

## Qué es este proyecto

GoalOS es una terminal personal de inversión cuantitativa para apuestas de fútbol: ingiere partidos/cuotas/lesiones de API-Football, calcula xG vía scraping de Understat, corre un motor de Poisson propio (`apps/api/src/services/math/poisson.py`) para detectar value bets, y complementa con un análisis de IA generativa (Gemini + fallback Groq) no integrado con el motor estadístico. Incluye gestión de bankroll, apuestas, historial con auditoría y generador de parleys.

- **Backend:** `apps/api` — FastAPI + SQLModel + PostgreSQL + Celery/Redis.
- **Frontend:** `apps/web` — Next.js (App Router) + TypeScript + NextAuth + Tailwind.
- **Legacy:** `legacy_v3/` — versión anterior en Streamlit, conservada solo como referencia.
- Reglas de ingeniería obligatorias del backend/frontend: ver [`aigents.md`](./aigents.md).
- Resumen técnico corto: ver [`llms.txt`](./llms.txt).

Estado al retomar el proyecto (junio 2026): un solo commit en git (`154d6af`), sin CI/CD, sin tests reales, ingesta diaria todavía en modo Mock. El detalle completo de hallazgos de la primera revisión está en la nota de Obsidian de la sesión inicial (ver más abajo).

## Flujo de trabajo obligatorio para toda sesión de desarrollo

Para **cualquier cambio de código/feature**, sin excepción:

1. **Planear.** Antes de tocar código, definir el alcance del cambio.
2. **Documentar en Obsidian.** Escribir o actualizar la nota de la sesión en `C:\Users\jeffe\Documents\Obsidian_Notas\10_Proyectos\GoalOS`, nombrada con fecha y hora (`YYYY-MM-DD_HHMM - <título>.md`), enlazada desde `GoalOS - Índice.md`.
3. **Esperar aprobación** del usuario sobre el plan antes de ejecutar.
4. **Ejecutar con mínimo 5 commits atómicos** subidos a `https://github.com/Jefferxx/GoalsOS.git`. Cada commit debe representar un cambio coherente y autocontenido (no un volcado de todo el trabajo en un solo commit).
5. **Verificar** lo construido (correr la app, tests, o inspección manual según aplique) antes de declarar el trabajo terminado.
6. **Actualizar la nota de Obsidian** de la sesión con el resultado final y cualquier decisión tomada durante la ejecución.

**Excepción:** trabajo de documentación pura (editar este `CLAUDE.md`, notas de Obsidian, README) no requiere el mínimo de 5 commits — puede ir en 1-2 commits descriptivos. El resto del flujo (plan → Obsidian → aprobación → ejecución → verificación → actualizar nota) sigue aplicando igual.

## Política de skills y plugins

Activar skills/plugins (code-review, etc.) **solo cuando la tarea puntual lo requiera**, y desactivarlos inmediatamente después de usarlos. No dejarlos activos de forma permanente — consumen tokens en cada mensaje aunque no se usen.

## Documentación

Todo cambio relevante debe quedar documentado en dos lugares:
- **Obsidian:** `C:\Users\jeffe\Documents\Obsidian_Notas\10_Proyectos\GoalOS` (notas por sesión + índice maestro).
- **GitHub:** historial de commits atómicos en `https://github.com/Jefferxx/GoalsOS.git`.
