import discord
from discord.ext import tasks
from client import client
import pytz
import psutil
import os
from collections import defaultdict
from datetime import datetime, timedelta
from database import database
import re
# In-memory error tracking
error_counts = defaultdict(int)

# In-memory error tracking
error_counts = defaultdict(int)
import deepl
DEEPL_API_KEY = os.getenv('DEEPL_TOKEN')


def count_errors_last_24_hours():
    # Error count is tracked in memory so this function just returns the count
    return sum(error_counts.values())

def get_system_stats():
    # Memory usage
    memory_info = psutil.virtual_memory()
    memory_usage = memory_info.percent

    # CPU usage
    cpu_usage = psutil.cpu_percent(interval=1)  # Takes 1 second to measure CPU usage

    return memory_usage, cpu_usage

async def get_stats():
    # Get guild and member count
    guilds_count = len(client.guilds)
    members_count = sum(guild.member_count for guild in client.guilds)
    

    bot_ping = client.latency * 1000 
    

    database_ping = database.ping_database()

    
    return guilds_count, members_count, bot_ping, database_ping


class ControlPanelView(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=None)  # No timeout for buttons
        self.embeds = embeds
        self.current_page = 0

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_page < len(self.embeds) - 1:
            self.current_page += 1
            await interaction.response.edit_message(embed=self.embeds[self.current_page])

@tasks.loop(minutes=5)
async def update_control_panel():
    test_channel_id = 1289162066485186661
    channel_id = 1289160117832650774 
    channel = client.get_channel(channel_id)

    if channel:
        guilds_count, members_count, bot_ping, database_ping = await get_stats()
        memory_usage, cpu_usage = get_system_stats()
        error_count = count_errors_last_24_hours()
        
        # Bot Statistics Embed
        embed_bot_stats = discord.Embed(
            title="Bot Control Panel",
            description="Here’s the latest information about the bot and server.\nUpdates each 5 minutes.",
            color=discord.Color.green()
        )
        translator = deepl.Translator(DEEPL_API_KEY)
        deepl_usage = translator.get_usage()
        embed_bot_stats.add_field(name="Total Guilds", value=f"`{str(guilds_count)}`")
        embed_bot_stats.add_field(name="Total Members", value=f"`{str(members_count)}`")
        embed_bot_stats.add_field(name="Bot Ping", value=f"`{bot_ping:.2f} ms`", inline=False)
        embed_bot_stats.add_field(name="Database Ping", value=f"`{database_ping}`", inline=False)
        embed_bot_stats.add_field(name="Memory Usage", value=f"`{memory_usage}% used`")
        embed_bot_stats.add_field(name="CPU Usage", value=f"`{cpu_usage}%`")
        embed_bot_stats.add_field(name="Errors", value=f"`{str(error_count)}`", inline=False)
        embed_bot_stats.add_field(name="DeepL Usage", value=f"`{extract_usage_info(str(deepl_usage))}`", inline=True)

        timezone = pytz.timezone("America/Chicago")
        embed_bot_stats.set_footer(text=f"Winston - {datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')}",
                                   icon_url=client.user.avatar.url)
        
        # Get role statistics
        guild = channel.guild
        roles = guild.roles[1:]
        roles = sorted(roles, key=lambda r: len(r.members), reverse=True) 
        
        embeds = [embed_bot_stats]  

        for i in range(0, len(roles), 15):
            embed_roles_stats = discord.Embed(
                title="Role Statistics",
                description="Roles and their member counts",
                color=discord.Color.blue()
            )
            batch_roles = roles[i:i + 15]
            for role in batch_roles:
                embed_roles_stats.add_field(name=role.name, value=f"`{len(role.members)} members`", inline=False)

            embeds.append(embed_roles_stats)
        message_id = 1289301900432507043
        test_message_id = 1289162401329188910
        # Fetch the message and update with pagination
        message = await channel.fetch_message(message_id)
        if message:
            view = ControlPanelView(embeds)
            await message.edit(embed=embed_bot_stats, view=view)


def extract_usage_info(usage_string):

    match = re.search(r"Characters:\s(\d+)\s+of\s+(\d+)", usage_string)
    
    if match:
        used_characters = int(match.group(1)) 
        total_characters = int(match.group(2))  

        # Calculate percentage of usage
        percentage_used = (used_characters / total_characters) * 100
        
        # Calculate remaining characters
        remaining_characters = total_characters - used_characters
        
        # Prepare detailed report
        detailed_info = (
            f"Usage this billing period:\n"
            f"Characters used: {used_characters:,} of {total_characters:,}\n" 
            f"Percentage used: {percentage_used:.2f}%\n"  
            f"Characters remaining: {remaining_characters:,}"
        )
        
        return detailed_info
    else:
        return "Invalid usage string format."

# Example usage string


