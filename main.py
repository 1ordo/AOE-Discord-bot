import discord
from discord.ext import commands, tasks
from client import client
from discord import app_commands, Interaction, Embed, Color, utils, File
import typing
from events import on_thread_create , on_member_update , other_events , on_guild_channel_update , on_guild_role_update ,on_message, on_member_join , on_message_delete , on_message_edit , on_raw_member_remove , on_voice_state_update,on_raw_reaction_add
import commands.language_translate, commands.thread_translate
import commands.role_all_linked
from resources.translation_functions import send_to_threads_with_webhooks
import commands.role_link
import commands.poll_commands
import commands.translate_with_roles
import commands.translate_with_emojii
from discord import app_commands, Client, Interaction
from discord.ui import  View, Button, Select, Modal
import inspect
import asyncio
import os
import typing
import re
from dotenv import load_dotenv
import logging
from database import database
from commands.poll_commands import update_poll_messages
logger = logging.getLogger(__name__)
from commands import daily_quote
from resources.Client_control_panel import update_control_panel
from commands.AI_Commands import ai_start_chat_callback
import dotenv


@client.event
async def on_ready():
    await client.tree.sync()
    #await client.change_presence(activity=discord.Activity(type=discord.ActivityType., name=""))
    if not client.user:
        raise RuntimeError("on_ready() somehow got called before Client.user was set!")
    print(inspect.cleandoc(f"""
        Logged in as {client.user} (ID: {client.user.id})
    """), end="\n\n")
    print("loading cache...")
    await database.load_cache()
    update_control_panel.start()
    print("cahce loaded!")
    update_poll_messages.start()
    daily_quote.scheduler.start()
    print("----------------------------------------------------------------------------------------")


        


@client.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == client.user.id:
        return

    guild = client.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    if channel:
        message = await channel.fetch_message(payload.message_id)
        user = guild.get_member(payload.user_id)
        
        poll_info = database.get_poll_by_message_id(guild.id, channel.id, message.id)
        if not poll_info:
            return

        emoji_to_option = {
            "1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4,
            "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8, "🔟": 9
        }
        # Check if the emoji is in the poll options
        if str(payload.emoji) in emoji_to_option:
            poll_id = poll_info[4]
            option_index = emoji_to_option[str(payload.emoji)]

            # Decrement vote in the database
            database.decrement_vote(poll_id, option_index)
            
            
@client.event
async def on_interaction(interaction: discord.Interaction):
    # Ensure this is a button interaction
    if interaction.type == discord.InteractionType.component:
        # Check if the interaction is a button click
        if interaction.data['component_type'] == 2:  # 2 corresponds to Button
            # Check if the custom_id matches
            if interaction.data['custom_id'] == "start_chat_button":
                await ai_start_chat_callback(interaction)


BOT_TOKEN = os.getenv('BOT_TOKEN')

dotenv.load_dotenv()
loop = asyncio.get_event_loop()
loop.create_task(client.start(BOT_TOKEN))
loop.run_forever()

    
    





