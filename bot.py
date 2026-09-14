"""Entry point for the Nudge Discord bot."""

from __future__ import annotations

import os

import certifi

# Some macOS Python installations do not include a system certificate bundle.
# Point HTTPS clients such as discord.py/aiohttp at certifi's trusted bundle.
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from database import (
    add_activity,
    initialize_database,
    list_activities,
    seed_default_activities,
)


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID_TEXT = os.getenv("OWNER_ID")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


def is_owner(interaction: discord.Interaction) -> bool:
    return OWNER_ID_TEXT is not None and str(interaction.user.id) == OWNER_ID_TEXT


async def reject_if_not_owner(interaction: discord.Interaction) -> bool:
    if is_owner(interaction):
        return False

    await interaction.response.send_message(
        "Nudge is currently a personal bot.", ephemeral=True
    )
    return True


@bot.event
async def on_ready() -> None:
    initialize_database()
    added_count = seed_default_activities()
    await bot.tree.sync()
    print(f"Nudge is online as {bot.user}.")
    if added_count:
        print(f"Added {added_count} built-in activities.")


@bot.tree.command(name="activity-add", description="Add an activity to Nudge.")
@app_commands.describe(
    name="What you could do",
    duration="How many minutes it takes",
    energy="How much energy it requires",
    category="The type of activity",
)
@app_commands.choices(
    energy=[
        app_commands.Choice(name="Low", value="low"),
        app_commands.Choice(name="Medium", value="medium"),
        app_commands.Choice(name="High", value="high"),
    ]
)
async def activity_add(
    interaction: discord.Interaction,
    name: str,
    duration: app_commands.Range[int, 1, 1440],
    energy: app_commands.Choice[str],
    category: str,
) -> None:
    if await reject_if_not_owner(interaction):
        return

    activity_id = add_activity(name, duration, energy.value, category)
    await interaction.response.send_message(
        f"Added **{name}** as activity #{activity_id}.", ephemeral=True
    )


@bot.tree.command(name="activity-list", description="List your saved activities.")
async def activity_list(interaction: discord.Interaction) -> None:
    if await reject_if_not_owner(interaction):
        return

    activities = list_activities()
    if not activities:
        await interaction.response.send_message(
            "You have no saved activities yet.", ephemeral=True
        )
        return

    lines = [
        f"**#{activity.id} {activity.name}** — {activity.duration_minutes} min, "
        f"{activity.energy} energy, {activity.category}"
        for activity in activities
    ]
    await interaction.response.send_message("\n".join(lines), ephemeral=True)


def main() -> None:
    if not TOKEN or not OWNER_ID_TEXT:
        raise RuntimeError("Add DISCORD_TOKEN and OWNER_ID to a .env file first.")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
