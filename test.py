"""Small test for Nudge's SQLite foundation.

Run with: python test.py
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    DEFAULT_ACTIVITIES,
    add_activity,
    initialize_database,
    list_activities,
    seed_default_activities,
)


def main() -> None:
    with TemporaryDirectory() as directory:
        database_path = Path(directory) / "test_nudge.db"
        initialize_database(database_path)

        activity_id = add_activity(
            name="Practice Python",
            duration_minutes=30,
            energy="medium",
            category="productive",
            database_path=database_path,
        )
        activities = list_activities(database_path)

        assert activity_id == 1
        assert len(activities) == 1
        assert activities[0].name == "Practice Python"

        added_count = seed_default_activities(database_path)
        assert added_count == len(DEFAULT_ACTIVITIES)
        assert len(list_activities(database_path)) == len(DEFAULT_ACTIVITIES) + 1

        # Defaults are only inserted once, even after another startup.
        assert seed_default_activities(database_path) == 0
        assert len(list_activities(database_path)) == len(DEFAULT_ACTIVITIES) + 1
        print("Database test passed.")


if __name__ == "__main__":
    main()
