from datetime import datetime, timezone
import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "property_advisor.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS saved_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                location TEXT NOT NULL,
                tier TEXT NOT NULL,
                property_type TEXT NOT NULL,
                current_price REAL NOT NULL,
                target_year INTEGER NOT NULL,
                projected_base REAL NOT NULL,
                direction TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS moderator_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                snapshot_key TEXT NOT NULL,
                location TEXT NOT NULL,
                tier TEXT NOT NULL,
                property_type TEXT NOT NULL,
                target_year INTEGER NOT NULL,
                auto_price REAL NOT NULL,
                projected_price REAL NOT NULL,
                direction TEXT NOT NULL,
                market_change TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS market_overrides (
                location_key TEXT PRIMARY KEY,
                state_name TEXT NOT NULL,
                area_name TEXT NOT NULL,
                base_price REAL NOT NULL,
                base_cagr REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def save_analysis_record(record: dict) -> None:
    init_db()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO saved_analyses (
                created_at, location, tier, property_type,
                current_price, target_year, projected_base, direction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now_iso,
                record["Location"],
                record["Tier"],
                record["Property Type"],
                float(record["Current Price (Auto)"]),
                int(record["Target Year"]),
                float(record["Projected Base"]),
                record["Direction"],
            ),
        )
        conn.commit()


def fetch_saved_analyses() -> pd.DataFrame:
    init_db()
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                created_at AS "Saved At",
                location AS "Location",
                tier AS "Tier",
                property_type AS "Property Type",
                current_price AS "Current Price (Auto)",
                target_year AS "Target Year",
                projected_base AS "Projected Base",
                direction AS "Direction"
            FROM saved_analyses
            ORDER BY id DESC
            """,
            conn,
        )
    return df


def clear_saved_analyses_db() -> None:
    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM saved_analyses")
        conn.commit()


def log_moderator_change_if_new(entry: dict) -> bool:
    init_db()
    with get_connection() as conn:
        last_row = conn.execute(
            "SELECT snapshot_key, projected_price FROM moderator_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()

        if last_row and last_row["snapshot_key"] == entry["snapshot_key"]:
            return False

        if last_row and float(last_row["projected_price"]) > 0:
            prev_price = float(last_row["projected_price"])
            shift_pct = ((float(entry["projected_price"]) - prev_price) / prev_price) * 100.0
            if shift_pct > 0.5:
                market_change = f"SHIFT UP ({shift_pct:+.1f}%)"
            elif shift_pct < -0.5:
                market_change = f"SHIFT DOWN ({shift_pct:+.1f}%)"
            else:
                market_change = "STEADY (0.0%)"
        else:
            market_change = f"ACTIVE ({entry['direction']})"

        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        conn.execute(
            """
            INSERT INTO moderator_logs (
                recorded_at, snapshot_key, location, tier, property_type,
                target_year, auto_price, projected_price, direction, market_change
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                now_iso,
                entry["snapshot_key"],
                entry["location"],
                entry["tier"],
                entry["property_type"],
                int(entry["target_year"]),
                float(entry["auto_price"]),
                float(entry["projected_price"]),
                entry["direction"],
                market_change,
            ),
        )
        conn.commit()
        return True


def fetch_moderator_logs(limit: int = 50) -> pd.DataFrame:
    init_db()
    with get_connection() as conn:
        df = pd.read_sql_query(
            """
            SELECT
                recorded_at AS "Timestamp",
                location AS "Location",
                tier AS "Tier",
                property_type AS "Property",
                target_year AS "Target Year",
                auto_price AS "Auto Price Today",
                projected_price AS "Projected Value",
                direction AS "Direction",
                market_change AS "Market Change"
            FROM moderator_logs
            ORDER BY id DESC
            LIMIT ?
            """,
            conn,
            params=(int(limit),),
        )
    return df


def upsert_market_override(state_name: str, area_name: str, base_price: float, base_cagr: float) -> None:
    init_db()
    key = f"{state_name.strip().lower()}::{area_name.strip().lower()}"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO market_overrides (location_key, state_name, area_name, base_price, base_cagr, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(location_key) DO UPDATE SET
                base_price = excluded.base_price,
                base_cagr = excluded.base_cagr,
                updated_at = excluded.updated_at
            """,
            (key, state_name.strip(), area_name.strip(), float(base_price), float(base_cagr), now_iso),
        )
        conn.commit()


def fetch_market_overrides() -> dict:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT location_key, state_name, area_name, base_price, base_cagr, updated_at FROM market_overrides"
        ).fetchall()
    return {
        row["location_key"]: {
            "state_name": row["state_name"],
            "area_name": row["area_name"],
            "base_price": float(row["base_price"]),
            "base_cagr": float(row["base_cagr"]),
            "updated_at": row["updated_at"],
        }
        for row in rows
    }