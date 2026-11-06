# tests/test_database.py
import asyncio
import pytest

import pytest_asyncio
import os
from dotenv import load_dotenv
import asyncpg

# Load test environment variables
load_dotenv(".env.test")

# Testing database configuration
TEST_DB_CONFIG = {
    "user": os.getenv("TEST_DB_USER"),
    "password": os.getenv("TEST_DB_PASSWORD"),
    "database": os.getenv("TEST_DB_NAME"),
    "host": os.getenv("TEST_DB_HOST", "localhost"),
    "port": int(os.getenv("TEST_DB_PORT", "5432")),
}

@pytest_asyncio.fixture
async def db_pool():
    """Create a test database pool."""
    pool = await asyncpg.create_pool(**TEST_DB_CONFIG)
    yield pool
    await pool.close()

@pytest_asyncio.fixture
async def setup_test_data(db_pool):
    """Set up test data before tests and clean up after."""
    async with db_pool.acquire() as conn:
        # Create test tables
        await conn.execute("""
            CREATE TEMPORARY TABLE users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL DEFAULT 'General',
                role TEXT NOT NULL DEFAULT 'User',
                active BOOLEAN NOT NULL DEFAULT TRUE,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        
        # Insert test users
        await conn.executemany(
            """
            INSERT INTO users (username, email, department, role) 
            VALUES ($1, $2, $3, $4)
            """,
            [
                ("test1", "test1@example.com", "Engineering", "Developer"),
                ("test2", "test2@example.com", "Marketing", "Manager"),
                ("test3", "test3@example.com", "Sales", "Representative")
            ]
        )
    
    yield
    
    # Cleanup happens automatically for temporary tables

@pytest.mark.asyncio
async def test_fetch_recent_users(db_pool, setup_test_data):
    """Test that fetching recent users works correctly."""
    from resource.users import fetch_recent_users
    
    # Monkeypatch db_pool
    import database
    database.db_pool = db_pool
    
    # Execute the function
    result = await fetch_recent_users(limit=10)
    
    # Assertions
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["username"] in ["test1", "test2", "test3"]
    assert "email" in result[0]
    assert "department" in result[0]

@pytest.mark.asyncio
async def test_create_user(db_pool, setup_test_data):
    """Test that creating a user works correctly."""
    from tools.users import create_user
    
    # Monkeypatch db_pool
    import database
    database.db_pool = db_pool
    
    # Test data
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "department": "Finance",
        "role": "Analyst"
    }
    
    # Execute the function
    result = await create_user(user_data)
    
    # Assertions
    assert result["status"] == "success"
    
    # Verify in database
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            "newuser"
        )
        
    assert user is not None
    assert user["email"] == "newuser@example.com"
    assert user["department"] == "Finance"