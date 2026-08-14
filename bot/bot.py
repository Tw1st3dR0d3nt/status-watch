import os
import json
import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
from datetime import datetime
import traceback
import copy

# ---- ENV SAFETY ----

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("Missing DISCORD_TOKEN")

# ---- INTENTS ----

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "data/incidents.json"
ALLOWED_IMPACTS = ["minor", "major", "critical"]

session = None

# ---- SETUP HOOK ----

async def setup_hook():
    # Command registration is performed in on_ready, after Discord has
    # populated bot.guilds. This prevents syncing an empty guild list.
    pass

bot.setup_hook = setup_hook

# ---- SESSION ----

async def get_session():
    global session
    if session is None or session.closed:
        session = aiohttp.ClientSession()
    return session

async def close_session():
    global session
    if session and not session.closed:
        await session.close()

# ---- FILE SETUP ----

os.makedirs("data", exist_ok=True)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        tracked_incidents = json.load(f)
else:
    tracked_incidents = {}

# FIXED (prevents startup spam)
first_run = True

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(tracked_incidents, f, indent=2)

CONFIG_FILE = "data/config.json"

if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
else:
    config = {"guilds": {}}

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

# ---- UI ----

class StatusView(discord.ui.LayoutView):
    def __init__(self, incident_name, timeline, url):
        super().__init__(timeout=None)

        view_details = discord.ui.Button(
            label="View Incident",
            url=url,
            style=discord.ButtonStyle.link
        )

        title_section = discord.ui.Section(
            discord.ui.TextDisplay(f"### [{incident_name}]({url})"),
            accessory=view_details
        )

        container = discord.ui.Container(
            title_section,

            # Separator ONLY between title and timeline
            discord.ui.Separator(),

            # Timeline starts below the separator
            discord.ui.TextDisplay(timeline),

        )

        self.add_item(container)

# ---- ERROR LOGGING ----

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"Error in event: {event}")
    traceback.print_exc()

# ---- EVENTS ----

commands_synced = False
command_templates = []

@bot.event
async def on_ready():
    global commands_synced, command_templates

    print(f"Logged in as {bot.user}")

    if not commands_synced:
        # Save copies of the global command definitions before clearing
        # the global registry. These templates are used for any server
        # the bot joins later.
        command_templates = [copy.copy(command) for command in tree.get_commands()]

        for guild in bot.guilds:
            try:
                tree.copy_global_to(guild=guild)
                synced = await tree.sync(guild=guild)
                print(
                    f"Guild sync complete: {guild.name} "
                    f"({guild.id}) - {len(synced)} commands"
                )
            except Exception as e:
                print(f"Guild sync failed for {guild.id}: {e}")

        # Remove the old global registrations after all existing guilds
        # have received their working guild-specific copies.
        tree.clear_commands(guild=None)

        try:
            await tree.sync()
            print("Old global commands cleared")
        except Exception as e:
            print(f"Global command cleanup failed: {e}")

        commands_synced = True

    if not check_status.is_running():
        check_status.start()
        print("Background task started")

@bot.event
async def on_guild_join(guild):
    # New servers need their own guild-specific copies.
    try:
        for command in command_templates:
            tree.add_command(
                copy.copy(command),
                guild=guild,
                override=True
            )

        synced = await tree.sync(guild=guild)
        print(
            f"Guild join sync complete: {guild.name} "
            f"({guild.id}) - {len(synced)} commands"
        )
    except Exception as e:
        print(f"Guild join sync failed for {guild.id}: {e}")

@bot.event
async def on_guild_remove(guild):
    # Remove stale per-server configuration when the bot leaves a server.
    guild_id = str(guild.id)

    if guild_id in config.get("guilds", {}):
        del config["guilds"][guild_id]
        save_config()
        print(f"Removed configuration for departed guild {guild.name} ({guild.id})")

@bot.event
async def on_disconnect():
    print("Disconnected from Discord")
    await close_session()

# ---- TIMELINE FORMATTER ----

def format_timeline(updates):
    return "\n\n".join([
        f"{datetime.fromisoformat(u['created_at'].replace('Z', '+00:00')).strftime('%b %d, %I:%M %p').replace(' 0', ' ')}\n"
        f"**{u['status'].capitalize()}** - {u['body']}"
        for u in updates
    ])

# ---- STATUS COMMAND ----

@bot.tree.command(name="status", description="Check Discord status")
async def status(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True, ephemeral=True)

    url = "https://discordstatus.com/api/v2/incidents.json"

    try:
        session = await get_session()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json()
    except Exception:
        return await interaction.followup.send(
            "Failed to fetch Discord status.",
            ephemeral=True
        )

    # Get all active incidents
    incidents = [
        i for i in data.get("incidents", [])
        if i.get("status") != "resolved"
    ]

    if incidents:
        view = discord.ui.LayoutView(timeout=None)

        for incident in incidents[:3]:
            timeline = format_timeline(incident["incident_updates"])

            view.add_item(
                discord.ui.Container(
                    discord.ui.Section(
                        discord.ui.TextDisplay(f"### [{incident['name']}]({incident['shortlink']})"),
                        accessory=discord.ui.Button(
                            label="View Incident",
                            url=incident["shortlink"],
                            style=discord.ButtonStyle.link
                        )
                    ),
                    discord.ui.Separator(),
                    discord.ui.TextDisplay(timeline),
                )
            )

            await interaction.followup.send(
                view=view,
                ephemeral=True
            )

    else:
        view = discord.ui.LayoutView(timeout=None)

        view.add_item(
            discord.ui.Container(
                discord.ui.TextDisplay("## All Systems Operational"),
                discord.ui.Separator(),
                discord.ui.TextDisplay(
                    ":green_circle: **Discord is operating normally.**"
                )
            )
        )

        await interaction.followup.send(
            view=view,
            ephemeral=True
        )

# ---- TEST COMMAND ----

@bot.tree.command(name="teststatus", description="Fetch latest incident for testing")
async def teststatus(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    try:
        session = await get_session()
        async with session.get("https://discordstatus.com/api/v2/incidents.json") as resp:
            data = await resp.json()

        incidents = data.get("incidents", [])

        if not incidents:
            await interaction.followup.send("No incidents found.", ephemeral=True)
            return

        incident = incidents[0]
        timeline = format_timeline(incident["incident_updates"])

        view = StatusView(
            incident["name"],
            timeline,
            incident["shortlink"]
        )

        await interaction.followup.send(
            view=view,
            ephemeral=True
        )

    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)

# ---- INCIDENT CHANNEL CONFIG ----

@bot.tree.command(
    name="setincidentchannel",
    description="Set this channel for automatic incident notifications.",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def setincidentchannel(
    interaction: discord.Interaction,
    channel: discord.TextChannel
):

    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used inside a server.",
            ephemeral=True
        )
        return

    guild_id = str(interaction.guild.id)
    channel_id = str(channel.id)

    config.setdefault("guilds", {})
    config["guilds"][guild_id] = {
        "channel_id": channel_id
    }

    save_config()

    await interaction.response.send_message(
        f":white_check_mark: Incident notifications will now be posted in {channel.mention}.",
        ephemeral=True
    )


@bot.tree.command(
    name="getincidentchannel",
    description="Show the configured incident notification channel.",
)
async def getincidentchannel(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used inside a server.",
            ephemeral=True
        )
        return

    guild_id = str(interaction.guild.id)
    guild_config = config["guilds"].get(guild_id)

    if not guild_config:
        await interaction.response.send_message(
            ":warning: No incident notification channel has been configured for this server.",
            ephemeral=True
        )
        return

    channel = interaction.guild.get_channel(
        int(guild_config["channel_id"])
    )

    if channel:
        await interaction.response.send_message(
            f":loudspeaker: Incident notifications are configured for {channel.mention}.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            ":warning: The configured channel no longer exists.",
            ephemeral=True
        )


@bot.tree.command(
    name="clearincidentchannel",
    description="Disable automatic incident notifications for this server.",
)
@app_commands.checks.has_permissions(manage_guild=True)
async def clearincidentchannel(interaction: discord.Interaction):

    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used inside a server.",
            ephemeral=True
        )
        return

    guild_id = str(interaction.guild.id)

    if guild_id in config["guilds"]:
        del config["guilds"][guild_id]
        save_config()

        await interaction.response.send_message(
            ":white_check_mark: Automatic incident notifications have been disabled for this server.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            ":information_source: This server does not currently have an incident notification channel configured.",
            ephemeral=True
        )

# ---- BACKGROUND TASK ----

@tasks.loop(minutes=1, reconnect=True)
async def check_status():
    global first_run

    url = "https://discordstatus.com/api/v2/incidents.json"

    try:
        session = await get_session()
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            data = await resp.json()
    except Exception as e:
        print(f"Failed to fetch status API: {e}")
        return

    configured_guilds = config.get("guilds", {})

    if not configured_guilds:
        return

    for incident in data.get("incidents", []):
        status = incident.get("status")
        incident_id = incident["id"]

        # Only skip resolved incidents that we never tracked
        if status == "resolved" and incident_id not in tracked_incidents:
            continue

        # GUARANTEED ORDER: newest -> oldest
        updates = sorted(
            incident["incident_updates"],
            key=lambda u: u["created_at"],
            reverse=True
        )

        if not updates:
            continue

        newest = updates[0]
        timeline = format_timeline(updates)

        # ---- NEW INCIDENT ----
        if incident_id not in tracked_incidents:
            if first_run:
                tracked_incidents[incident_id] = {
                    "last_update_id": newest["id"],
                    "messages": {}
                }
                save_data()
                continue

            tracked_incidents[incident_id] = {
                "last_update_id": newest["id"],
                "messages": {}
            }

            for guild_id, guild_config in configured_guilds.items():
                try:
                    channel = bot.get_channel(int(guild_config["channel_id"]))

                    if channel is None:
                        channel = await bot.fetch_channel(
                            int(guild_config["channel_id"])
                        )

                    msg = await channel.send(
                        view=StatusView(
                            incident["name"],
                            timeline,
                            incident["shortlink"]
                        )
                    )

                    tracked_incidents[incident_id]["messages"][guild_id] = msg.id

                except Exception as e:
                    print(
                        f"Failed to send new incident to guild "
                        f"{guild_id}: {e}"
                    )

            save_data()
            continue

        # ---- EXISTING INCIDENT ----
        tracked = tracked_incidents[incident_id]

        # Backward-compatible migration from the old single-message format.
        if "messages" not in tracked:
            tracked["messages"] = {}

        legacy_message_id = tracked.pop("message_id", None)

        # If there is only one configured server, we can safely associate
        # the old message with that server.
        if legacy_message_id and len(configured_guilds) == 1:
            only_guild_id = next(iter(configured_guilds))
            tracked["messages"][only_guild_id] = legacy_message_id
            save_data()

        if first_run:
            # If a tracked incident is already resolved when the bot starts,
            # update its existing messages once, then clean it up.
            if status == "resolved":
                startup_success = True

                for guild_id, msg_id in list(tracked["messages"].items()):
                    try:
                        guild_config = configured_guilds.get(guild_id)

                        if not guild_config:
                            continue

                        channel = bot.get_channel(
                            int(guild_config["channel_id"])
                        )

                        if channel is None:
                            channel = await bot.fetch_channel(
                                int(guild_config["channel_id"])
                            )

                        msg = await channel.fetch_message(int(msg_id))

                        await msg.edit(
                            view=StatusView(
                                incident["name"],
                                timeline,
                                incident["shortlink"]
                            )
                        )

                    except Exception as e:
                        startup_success = False
                        print(
                            f"Failed to update resolved incident on startup "
                            f"for guild {guild_id}: {e}"
                        )

                if startup_success:
                    del tracked_incidents[incident_id]
                    save_data()

                continue

            tracked["last_update_id"] = newest["id"]
            save_data()
            continue

        if (
            tracked.get("last_update_id") != newest["id"]
            or status == "resolved"
        ):
            update_success = True

            for guild_id, guild_config in configured_guilds.items():
                try:
                    channel = bot.get_channel(
                        int(guild_config["channel_id"])
                    )

                    if channel is None:
                        channel = await bot.fetch_channel(
                            int(guild_config["channel_id"])
                        )

                    msg_id = tracked["messages"].get(guild_id)

                    if msg_id:
                        msg = await channel.fetch_message(int(msg_id))

                        await msg.edit(
                            view=StatusView(
                                incident["name"],
                                timeline,
                                incident["shortlink"]
                            )
                        )
                    else:
                        # No message exists for this server yet.
                        # This can happen if the server was configured
                        # after the incident started.
                        msg = await channel.send(
                            view=StatusView(
                                incident["name"],
                                timeline,
                                incident["shortlink"]
                            )
                        )

                        tracked["messages"][guild_id] = msg.id

                except Exception as e:
                    update_success = False
                    print(
                        f"Failed to update incident for guild "
                        f"{guild_id}: {e}"
                    )

            tracked["last_update_id"] = newest["id"]
            save_data()

            # Only remove the incident after every configured server was
            # successfully updated. This prevents a failed server update
            # from permanently losing the incident from tracking.
            if status == "resolved" and update_success:
                del tracked_incidents[incident_id]
                save_data()

    first_run = False

# ---- START BOT ----

bot.run(TOKEN)
