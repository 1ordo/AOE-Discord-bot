import discord
from datetime import timezone, datetime as dt1,timedelta
from langdetect import detect
from database import database #database.py
import datetime
import pytz
from client import client

@client.event
async def on_raw_member_remove(payload):
    try:
        guild_id = payload.guild_id
        user = payload.user
        guild = client.get_guild(guild_id)
        
        if not guild:
            return
        display_name = user.display_name if hasattr(user, 'display_name') else user.name
        
        avatar_url = user.display_avatar.url
            
        async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
            if entry.target.id == user.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 60:
                kicker = entry.user
                channel_id = database.log_retrieve(guild.id, "member_kick")
                if channel_id:
                    embed = discord.Embed(
                        description=f"{user.mention} got kicked by {kicker.mention}",
                        color=discord.Color.red()
                    )
                    embed.set_thumbnail(url=user.display_avatar.url)
                    embed.set_author(name=display_name, icon_url=user.display_avatar.url)
                    timezone = pytz.timezone("America/Chicago")

                    # Get the current time in the server's timezone
                    current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

                    embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
                    await guild.get_channel(channel_id).send(embed=embed)
                return
            else:
                channel_id = database.log_retrieve(guild.id, "member_left_server")
                if channel_id:
                    embed = discord.Embed(
                        description=f"{user.mention} left the server.",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=avatar_url)
                    embed.set_author(name=display_name, icon_url=avatar_url)
                    timezone = pytz.timezone("America/Chicago")

                    # Get the current time in the server's timezone
                    current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

                    embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
                    await guild.get_channel(channel_id).send(embed=embed)
    except Exception as e:
        print(e)
