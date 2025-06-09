import sqlite3
from typing import Optional, Dict, Any

DB_FILE = "users.db"


class UserDB:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # Create users table
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    school TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    join_date INTEGER NOT NULL
                );
            """)
            # Create alts table
            c.execute("""
                CREATE TABLE IF NOT EXISTS alts (
                    alt_id INTEGER PRIMARY KEY,
                    owner_id INTEGER NOT NULL,
                    FOREIGN KEY (owner_id) REFERENCES users(user_id),
                    CHECK (alt_id != owner_id)
                );
            """)
            conn.commit()

    def add_user(
        self,
        user_id: int,
        name: str,
        school: str,
        year: int,
        email: str,
        join_date: int,
    ):
        """Add a real user."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                """
                INSERT INTO users (user_id, name, school, year, email, join_date)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (user_id, name, school, year, email, join_date),
            )
            conn.commit()

    def add_alt(self, alt_id: int, owner_id: int):
        """Add an alt account linked to an existing real user."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()

            # Ensure owner exists
            c.execute("SELECT 1 FROM users WHERE user_id = ?", (owner_id,))
            if c.fetchone() is None:
                raise ValueError(f"Owner with user_id {owner_id} does not exist.")

            # Ensure alt is not the same as owner
            if alt_id == owner_id:
                raise ValueError("Alt ID cannot be the same as owner ID.")

            # Add the alt to the alts table
            c.execute(
                """
                INSERT INTO alts (alt_id, owner_id)
                VALUES (?, ?);
                """,
                (alt_id, owner_id),
            )
            conn.commit()

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve the effective user data for a given user_id (real or alt)."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Check if user is an alt
            c.execute("SELECT owner_id FROM alts WHERE alt_id = ?", (user_id,))
            row = c.fetchone()
            effective_user_id = row["owner_id"] if row else user_id

            # Fetch user info
            c.execute("SELECT * FROM users WHERE user_id = ?", (effective_user_id,))
            user_row = c.fetchone()
            return dict(user_row) if user_row else None


# Singleton should be fine here...
_db_instance = None


def get_db() -> UserDB:
    global _db_instance
    if _db_instance is None:
        _db_instance = UserDB()
    return _db_instance
