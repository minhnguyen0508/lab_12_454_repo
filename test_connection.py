import asyncio
from database import init_db, close_db

async def main():
    try:
        pool = await init_db()

        async with pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")

        print("Database connection successful:", result)

    finally:
        await close_db()

if __name__ == "__main__":
    asyncio.run(main())