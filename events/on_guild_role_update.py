
import discord
import datetime
from datetime import timezone, datetime as dt1,timedelta
from langdetect import detect
from discord.ui import  View, Button, Select, Modal
from database import database #database.py
from dotenv import load_dotenv
import pytz
from client import client



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

    embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.display_avatar.url)
    return embed 





@client.event
async def on_guild_role_update(before, after):
    guild_id = before.guild.id
    channel_id = database.log_retrieve(guild_id, "role_update")
    if channel_id:
        embed = create_embed(f"Role {before.name} updated.", after, discord.Color.gold(),client)
        
        changes = []
        if before.name != after.name:
            changes.append(f"Name: {before.name} ➡️ {after.name}")
        
        before_perms = format_permissions(before.permissions)
        after_perms = format_permissions(after.permissions)

        before_changes = []
        after_changes = []
        for perm, value in after_perms.items():
            if before_perms.get(perm) != value:
                before_changes.append(f"{perm}: {before_perms.get(perm)}")
                after_changes.append(f"{perm}: {value}")

        if before_changes and after_changes:
            embed.add_field(name="Before Permissions", value="\n".join(before_changes), inline=False)
            embed.add_field(name="After Permissions", value="\n".join(after_changes), inline=False)

        if changes:
            embed.add_field(name="Changes", value="\n".join(changes), inline=False)

            await before.guild.get_channel(channel_id).send(embed=embed)
   

def format_permissions(permissions):
    perms = {}
    for perm, value in permissions:
        try:
            perm_name = str(perm).split('.')[1]  # Attempt to split and get the permission name
            perms[perm_name] = value
        except IndexError:
            # Handle the case where the permission format is unexpected
            perms[str(perm)] = value  # Store the permission as-is
    return perms