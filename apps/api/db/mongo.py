from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from config import get_settings

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None


async def connect_db():
    global _client, _db
    settings = get_settings()
    _client = AsyncIOMotorClient(settings.mongodb_uri)
    _db = _client[settings.database_name]

    # Create indexes
    await _db.users.create_index("email", unique=True)
    await _db.events.create_index([("user_id", 1), ("timestamp", -1)])
    await _db.events.create_index("session_id")
    await _db.sessions.create_index("user_id")
    await _db.sessions.create_index("session_id", unique=True)
    await _db.passports.create_index("user_id", unique=True)
    await _db.tasks.create_index("task_id", unique=True)
    await _db.jobs.create_index("job_id", unique=True)

    print("Connected to MongoDB")


async def close_db():
    global _client
    if _client:
        _client.close()
        print("Disconnected from MongoDB")


def get_db() -> AsyncIOMotorDatabase:
    if _db is None:
        raise RuntimeError("Database not initialized. Call connect_db() first.")
    return _db
