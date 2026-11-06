import asyncio
import logging
from mcp_server import MCPServer
from database import init_db, close_db
from resource.users import fetch_recent_users
from resource.users import fetch_users_by_criteria
from tools.users import create_user
from tools.users import transfer_user_to_department
import asyncpg

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_server")

# Create MCP server
server = MCPServer()

# Register the resource
@server.resource(
    name="recent_users", 
    description="Fetch the most recent users from the database."
)
async def recent_users_resource():
    return await fetch_recent_users(limit=20)

async def main():
    try:
        # Initialize the database
        await init_db()
        
        # Start the server
        logger.info("Starting MCP server...")
        await server.start()
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        # Close database connections on shutdown
        await close_db()

@server.resource(
    name="users_by_criteria", 
    description="Fetch users matching specific criteria like department or role."
)
async def users_by_criteria_resource(data: dict):
    return await fetch_users_by_criteria(
        department=data.get("department"),
        role=data.get("role"),
        active=data.get("active", True),
        limit=data.get("limit", 20)
    )

# Register the tool
@server.tool(
    name="create_user",
    description="Create a new user in the database."
)
async def create_user_tool(data: dict):
    return await create_user(data)

@server.tool(
    name="transfer_user",
    description="Transfer a user to a new department."
)
async def transfer_user_tool(data: dict):
    user_id = data.get("user_id")
    new_department = data.get("new_department")
    
    if not user_id or not new_department:
        return {"error": "Missing user_id or new_department"}
        
    return await transfer_user_to_department(user_id, new_department)

if __name__ == "__main__":
    asyncio.run(main())