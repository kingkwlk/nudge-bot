# Nudge

Nudge is a personal Discord bot that stores activities and helps decide what to
do based on available time, energy, and category.

## Current milestone

- SQLite activity storage
- One-time starter library of built-in activities
- `/activity-add` slash command
- `/activity-list` slash command
- Owner-only access

## Recommendations

Use `/nudge time:30 energy:medium category:any` to get a suggestion.
Category is optional and supports custom categories from your saved activities.
Energy is a maximum: medium also allows low-energy activities.

The **Another** button selects a different matching activity (older suggestions
can return later). It is disabled when only one activity fits. Buttons expire
after five minutes; run `/nudge` again to start a fresh recommendation.
Suggestions are private to you and do not yet record completion history.

## Local setup

1. Create and activate a Python virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and enter your Discord token and user ID.
4. Run `python test.py` to verify SQLite.
5. Run `python bot.py` to start Nudge.
