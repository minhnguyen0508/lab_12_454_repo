import { pool, getUsers } from "./db.js";

async function main() {
  try {
    const result = await pool.query("SELECT NOW() AS server_time");

    console.log("PostgreSQL connection successful!");
    console.log("Database time:", result.rows[0].server_time);

    const users = await getUsers();
    console.table(users);
  } catch (error) {
    console.error("Database test failed:", error.message);
    process.exitCode = 1;
  } finally {
    await pool.end();
  }
}

main();