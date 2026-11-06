
import "dotenv/config";

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { createMcpExpressApp } from "@modelcontextprotocol/sdk/server/express.js";
import { z } from "zod";

import { pool, getUsers, getUserById } from "./db.js";

const PORT = Number(process.env.PORT || 3000);
const app = createMcpExpressApp();

// Preserve the professor's original HTTP endpoint.
app.get("/context", (req, res) => {
  res.json({
    message: "Hello from MCP Server",
    timestamp: new Date()
  });
});

// Create an MCP server and register its capabilities.
function createServer() {
  const server = new McpServer({
    name: "lab-12-postgresql-mcp",
    version: "1.0.0"
  });

  // Tool 1: Verify database connectivity.
  server.registerTool(
    "check_database",
    {
      title: "Check Database",
      description: "Check whether PostgreSQL is accessible."
    },
    async () => {
      try {
        const result = await pool.query("SELECT 1 AS status");

        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              connected: result.rows[0].status === 1
            })
          }]
        };
      } catch (error) {
        console.error("Database check failed:", error);
        return {
          isError: true,
          content: [{
            type: "text",
            text: "Database connection failed."
          }]
        };
      }
    }
  );

  // Tool 2: Retrieve users from PostgreSQL.
  server.registerTool(
    "list_users",
    {
      title: "List Users",
      description: "Retrieve a limited list of lab users.",
      inputSchema: {
        limit: z.number().int().min(1).max(100).default(10)
      }
    },
    async ({ limit }) => {
      try {
        const users = await getUsers(limit);

        return {
          content: [{
            type: "text",
            text: JSON.stringify(users, null, 2)
          }]
        };
      } catch (error) {
        console.error("List users failed:", error);
        return {
          isError: true,
          content: [{
            type: "text",
            text: "Unable to retrieve users."
          }]
        };
      }
    }
  );

  // Tool 3: Retrieve one user by ID.
  server.registerTool(
    "get_user",
    {
      title: "Get User",
      description: "Retrieve a lab user using their numeric ID.",
      inputSchema: {
        id: z.number().int().positive()
      }
    },
    async ({ id }) => {
      try {
        const user = await getUserById(id);

        return {
          content: [{
            type: "text",
            text: JSON.stringify(
              user ?? { message: "User not found" },
              null,
              2
            )
          }]
        };
      } catch (error) {
        console.error("Get user failed:", error);
        return {
          isError: true,
          content: [{
            type: "text",
            text: "Unable to retrieve user."
          }]
        };
      }
    }
  );

  // MCP resource: Read a snapshot of lab users.
  server.registerResource(
    "lab-users",
    "postgres://lab/users",
    {
      title: "Lab Users",
      description: "Read-only PostgreSQL user records.",
      mimeType: "application/json"
    },
    async (uri) => {
      const users = await getUsers(20);

      return {
        contents: [{
          uri: uri.href,
          mimeType: "application/json",
          text: JSON.stringify(users, null, 2)
        }]
      };
    }
  );

  return server;
}

// Stateless MCP over Streamable HTTP.
app.post("/mcp", async (req, res) => {
  const server = createServer();

  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true
  });

  res.once("finish", () => {
    void server.close().catch(console.error);
  });

  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("MCP request failed:", error);

    if (!res.headersSent) {
      res.status(500).json({
        error: "Internal MCP server error"
      });
    }
  }
});

app.get("/mcp", (req, res) => {
  res.status(405).set("Allow", "POST").end();
});

app.delete("/mcp", (req, res) => {
  res.status(405).set("Allow", "POST").end();
});

const httpServer = app.listen(PORT, "127.0.0.1", () => {
  console.log(`HTTP server: http://localhost:${PORT}/context`);
  console.log(`MCP endpoint: http://localhost:${PORT}/mcp`);
});

async function shutdown() {
  httpServer.close();
  await pool.end();
}

process.on("SIGINT", async () => {
  await shutdown();
  process.exit(0);
});
