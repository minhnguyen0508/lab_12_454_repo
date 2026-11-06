from typing import List, Dict, Any, Optional 
import logging
from database import db_pool 

logger = logging.getLogger("mcp_database.resources.users")

async def fetch_recent_users(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Fetch the most recent users from the database

    args: 
        limit: maximum number of users to return 
    Return: 
        List of user objects
    """
    try: 
        if not db_pool: 
            logger.error("Database pool not initialized")
            return {"error": "Database connection not available"}

        async with db_pool.acquire() as connection: 
            query = """ 
                SELECT id, username, email, created_at
                FROM users
                ORDER BY created_at DESC
                LIMIT $1;
            """
            rows = await connection.fetch(query, limit)

        users = []
        for row in rows:
            user = dict(row)

            if "created_at" in user and user["created_at"]:
                user["created_at"] = user["created_at"].isoformat()
            users.append(user)
        logger.info(f"Fetched{len(users)} recent users")
        return users
    except Exception as e:
        logger.error(f"Error fetching recent users: {e}")
        return {"error": f"Database error: {str(e)}"}

async def fetch_users_by_criteria(
    department: Optional[str] = None,
    role: Optional[str] = None,
    active: Optional[bool] = True,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Fetch users matching specific criteria.
    
    Args:
        department: Filter by department (optional)
        role: Filter by role (optional)
        active: Filter by active status (default: True)
        limit: Maximum results to return (default: 20)
        
    Returns:
        List of matching user objects
    """
    try:
        if not db_pool:
            logger.error("Database pool not initialized")
            return {"error": "Database connection not available"}
            
        # Build dynamic query
        conditions = ["active = $1"]
        params = [active]
        param_count = 1
        
        if department:
            param_count += 1
            conditions.append(f"department = ${param_count}")
            params.append(department)
            
        if role:
            param_count += 1
            conditions.append(f"role = ${param_count}")
            params.append(role)
            
        # Build the final query
        query = f"""
            SELECT id, username, email, department, role, created_at 
            FROM users 
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC 
            LIMIT ${param_count + 1};
        """
        params.append(limit)
        
        async with db_pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
            
            # Convert to dictionaries and handle datetime serialization
            users = []
            for row in rows:
                user = dict(row)
                if "created_at" in user and user["created_at"]:
                    user["created_at"] = user["created_at"].isoformat()
                users.append(user)
                
            logger.info(f"Fetched {len(users)} users matching criteria")
            return users
    except Exception as e:
        logger.error(f"Error fetching users by criteria: {e}")
        return {"error": f"Database error: {str(e)}"}