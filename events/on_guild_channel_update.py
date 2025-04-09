
from client import client
import discord
import datetime
from datetime import timezone, datetime as dt1,timedelta
from langdetect import detect
from discord.ui import  View, Button, Select, Modal
from database import database #database.py
from dotenv import load_dotenv
import pytz

def create_embed(description, member, color,client):
    embed = discord.Embed(
        description=description,
        color=color
    )
    
    if hasattr(member, 'display_avatar'):
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    
    timezone = pytz.timezone("America/Chicago")


    # Get the current time in the server's timezone
    current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

    embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
    return embed 


@client.event
async def on_guild_channel_update(before, after):
    guild_id = before.guild.id
    channel_id = database.log_retrieve(guild_id, "channel_updated")

    if channel_id:
        embed = create_embed(f"Channel {before.name} updated.", after, discord.Color.gold(),client)
        
        changes = []
        if hasattr(before, 'name') and before.name != after.name:
            changes.append(f"Name: {before.name} ➡️ {after.name}")
        if hasattr(before, 'category') and before.category != after.category:
            changes.append("Category updated")
        if hasattr(before, 'bitrate') and before.bitrate != after.bitrate:
            changes.append("Bitrate updated")
        if hasattr(before, 'user_limit') and before.user_limit != after.user_limit:
            changes.append("User limit updated")
        if hasattr(before, 'slowmode_delay') and before.slowmode_delay != after.slowmode_delay:
            changes.append("Slowmode delay updated")
        if hasattr(before, 'type') and before.type != after.type:
            changes.append("Type updated")
        
        if changes:
            embed.add_field(name="Changes", value="\n".join(changes), inline=False)

            await before.guild.get_channel(channel_id).send(embed=embed)

    # Check for permission overwrites update
    channel_id_perm = database.log_retrieve(guild_id, "channel_perm_update")
    if before.overwrites != after.overwrites and channel_id_perm:
        before_overwrites = {key: value for key, value in before.overwrites.items()}
        after_overwrites = {key: value for key, value in after.overwrites.items()}

        def format_overwrites(overwrites, compare_overwrites):
            perms = []
            for target, overwrite in overwrites.items():
                if target not in compare_overwrites or compare_overwrites[target] != overwrite:
                    perm_str = []
                    for perm, value in overwrite:
                        if value is True:
                            perm_str.append(f"{perm}: ✅")
                        elif value is False:
                            perm_str.append(f"{perm}: ❌")
                    perms.append(f"{target.name}: {'\n'.join(perm_str)}")
            return perms

        before_perms = format_overwrites(before_overwrites, after_overwrites)
        after_perms = format_overwrites(after_overwrites, before_overwrites)

        embed_perm = create_embed(f"Permissions updated for channel {before.name}.", before, discord.Color.gold(),client)
        if before_perms:
            embed_perm.add_field(name="Before Permissions", value="\n".join(before_perms), inline=False)
        if after_perms:
            embed_perm.add_field(name="After Permissions", value="\n".join(after_perms), inline=False)
        await before.guild.get_channel(channel_id_perm).send(embed=embed_perm)