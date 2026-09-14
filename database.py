"""SQLite storage for the Nudge bot."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


DATABASE_PATH = Path(__file__).with_name("nudge.db")

DEFAULT_ACTIVITIES = [
    ("Clean your desk", 10, "low", "chores"),
    ("Take out the trash", 10, "low", "chores"),
    ("Tidy one room", 20, "medium", "chores"),
    ("Read a book", 20, "low", "relaxation"),
    ("Listen to music", 15, "low", "relaxation"),
    ("Take a screen break", 10, "low", "relaxation"),
    ("Go for a walk", 20, "medium", "exercise"),
    ("Stretch", 10, "low", "exercise"),
    ("Complete a short workout", 30, "high", "exercise"),
    ("Practice Python", 30, "medium", "productive"),
    ("Organize your task list", 10, "low", "productive"),
    ("Work on a personal project", 45, "high", "productive"),
    ("Play a game", 30, "low", "fun"),
    ("Watch one episode of a show", 30, "low", "fun"),
    ("Draw or sketch something", 20, "medium", "fun"),
    ("Message a friend", 10, "low", "social"),
    ("Call a family member", 20, "medium", "social"),
]


@dataclass(frozen=True)
class Activity:
    id: int
    name: str
    duration_minutes: int
    energy: str
    category: str


def connect(database_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_path: Path = DATABASE_PATH) -> None:
    with connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                duration_minutes INTEGER NOT NULL CHECK (duration_minutes > 0),
                energy TEXT NOT NULL CHECK (energy IN ('low', 'medium', 'high')),
                category TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )


def seed_default_activities(database_path: Path = DATABASE_PATH) -> int:
    """Add the starter activity library once and return the number added."""
    with connect(database_path) as connection:
        already_seeded = connection.execute(
            "SELECT 1 FROM app_settings WHERE key = 'defaults_seeded'"
        ).fetchone()
        if already_seeded:
            return 0

        connection.executemany(
            """
            INSERT INTO activities (name, duration_minutes, energy, category)
            VALUES (?, ?, ?, ?)
            """,
            DEFAULT_ACTIVITIES,
        )
        connection.execute(
            "INSERT INTO app_settings (key, value) VALUES ('defaults_seeded', '1')"
        )
        return len(DEFAULT_ACTIVITIES)


def add_activity(
    name: str,
    duration_minutes: int,
    energy: str,
    category: str,
    database_path: Path = DATABASE_PATH,
) -> int:
    cleaned_name = name.strip()
    cleaned_energy = energy.strip().lower()
    cleaned_category = category.strip().lower()

    if not cleaned_name:
        raise ValueError("Activity name cannot be empty.")
    if duration_minutes <= 0:
        raise ValueError("Duration must be greater than zero.")
    if cleaned_energy not in {"low", "medium", "high"}:
        raise ValueError("Energy must be low, medium, or high.")
    if not cleaned_category:
        raise ValueError("Category cannot be empty.")

    with connect(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO activities (name, duration_minutes, energy, category)
            VALUES (?, ?, ?, ?)
            """,
            (cleaned_name, duration_minutes, cleaned_energy, cleaned_category),
        )
        return int(cursor.lastrowid)


def list_activities(database_path: Path = DATABASE_PATH) -> list[Activity]:
    with connect(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, name, duration_minutes, energy, category
            FROM activities
            ORDER BY id
            """
        ).fetchall()

    return [Activity(**dict(row)) for row in rows]
