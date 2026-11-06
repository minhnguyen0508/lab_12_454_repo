from typing import Dict, Any, Optional
from pydantic import BaseModel, EmailStr, Field, validator
import logging
import re
from database import db_pool

logger = logging.getLogger("mcp_database.tools.users")

class CreateUserRequest(BaseModel):
    """Validation model for user creation requests."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    department: Optional[str] = "General"
    role: Optional[str] = "User"
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric')
        return v

async def create_user(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new user in the database.
    
    Args:
        data: User data containing username, email, etc.
        
    Returns:
        Response with status and user info
    """
    try:
        # Validate the input data with Pydantic
        user_data = CreateUserRequest(**data)
        
        if not db_pool:
            logger.error("Database pool not initialized")
            return {
                "status": "error",
                "message": "Database connection not available"
            }
        
        async with db_pool.acquire() as connection:
            # Check if user already exists
            existing_user = await connection.fetchrow(
                "SELECT id FROM users WHERE username = $1 OR email = $2",
                user_data.username,
                user_data.email
            )
            
            if existing_user:
                return {
                    "status": "error",
                    "message": "User with this username or email already exists"
                }
            
            # Insert the new user
            query = """
                INSERT INTO users (username, email, department, role) 
                VALUES ($1, $2, $3, $4)
                RETURNING id;
            """
            
            user_id = await connection.fetchval(
                query,
                user_data.username,
                user_data.email,
                user_data.department,
                user_data.role
            )
            
            logger.info(f"Created new user: {user_data.username} (ID: {user_id})")
            
            return {
                "status": "success",
                "message": f"User {user_data.username} created successfully",
                "user_id": user_id
            }
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return {
            "status": "error",
            "message": f"Failed to create user: {str(e)}"
        }

async def transfer_user_to_department(
    user_id: int,
    new_department: str
) -> Dict[str, Any]:
    """
    Transfer a user to a new department, recording the change in the audit log.
    
    Args:
        user_id: ID of the user to transfer
        new_department: Name of the target department
        
    Returns:
        Status of the operation
    """
    try:
        if not db_pool:
            return {"error": "Database connection not available"}
            
        async with db_pool.acquire() as connection:
            # Start a transaction
            async with connection.transaction():
                # Get current department
                current_dept = await connection.fetchval(
                    "SELECT department FROM users WHERE id = $1",
                    user_id
                )
                
                if not current_dept:
                    return {"error": "User not found"}
                
                # Update the user's department
                await connection.execute(
                    "UPDATE users SET department = $1 WHERE id = $2",
                    new_department,
                    user_id
                )
                
                # Record the change in audit log
                await connection.execute(
                    """
                    INSERT INTO user_audit_log 
                    (user_id, field_changed, old_value, new_value) 
                    VALUES ($1, $2, $3, $4)
                    """,
                    user_id,
                    "department",
                    current_dept,
                    new_department
                )
                
                logger.info(f"Transferred user {user_id} from {current_dept} to {new_department}")
                
                return {
                    "status": "success",
                    "message": f"User transferred from {current_dept} to {new_department}"
                }
    except Exception as e:
        logger.error(f"Error transferring user: {e}")
        return {"error": f"Transfer failed: {str(e)}"}