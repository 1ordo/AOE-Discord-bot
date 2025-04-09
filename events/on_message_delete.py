import discord
from datetime import timezone, datetime as dt1,timedelta
from langdetect import detect
from pathlib import Path
from database import database #database.py
from dotenv import load_dotenv
import datetime
import pytz
from client import client

def create_embed(description, member, color, client, extra=None):
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
    
    if extra:
        embed.add_field(name="Additional Information", value=extra, inline=False)
    
    return embed



@client.event
async def on_message_delete(message):
    guild_id = message.guild.id if message.guild else None
    channel_id = database.log_retrieve(guild_id, "message_delete")
    
    if channel_id:
        # Handling attachments
        if message.attachments:
            attachment_urls = [attachment.url for attachment in message.attachments]
            attachment_info = "Attachments were deleted:\n" + "\n".join(attachment_urls)
        else:
            attachment_info = None
        
        # Prepare the base description
        description = f"Message deleted in #{message.channel.mention}: {message.content}"
        
        # Check if the description is too long for a single embed
        if len(description) > 2048:
            # Truncate the message content for the embed
            description = description[:2045] + "..."
            if attachment_info:
                description += "\n\n" + attachment_info
        else:
            # Append additional information
            if attachment_info:
                description += "\n\n" + attachment_info
        
        # Create and send the embed
        embed = create_embed(description, message.author, discord.Color.red(), client)
        await message.guild.get_channel(channel_id).send(embed=embed)