import discord
from datetime import timezone, datetime as dt1,timedelta
from discord import app_commands, Intents, Client, Interaction, Emoji, PartialEmoji
import typing
from database import database #database.py
from dotenv import load_dotenv
from resources.resources import resources
from resources.error_handler import has_permissions , MissingPermissions
resource = resources()
import aiohttp
import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import dotenv

dotenv.load_dotenv()

log_types = {
        "memberlogs": [
            "member_ban", "member_timeout", "member_kick", "member_join_server",
            "member_left_server", "member_nickname", "member_unbanned",
        ],
        "channel_log": [
            "channel_created", "channel_deleted", "channel_updated", "thread_created", "thread_deleted", "channel_perm_update"
        ],
        "voice_chat_log": [
            "member_joined_vc", "member_left_vc", "member_move_vc",
            "member_switch_vc", "member_disconnected_vc", "member_mute_deaf"
        ],
        "server_invite": [
            "invites","server_invite"
        ],
        "role_log": [
            "role_created", "role_give", "role_delete", "role_update","member_role"
        ],
        "message_log": [
            "message_delete", "message_edit"
        ]
    }




SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', "resources/credentials.json")
SPREADSHEET_ID = os.getenv('WELCOME_SPREADSHEET_ID')
WORKSHEET_NAME = os.getenv('WELCOME_WORKSHEET_NAME', "Welcoming")


USED_WELCOME_FILE = "used_welcoming.json"

def load_used_welcome():
    try:
        with open(USED_WELCOME_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_used_welcome(used_quotes):
    with open(USED_WELCOME_FILE, 'w') as file:
        json.dump(used_quotes, file)



def init_gspread():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    except Exception as e:
        print(f"Error initializing Google Sheets client: {e}")
        raise

def get_random_quote():
    sheet = init_gspread()
    quotes = sheet.col_values(1) 
    used_welcome = load_used_welcome()


    unused_welcomes = [quote for quote in quotes if quote not in used_welcome]
    
    if not unused_welcomes:
        used_welcome.clear()
        save_used_welcome(used_welcome)
        unused_welcomes = quotes

    quote = random.choice(unused_welcomes)
    
    used_welcome.append(quote)
    save_used_welcome(used_welcome)
    
    return quote






server_group = app_commands.Group(name="server", description="server default commands!",guild_only=True)

@server_group.command(name="testwelcome", description="Test join")
@has_permissions(manage_guild=True)
async def testjoin(interaction: Interaction):
    await interaction.response.defer()
    client = interaction.client
    guild_id = interaction.guild.id
    
    # Retrieve default settings from the database
    defaults = database.check_defaults(guild_id)
    if defaults:
        guild_id, welcome_id, welcome_message, ai_category_id, ai_channel_id = defaults
    else:
        await interaction.response.send_message("You didn't set defaults yet.")
        return
    
    # Fallback values for welcome message
    username = interaction.user.display_name
    if not welcome_message:
        welcome_message = get_random_quote()
        welcome_message = welcome_message.replace("{username}", username)  
    # Handle avatar URL
    avatar_url = interaction.user.display_avatar.url

    try:
        # Retrieve image from local folder
        image_path = os.path.join('welcome_images', f'{guild_id}.png')
        
        if os.path.exists(image_path):
            with open(image_path, 'rb') as image_file:
                image_bytes = image_file.read()
            
            # Generate welcome image
            generated_image = resources.generate_image(guild_id, welcome_message, avatar_url,interaction.user.id)
            

            
            # Inform user that the message is being sent
            await interaction.followup.send("Message is being sent in the welcome channel!")
            
            # Send the image to the welcome channel
            selected_channel = client.get_channel(welcome_id)
            if selected_channel:
                await selected_channel.send(file=discord.File(generated_image, filename='welcome.png'))
                if os.path.exists(generated_image):
                    os.remove(generated_image)
            else:
                await interaction.followup.send(f"Could not find the welcome channel with ID: {welcome_id}")
        else:
            await interaction.followup.send("No welcome image set for this server. Please configure one using `/welcome_configuration`.")
    except Exception as e:
        await interaction.followup.send(f"An unexpected error occurred: {e}")


@server_group.command(name="welcome_configuration", description="Welcome your members with a great message!")
@app_commands.describe(channel="The welcome channel",welcome_message ="the message you want your members to be greeted with!",image_link = "the image link you want (upload it to discord and copy link)")
@has_permissions(manage_guild=True)
async def welcomeconfiguration(interaction: Interaction, channel:typing.Optional[discord.TextChannel] = None , welcome_message:typing.Optional[str] = None,image_link:typing.Optional[str] = None):
    await interaction.response.defer()
    welcome_image = None
    channel,welcome_message,image_link
    guild_id = None 
    welcome_id = channel.id if channel else None
    welcome_message = None
    guild_id = interaction.guild.id
    defaults = database.check_defaults(guild_id)
    
    if channel or welcome_message:    
        database.update_defaults(guild_id=guild_id, welcome_message=welcome_message, welcome_id=channel.id) 
    if image_link:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_link) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        
                        # Ensure the "welcome_images" folder exists
                        if not os.path.exists('welcome_images'):
                            os.makedirs('welcome_images')
                        
                        # Save the image with the guild ID as the filename
                        image_path = os.path.join('welcome_images', f'{guild_id}.png')
                        with open(image_path, 'wb') as f:
                            f.write(image_data)
                        
        except Exception as e:
            print(f"An error occurred while downloading the image: {e}")


        
    if defaults:
        guild_id, welcome_id, welcome_message, ai_category_id, Ai_channel_id = defaults   
        
    if not welcome_message:
        welcome_message = "Hi {username}, welcome to the server!'\n"     
        
    welcome_channel = f"<#{welcome_id}>" if welcome_id else '**not set**'
    welcome_message_status = welcome_message
    image_path = os.path.join('welcome_images', f'{guild_id}.png')
    if os.path.exists(image_path):
        welcome_image = f"Image saved locally as '{guild_id}.png'"
    else:
        welcome_image = "not set"
    embed = discord.Embed(
        title="Welcome Configuration",
        description="To configure the welcome settings for your server, follow these steps:",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="1. Set Welcome Channel",
        value="Provide the channel where you want new members to be welcomed.\n"
              "`channel` to set the welcome channel.",
        inline=False      
    )
    embed.add_field(
        name="2. Upload Welcome Image",
        value="Upload an image to be displayed along with the welcome message.\n",
        inline=False       
    )
    embed.add_field(
        name="3. Set Welcome Message",
        value="Customize the welcome message. By default, it's 'Hi {username}, welcome to the server!'\n"
              "You can also use this command to set your desired welcome message by setting 'welcome_message'.",
        inline=False       
    )
    embed.add_field(
        name="Testing Welcome Message",
        value="To test the welcome functionality, use the command `/testwelcome`.",
        inline=False 
    )
    embed.add_field(
        name="Current Configuration Status",
        value=f"**Welcome Channel:** {welcome_channel}\n"
              f"**Welcome Message:** {welcome_message_status}\n"
              f"**Welcome Image:** *{welcome_image}*",
        inline=False        
    )
    embed.set_footer(text=f"Server ID: {guild_id}")

    await interaction.followup.send(embed=embed)
    
YES_NO_CHOICES = [
    app_commands.Choice(name="Yes", value="yes"),
    app_commands.Choice(name="No", value="no")
]

@server_group.command(name="logs", description="Sets up logs! Just write it without additions to start!")
@has_permissions(manage_guild=True)
@app_commands.describe(
    member_logs="Enable or disable member logs",
    channel_log="Enable or disable channel logs",
    voice_chat_log="Enable or disable voice chat logs",
    server_invite="Enable or disable server invite logs",
    role_log="Enable or disable role logs",
    message_log="Enable or disable message logs"
)
@app_commands.choices(
    member_logs=YES_NO_CHOICES,
    channel_log=YES_NO_CHOICES,
    voice_chat_log=YES_NO_CHOICES,
    server_invite=YES_NO_CHOICES,
    role_log=YES_NO_CHOICES,
    message_log=YES_NO_CHOICES
)
async def logs(
    interaction: discord.Interaction, 
    member_logs: typing.Optional[str] = None, 
    channel_log: typing.Optional[str] = None, 
    voice_chat_log: typing.Optional[str] = None, 
    server_invite: typing.Optional[str] = None, 
    role_log: typing.Optional[str] = None, 
    message_log: typing.Optional[str] = None
):


    logs_select = {
        "memberlogs": member_logs,
        "channel_log": channel_log,
        "voice_chat_log": voice_chat_log,
        "server_invite": server_invite,
        "role_log": role_log,
        "message_log": message_log
    }
    
    if any(logs_select.values()):
        try:
            guild_id = interaction.guild.id
            channel_id = interaction.channel.id
            for log_type, log_value in logs_select.items():
                if log_value is not None:
                    columns = log_types.get(log_type, [])
                    if log_value.lower() == "yes":
                        # Update columns in the database to channel_id
                        for column in columns:
                            database.log_update(guild_id, column, channel_id)
                    elif log_value.lower() == "no":
                        # Update columns in the database to None
                        for column in columns:
                            database.log_update(guild_id, column, None)
            
            await interaction.response.send_message("Selected logs have been updated successfully to this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
    else:
        result = discord.Embed(
            title="Logs",
            colour=discord.Color.blurple(),
            description=(
                "Setting up logs will help you keep track of various activities and events within your server. "
                "It's quick and easy, and you'll have comprehensive oversight of your server's activity in no time!"
            )
        )
        result.add_field(name="How Can It Help Me? :question:", value=(
                "Logs can help you track various events in your server, providing valuable insights and moderation capabilities. "
                "Here is what each log type does:\n\n"
                "**Member Logs: 👤** Tracks member-related activities like bans, timeouts, kicks, joins, leaves, nickname changes, and unbans.\n"
                "**Channel Logs: 📝** Monitors channel activities such as creations, deletions, and updates.\n"
                "**Voice Chat Logs: 🎤** Keeps track of activities in voice channels, including joins, leaves, moves, switches, disconnects, and mutes/deafens.\n"
                "**Server Invites: 💌** Logs information related to server invites.\n"
                "**Role Logs: 🛡️** Tracks role-related changes such as creations, deletions, updates, and assignments.\n"
                "**Message Logs: 📬** Monitors message-related activities including deletions and edits."
            ))
        result.add_field(name="Logs Setup :tools:", value=(
                "Here you can set up your logs!\n"
                "It's really simple:\n"
                "1. Go to the channel where you want to send the logs.\n"
                "2. Use the following options to enable or disable logs:\n"
                "   - **Member Logs: 👤** Type 'yes' to enable or 'no' to disable.\n"
                "   - **Channel Logs: 📝** Type 'yes' to enable or 'no' to disable.\n"
                "   - **Voice Chat Logs: 🎤** Type 'yes' to enable or 'no' to disable.\n"
                "   - **Server Invites: 💌** Type 'yes' to enable or 'no' to disable.\n"
                "   - **Role Logs: 🛡️** Type 'yes' to enable or 'no' to disable.\n"
                "   - **Message Logs: 📬** Type 'yes' to enable or 'no' to disable.\n"
                "Example: `/logs member_logs:yes channel_logs:no voice_chat_logs:yes`"
            ))
        await interaction.response.send_message(embed=result)







def get_server_group():
    return server_group