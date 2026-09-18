"""Small test for Nudge's SQLite foundation.

Run with: python test.py
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    DEFAULT_ACTIVITIES,
    Activity,
    add_activity,
    initialize_database,
    list_activities,
    seed_default_activities,
)
from recommendations import choose_activity, matching_activities


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

    examples = [
        Activity(1, "Read", 10, "low", "relaxation"),
        Activity(2, "Code", 30, "medium", "productive"),
        Activity(3, "Workout", 20, "high", "exercise"),
        Activity(4, "Walk", 20, "medium", "exercise"),
    ]
    assert [a.id for a in matching_activities(examples, 20, "low")] == [1]
    assert [a.id for a in matching_activities(examples, 30, "medium")] == [1, 2, 4]
    assert matching_activities(examples, 30, " HIGH ", " Exercise ") == examples[2:]
    assert matching_activities(examples, 5, "high") == []
    assert matching_activities(examples, 30, "high", "unknown") == []
    alternatives = matching_activities(examples, 30, "medium", exclude_id=1)
    assert {a.id for a in alternatives} == {2, 4}
    assert choose_activity([]) is None
    assert choose_activity([examples[0]]) == examples[0]
    for _ in range(20):
        assert choose_activity(alternatives) in alternatives
    for minutes, energy in [(0, "low"), (30, "invalid")]:
        try:
            matching_activities(examples, minutes, energy)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid filters should be rejected.")
    print("Recommendation tests passed.")


if __name__ == "__main__":
    main()
