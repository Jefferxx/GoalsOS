import os
from celery import Celery
from celery.schedules import crontab

# 1. Configuración del Broker (Redis)
# Usamos el mismo Redis que para el caché, pero en la DB 1 (para separar datos)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/1")

# 2. Inicializar la App Celery
celery_app = Celery(
    "goalos_worker",
    broker=REDIS_URL,
    backend=REDIS_URL
)

# 3. Configuración General
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# 4. DEFINICIÓN DE CRONOGRAMA (EL LATIDO)
# Aquí le decimos: "Ejecuta estas funciones automáticamente"
celery_app.conf.beat_schedule = {
    "daily-ingestion-routine": {
        "task": "src.tasks.ingestion.run_daily_ingestion",
        "schedule": crontab(hour=0, minute=1),
    },
    "scheduled-sync-job": {
        "task": "src.tasks.workers.scheduled_sync_job",
        "schedule": crontab(hour=10, minute=0), # 05:00 AM Ecuador (UTC-5)
    },
    "scheduled-audit-job": {
        "task": "src.tasks.workers.scheduled_audit_job",
        "schedule": crontab(hour=4, minute=55), # 23:55 PM Ecuador (UTC-5)
    },
}

# Auto-descubrir tareas en carpetas
celery_app.autodiscover_tasks(["src.tasks.ingestion", "src.tasks.workers"])