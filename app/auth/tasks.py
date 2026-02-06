import asyncio
from celery import Celery
from celery.schedules import crontab
from app.database import AsyncSessionLocal
from . import crud

celery_app = Celery("tasks", broker="redis://redis:6379/0")


@celery_app.task(name="cleanup_expired_tokens")
def cleanup_expired_tokens():
    async def run_cleanup():
        async with AsyncSessionLocal() as db:
            await crud.delete_expired_activation_tokens(db)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(run_cleanup())


celery_app.conf.beat_schedule = {
    "delete-tokens-every-night": {
        "task": "cleanup_expired_tokens",
        "schedule": crontab(hour=0, minute=0),
    },
}



