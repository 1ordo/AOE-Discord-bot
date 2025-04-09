import discord
from datetime import timezone, datetime as dt1, timedelta
from langdetect import detect
from pathlib import Path
from database import database  # database.py
from dotenv import load_dotenv
from client import client



@client.event
async def on_message_edit(before, after):
    if before.guild and after.guild:  
        if not before.author.bot and before.content != after.content:
            guild_id = before.guild.id
            channel_id = database.log_retrieve(guild_id, "message_edit")
            if channel_id:
                embed = discord.Embed(
                    description=f"Message edited in #{before.channel.mention} by {before.author.mention}",
                    color=discord.Color.gold()
                )

                # Handle edited content
                before_content = before.content if before.content else "No content"
                after_content = after.content if after.content else "No content"

                # Check if the before and after content are too long
                if len(before_content) > 1024:
                    before_content = before_content[:1021] + "..."
                if len(after_content) > 1024:
                    after_content = after_content[:1021] + "..."
                
                # Add before and after content to embed
                embed.add_field(name="Before", value=before_content, inline=False)
                embed.add_field(name="After", value=after_content, inline=False)

                # Handle attachments (image/gif)
                if before.attachments or after.attachments:
                    attachments_before = "\n".join([attachment.url for attachment in before.attachments]) if before.attachments else "No attachments"
                    attachments_after = "\n".join([attachment.url for attachment in after.attachments]) if after.attachments else "No attachments"
                    
                    # Check if the attachments have changed
                    if attachments_before != attachments_after:
                        embed.add_field(name="Attachments Before", value=attachments_before, inline=False)
                        embed.add_field(name="Attachments After", value=attachments_after, inline=False)
                
                # Send the embed message
                await before.guild.get_channel(channel_id).send(embed=embed)
