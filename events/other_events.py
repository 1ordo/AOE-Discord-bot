import discord
from datetime import timezone, datetime as dt1,timedelta
from langdetect import detect
from database import database #database.py
import datetime
import pytz
from client import client

#@client.event
#async def on_guild_remove(guild):
#    guild_id = guild.id
#    database.delete_guild_data(guild_id)

@client.event
async def on_invite_create(invite:discord.Invite):
    guild_id = invite.guild.id
    channel_id = database.log_retrieve(guild_id, "server_invite")
    try:
        if channel_id:
            # Fallback values
            inviter_name = invite.inviter.display_name if invite.inviter.display_name else invite.inviter.name
            inviter_avatar_url = invite.inviter.display_avatar.url if invite.inviter.display_avatar else None

            embed = discord.Embed(
                description=f"Invite link `{invite.code}` created.",
                color=discord.Color.blue()
            )
            
            # Set the author field with a fallback for missing avatar
            if inviter_avatar_url:
                embed.set_author(name=inviter_name, icon_url=inviter_avatar_url)
            else:
                embed.set_author(name=inviter_name)

            # Add more fields or customize the embed as needed
            await invite.guild.get_channel(channel_id).send(embed=embed)
    except:
        pass

        


@client.event
async def on_member_ban(guild, user):
    try:
        # Retrieve the channel ID for logging
        channel_id = database.log_retrieve(guild.id, "member_ban")
        if channel_id:
            # Fallback values
            user_name = user.display_name if hasattr(user, 'display_name') else user.name
            user_avatar_url = user.display_avatar.url

            # Retrieve the server's timezone
            
            # Create the embed
            embed = discord.Embed(
                description=f"{user.mention} was banned from the server.",
                color=discord.Color.dark_red()
            )
            
            if user_avatar_url:
                embed.set_thumbnail(url=user_avatar_url)
                embed.set_author(name=user_name, icon_url=user_avatar_url)
            else:
                embed.set_author(name=user_name)
                
                
            timezone = pytz.timezone("America/Chicago")
            # Get the current time in the server's timezone
            current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

            embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
            await guild.get_channel(channel_id).send(embed=embed)
    except:
        pass

@client.event
async def on_member_unban(guild, user):
    try:
        channel_id = database.log_retrieve(guild.id, "member_ban")
        if channel_id:
            # Fallback values
            user_name = user.display_name if hasattr(user, 'display_name') else user.name
            user_avatar_url = user.display_avatar.url
            
            embed = discord.Embed(
                description=f"{user.mention} was unbanned from the server.",
                color=discord.Color.green()
            )
            
            if user_avatar_url:
                embed.set_thumbnail(url=user_avatar_url)
                embed.set_author(name=user_name, icon_url=user_avatar_url)
            else:
                embed.set_author(name=user_name)
            timezone = pytz.timezone("America/Chicago")

            # Get the current time in the server's timezone
            current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

            embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
            await guild.get_channel(channel_id).send(embed=embed)
    except:
        pass
        
        

        
        
        
def create_embed(description, member, color, client):
    embed = discord.Embed(
        description=description,
        color=color
    )
    # Fallback values
    
    if hasattr(member, 'display_avatar'):
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    
    timezone = pytz.timezone("America/Chicago")

    # Get the current time in the server's timezone
    current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

    embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
    return embed



    
@client.event
async def on_guild_channel_create(channel):
    try:
        guild_id = channel.guild.id
        channel_id = database.log_retrieve(guild_id, "channel_created")
        if channel_id:
            embed = create_embed(f"Channel {channel.mention} created.", channel, discord.Color.green(),client)
            await channel.guild.get_channel(channel_id).send(embed=embed)
    except:
        pass

@client.event
async def on_guild_channel_delete(channel):
    try:
        guild_id = channel.guild.id
        channel_id = database.log_retrieve(guild_id, "channel_deleted")

        if channel_id:
            embed = create_embed(f"Channel {channel.name} deleted.", channel, discord.Color.red(),client)
            await channel.guild.get_channel(channel_id).send(embed=embed)
    except:
        pass


    

@client.event
async def on_thread_delete(thread):
    try:
        guild_id = thread.guild.id
        channel_id = database.log_retrieve(guild_id, "thread_deleted")
        if channel_id:
            embed = create_embed(f"Thread {thread.name} deleted.", thread, discord.Color.red(),client)
            await thread.guild.get_channel(channel_id).send(embed=embed)
    except:
        pass

@client.event
async def on_guild_role_create(role):
    try:
        guild_id = role.guild.id
        channel_id = database.log_retrieve(guild_id, "role_created")
        if channel_id:
            embed = create_embed(f"Role {role.name} created.", role, discord.Color.green(),client)
            await role.guild.get_channel(channel_id).send(embed=embed)
    except:
        pass

@client.event
async def on_guild_role_delete(role):
    try:
        guild_id = role.guild.id
        channel_id = database.log_retrieve(guild_id, "role_delete")
        if channel_id:
            embed = create_embed(f"Role {role.name} deleted.", role, discord.Color.red(),client)
            await role.guild.get_channel(channel_id).send(embed=embed)
    except:
        pass
    



