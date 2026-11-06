import "dotenv/config";
import pg from "pg";

const { Pool } = pg;

export const pool = new Pool({
  host: process.env.DB_HOST,
  port: Number(process.env.DB_PORT || 5432),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 5,
  connectionTimeoutMillis: 5000,
  idleTimeoutMillis: 30000
});

pool.on("error", (err) => {
  console.error("Idle PostgreSQL client error:", err.message);
});

export async function getUsers(limit = 10) {
  const result = await pool.query(
    `SELECT id, name, email, created_at
     FROM lab_users
     ORDER BY id
     LIMIT $1`,
    [limit]
  );

  return result.rows;
}

export async function getUserById(id) {
  const result = await pool.query(
    `SELECT id, name, email, created_at
     FROM lab_users
     WHERE id = $1`,
    [id]
  );

  return result.rows[0] ?? null;
}