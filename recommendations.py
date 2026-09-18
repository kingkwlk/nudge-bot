"""Filtering and selection logic, independent of Discord."""

import random

from database import Activity


ENERGY_LEVELS = {"low": 0, "medium": 1, "high": 2}


def matching_activities(
    activities: list[Activity],
    available_minutes: int,
    energy: str,
    category: str = "any",
    exclude_id: int | None = None,
) -> list[Activity]:
    energy = energy.strip().lower()
    category = category.strip().lower()
    if available_minutes <= 0:
        raise ValueError("Available time must be positive.")
    if energy not in ENERGY_LEVELS:
        raise ValueError("Energy must be low, medium, or high.")
    return [
        activity
        for activity in activities
        if activity.duration_minutes <= available_minutes
        and ENERGY_LEVELS[activity.energy] <= ENERGY_LEVELS[energy]
        and (category == "any" or activity.category.lower() == category)
        and activity.id != exclude_id
    ]


def choose_activity(matches: list[Activity]) -> Activity | None:
    return random.choice(matches) if matches else None
