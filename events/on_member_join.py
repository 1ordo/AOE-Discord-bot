import discord
from datetime import timezone, datetime as dt1,timedelta
from langdetect import detect
from database import database #database.py
import datetime
from resources.resources import resources
resource = resources()
from io import BytesIO
from client import client
import os
from commands.server_commands import get_random_quote

@client.event
async def on_member_join(member: discord.Member):
    try: 
        guild_id = member.guild.id
        channel_id = database.log_retrieve(guild_id, "member_join_server")
        welcome_id = None
        welcome_message = "Hi {username}, welcome to the server!\n"
        invites_before = await member.guild.invites()
        
                
        if channel_id:
            embed = discord.Embed(
                description=f"{member.mention} Joined the Server!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
            embed.add_field(name="⏲Account Age", value=f"`{member.created_at.strftime("%b %d, %Y")}`\n **{get_account_age(member)}**", inline=False)

            embed.set_footer(text=f"Winston - {datetime.datetime.now().strftime("%m/%d/%Y %I:%M %p")}", icon_url=client.user.avatar.url)
            await member.guild.get_channel(channel_id).send(embed=embed)
    
        # Check if the member has an avatar
        avatar_url = member.display_avatar.url
        defaults = database.check_defaults(guild_id)
        if defaults:
            guild_id, welcome_id, welcome_message, ai_category_id, ai_channel_id = defaults
        else:
            return  # Exit if no defaults are set
        
        # Fallback values for welcome message
        username = member.display_name
        if not welcome_message:
            welcome_message = get_random_quote()  # Replace with your function to get a random quote
        welcome_message = welcome_message.replace("{username}", username)

        # Handle avatar URL
        avatar_url = member.display_avatar.url if member.display_avatar else member.default_avatar.url

        try:
            # Retrieve image from local folder
            image_path = os.path.join('welcome_images', f'{guild_id}.png')
            
            if os.path.exists(image_path):
                with open(image_path, 'rb') as image_file:
                    image_bytes = image_file.read()

                # Generate the welcome image
                generated_image_path = resources.generate_image(guild_id, welcome_message, avatar_url, member.id)
                
                # Send the welcome message and image to the designated channel
                selected_channel = client.get_channel(welcome_id)
                if selected_channel:
                    with open(generated_image_path, 'rb') as image_file:
                        image_bytes = image_file.read()
                    
                    sent_message = await selected_channel.send(file=discord.File(BytesIO(image_bytes), filename='welcome.png'), content=f"{member.mention}")
                    database.add_message_ignore(sent_message.guild.id,sent_message.id)
                    # Optionally remove the image if you saved it as a file
                    if os.path.exists(generated_image_path):
                        os.remove(generated_image_path)
                else:
                    print(f"Could not find the welcome channel with ID: {welcome_id}")
            else:
                print(f"No welcome image set for this server (Guild ID: {guild_id}). Please configure one.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
    except Exception as e:
        print(f"Error in on_member_join: {e}")
    

def get_account_age(member):
        age = datetime.datetime.now(datetime.UTC) - member.created_at
        years = age.days // 365
        months = (age.days % 365) // 30
        days = age.days % 30
        return f"{years} years, {months} months, {days} days"