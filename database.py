import os
import asyncpg
import logging 
from dotenv import load_dotenv


#logging config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("mcp_database")


#load environment variables
load_dotenv()

#databse config
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "mcp_lab"),
    "user": os.getenv("DB_USER", "mcp_user"),
    "password": os.getenv("DB_PASSWORD"),
}


#global var
db_pool = None

async def init_db():
    """Initialize te database connection pool."""
    global db_pool 
    try: 
        db_pool= await asyncpg.create_pool(
            **DB_CONFIG,
            min_size=1,
            max_size=10,
            command_timeout =60,
            timeout = 10,
        )
        logger.info("Database connection pool established")
        #Test the connection 
        async with db_pool.acquire() as connection:
            version =await connection.fetchval("SELECT version();")
            logger.info(f"Connected to PostgreSQL: {version}")

        return db_pool

    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        raise 

async def close_db():
    """CLose the databse connection pool"""
    global db_pool
    if db_pool:
        await db_pool.close()
        logger.info("Database cconnection pool closed")