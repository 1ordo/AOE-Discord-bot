import discord
from datetime import timezone, datetime as dt1,timedelta
from database import database #database.py
import datetime
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

        embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
    return embed 



@client.event
async def on_voice_state_update(member, before, after):
    guild_id = member.guild.id
    guild = client.get_guild(guild_id)
    # Member joined a voice channel
    if before.channel is None and after.channel is not None:
        channel_id = database.log_retrieve(guild_id, "member_joined_vc")
        if channel_id:
            embed = create_embed(f"{member.mention} joined {after.channel.name}.", member, discord.Color.green(),client)
            await member.guild.get_channel(channel_id).send(embed=embed)
    
   # Member left a voice channel
    elif before.channel is not None and after.channel is None:
        check = False
        channel_id = database.log_retrieve(guild_id, "member_left_vc")
        guild = client.get_guild(guild_id)
        if channel_id:
            check = True
            embed = create_embed(f"{member.mention} left {before.channel.name}.", member, discord.Color.red(),client)
            
        
        # Check if the member was disconnected by an admin
        async for entry in member.guild.audit_logs(action=discord.AuditLogAction.member_update, limit=5):
            if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 60:
                # Member was disconnected by an admin
                check = True
                disconnector = entry.user
                channel_id = database.log_retrieve(guild_id, "member_disconnected_vc")
                if channel_id:
                    embed = create_embed(f"{member.mention} was disconnected by {disconnector.mention}.", member, discord.Color.red(),client)
                break
        if check:
            await member.guild.get_channel(channel_id).send(embed=embed)   
             
    # Member moved to another voice channel
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        channel_id = database.log_retrieve(guild_id, "member_move_vc")
        if channel_id:
            embed = create_embed(f"{member.mention} moved from {before.channel.name} to {after.channel.name}.", member, discord.Color.blue(),client)
            await member.guild.get_channel(channel_id).send(embed=embed)
    
    # Member switched between different states in the same voice channel (e.g., muted, deafened)
    if before.mute != after.mute or before.deaf != after.deaf:
        channel_id = database.log_retrieve(guild_id, "member_mute_deaf")
        if channel_id:
            states = []
            if before.mute != after.mute:
                states.append("server muted" if after.mute else "server unmuted")
            if before.deaf != after.deaf:
                states.append("server deafened" if after.deaf else "server undeafened")
            embed = create_embed(f"{member.mention} was {' and '.join(states)} in {after.channel.name}.", member, discord.Color.orange(),client)
            await member.guild.get_channel(channel_id).send(embed=embed)
    
                        
#problem is not here man 
                    