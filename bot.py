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
    Activity,
    add_activity,
    initialize_database,
    list_activities,
    seed_default_activities,
)
from recommendations import choose_activity, matching_activities


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


def recommendation_embed(activity: Activity, time: int, energy: str) -> discord.Embed:
    embed = discord.Embed(
        title="Your nudge",
        description=activity.name[:4096],
        color=discord.Color.green(),
    )
    embed.add_field(name="Time", value=f"{activity.duration_minutes} minutes")
    embed.add_field(name="Energy", value=activity.energy.title())
    embed.add_field(name="Category", value=activity.category[:1024])
    embed.set_footer(
        text=f"Fits your {time}-minute window and {energy} energy budget."
    )
    return embed


class NudgeView(discord.ui.View):
    def __init__(
        self, time: int, energy: str, category: str, current_id: int, has_another: bool
    ) -> None:
        super().__init__(timeout=300)
        self.time = time
        self.energy = energy
        self.category = category
        self.current_id = current_id
        self.another.disabled = not has_another

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return not await reject_if_not_owner(interaction)

    @discord.ui.button(label="Another", style=discord.ButtonStyle.primary)
    async def another(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ) -> None:
        matches = matching_activities(
            list_activities(), self.time, self.energy, self.category,
            exclude_id=self.current_id,
        )
        activity = choose_activity(matches)
        if activity is None:
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(
                "No other activities fit. Add one or try broader filters.",
                ephemeral=True,
            )
            return
        self.current_id = activity.id
        await interaction.response.edit_message(
            embed=recommendation_embed(activity, self.time, self.energy), view=self
        )


@bot.tree.command(name="nudge", description="Find something to do right now.")
@app_commands.describe(
    time="How many minutes you have",
    energy="The maximum energy you want to spend",
    category="An activity category, or any for all categories",
)
@app_commands.choices(energy=[
    app_commands.Choice(name="Low", value="low"),
    app_commands.Choice(name="Medium", value="medium"),
    app_commands.Choice(name="High", value="high"),
])
async def nudge(
    interaction: discord.Interaction,
    time: app_commands.Range[int, 1, 1440],
    energy: app_commands.Choice[str],
    category: str = "any",
) -> None:
    if await reject_if_not_owner(interaction):
        return
    matches = matching_activities(list_activities(), time, energy.value, category)
    activity = choose_activity(matches)
    if activity is None:
        await interaction.response.send_message(
            "No activities fit those filters. Try more time, a higher energy "
            "level, category:any, or add an activity with /activity-add.",
            ephemeral=True,
        )
        return
    await interaction.response.send_message(
        embed=recommendation_embed(activity, time, energy.value),
        view=NudgeView(time, energy.value, category, activity.id, len(matches) > 1),
        ephemeral=True,
    )


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
