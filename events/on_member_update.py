from discord import Member
import discord
from client import client
import logging
from discord.ext import commands
from discord_webhook import DiscordWebhook
from io import BytesIO
from database import database
from datetime import timezone, datetime as dt1,timedelta
from langdetect import detect
import datetime
import pytz





logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@client.event
async def on_member_update(before: Member, after: Member):
    guild = after.guild

    before_roles = set(before.roles)
    after_roles = set(after.roles)

    linked_roles = database.get_linked_roles_by_guild(guild.id)
    if linked_roles:
        for entry in linked_roles:
            role_id, target_role_id, role_link_id = entry[2], int(entry[3]), entry[4]

            source_role = guild.get_role(role_id)
            target_role = guild.get_role(target_role_id)

            if not source_role or not target_role:
                continue


            if source_role not in before_roles and source_role in after_roles:
                
                required_roles = [
                    guild.get_role(entry[2]) 
                    for entry in linked_roles 
                    if entry[4] == role_link_id
                ]

                if all(role in after_roles for role in required_roles):
                    if target_role not in after_roles:  
                        await after.add_roles(target_role)
                        logger.info(f"You have been given the {target_role.name} role!")

            elif source_role in before_roles and source_role not in after_roles:
                required_roles = [
                    guild.get_role(entry[2]) 
                    for entry in linked_roles 
                    if entry[4] == role_link_id
                ]

                if any(role not in after_roles for role in required_roles):
                    if target_role in after_roles:
                        await after.remove_roles(target_role)
                        logger.info(f"The {target_role.name} role has been removed because you no longer meet the requirements.")

    if before.timed_out_until != after.timed_out_until:
        # Member was timed out or the timeout was removed
        guild = before.guild
        channel_id = database.log_retrieve(guild.id, "member_timeout")
        if channel_id:
            timezone = pytz.timezone("America/Chicago")

            # Create embed for timeout events
            if after.timed_out_until:
                # Convert timed_out_until to server's time zone
                timeout_end_utc = after.timed_out_until
                timeout_end_server_tz = timeout_end_utc.astimezone(timezone)
                
                embed = discord.Embed(
                    description=f"✅ {after.mention} was timed out until {timeout_end_server_tz.strftime('%m/%d/%Y %I:%M %p')} ({timeout_end_server_tz.strftime('%Z')})",
                    color=discord.Color.dark_grey()
                )
            else:
                embed = discord.Embed(
                    description=f"❌ {after.mention}'s timeout was removed.",
                    color=discord.Color.dark_grey()
                )
            
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.set_author(name=after.display_name, icon_url=after.display_avatar.url)

            # Get the current time in the server's timezone
            current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

            embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.display_avatar.url)
            await guild.get_channel(channel_id).send(embed=embed)
    if before.roles != after.roles:
        
        guild = before.guild
        channel_id = database.log_retrieve(guild.id, "member_role")
        if channel_id:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]
            
            added_roles_str = ", ".join([role.name for role in added_roles])
            removed_roles_str = ", ".join([role.name for role in removed_roles])
            
            embed = discord.Embed(
                description=f"Roles updated for {after.mention}",
                color=discord.Color.gold()
            )
            if added_roles:
                embed.add_field(name="✅ Added Roles", value=added_roles_str, inline=False)
            if removed_roles:
                embed.add_field(name="❌ Removed Roles", value=removed_roles_str, inline=False)
            
            await after.guild.get_channel(channel_id).send(embed=embed)
                    
            # Handle nickname changes
    if before.nick != after.nick:
        guild = before.guild
        channel_id = database.log_retrieve(guild.id,"member_nickname")
        if after.nick:
            embed = discord.Embed(
                description=f"{before.mention} changed their nickname to {after.nick}.(Was {before.nick})",
                color=discord.Color.purple()
            )
        else:
            embed = discord.Embed(
                description=f"{before.mention} removed their nickname.",
                color=discord.Color.purple()
            )
        embed.set_author(name=before.display_name, icon_url=after.display_avatar.url)
        timezone = pytz.timezone("America/Chicago")

        # Get the current time in the server's timezone
        current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

        embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
        if guild:
            await guild.get_channel(channel_id).send(embed=embed)