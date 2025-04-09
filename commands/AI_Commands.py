import discord
from discord.ext import commands, tasks
import datetime
from datetime import timezone, datetime as dt1,timedelta
from collections import defaultdict
from discord import app_commands, Intents, Client, Interaction
import logging
from langdetect import detect
from discord.ui import  View, Button, Select, Modal
from pathlib import Path
import google.generativeai as genai
from database import database
from resources.resources import resources
from dotenv import load_dotenv
import asyncio
import os
import json
import typing
from resources.ai_functions import generate_single_response


ai_group = app_commands.Group(name="ai", description="AI Commands")
   
@ai_group.command(name="ask", description="Ask any quick question you want! (Beta, We use google Ai to answer your questions!)")
async def ask(interaction: Interaction, question: str):
    try:
        # Acknowledge the interaction immediately
        await interaction.response.defer()
        try:
            answer = await asyncio.wait_for(generate_single_response(question), timeout=30)  # Adjust timeout as needed
            await interaction.followup.send(content=(f"**{question}**" + f"\n \n {answer}"))
        except asyncio.TimeoutError:
            answer = "API response timed out.. Maybe your asking for really long answer?"
            await interaction.followup.send(answer)
        except discord.errors.HTTPException as e:  
            # Generate a unique filename based on user ID
            unique_filename = f"answer_{interaction.user.id}.txt"
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(unique_filename), exist_ok=True)
            # Create a text file
            with open(unique_filename, "w", encoding="utf-8") as file:
                file.write(answer)
            # Delete the local file after sending
            await interaction.followup.send(file=discord.File(unique_filename), ephemeral=True)
            # Remove the file after sending
            os.remove(unique_filename)
        logging.info(f"Someone used /ask to answer this question: {question}")
        
    except discord.errors.InteractionResponded:
        # This error occurs if the interaction has already been responded to before
        pass
    except Exception as e: 
        print(e)
        import traceback; traceback.print_exc();
        await interaction.followup.send("Something went wrong, this feature still in Beta.. \nPlease try with another question")



ai_start_chat_button = Button(style=discord.ButtonStyle.green, label="Start Chat", custom_id="start_chat_button")

async def ai_start_chat_callback(interaction: Interaction):
    guild_id = interaction.guild_id
    defaults = database.check_defaults(guild_id)
    user_id = interaction.user.id
    no_of_channels_limit = 1
    if defaults:
        guild_id, welcome_id, welcome_message, ai_category_id, Ai_channel_id = defaults
        
    selected_category = interaction.guild.get_channel(int(ai_category_id))
    
    def count_user_channels_in_category(user, category):
        user_channel_count = 1
        if user.guild_permissions.administrator:
            return 1
        for channel in category.channels:
            # Check if the user has permissions in this channel
            permissions = channel.permissions_for(user)
            if permissions.read_messages and permissions.send_messages:
                user_channel_count += 1 
        return user_channel_count
    no_of_channels = count_user_channels_in_category(interaction.user, selected_category)
    if int(no_of_channels) <= 2: #count index so its 2
        new_channel = await interaction.guild.create_text_channel(name=interaction.user.name,
                                                                category=selected_category)
        
        await new_channel.set_permissions(interaction.user,
                                        read_messages=True,
                                        send_messages=True)
        await new_channel.set_permissions(interaction.guild.default_role,
                                        read_messages=False, 
                                        send_messages=False)
        await interaction.response.send_message(f"your chat session created <#{new_channel.id}>", ephemeral=True)
        embed = discord.Embed(
        title='Welcome to the Chat Room!',
        description=f'Hi <@{user_id}> \n'
                    'Feel free to ask questions and chat with the bot here. '
                    'Please keep the conversation respectful and on-topic.\n\n'
                    'Once you are done chatting, type `/close` to close the channel.'
                    ,
        color=discord.Color.blue())
        embed.set_footer(text='Powered by Winston & Gemini!')
        await new_channel.send(embed=embed)
    else:
        await interaction.response.send_message("You have exeeded the number of channels per user (Max is 2)",ephemeral=True)
        


@ai_group.command(name="configuration", description="Configure AI channels for main server.")
async def aiconfiguration(interaction: Interaction, channel: typing.Optional[discord.TextChannel] = None, category: typing.Optional[discord.CategoryChannel] = None):
    guild = interaction.guild
    guild_id = interaction.guild.id
    ai_view = View()
    ai_view.add_item(ai_start_chat_button)
    ai_category_id = "Not set Yet"
    Ai_channel_id = "Not set Yet"
    # todo test later
    if not interaction.user.guild_permissions.manage_guild:
        await interaction.response.send_message("Only members with the 'Manage Server' permission can use this command.")
        return 
    if guild_id not in (1041900511244329010,1286288029379596329):
        await interaction.response.send_message("This feature is only available for our main server!")
        return
    
    if category != None  and channel != None:
        database.update_defaults(guild_id=guild_id,Ai_channel_id=channel.id, ai_category_id = category.id)

        
        embed = discord.Embed(
        title=" Start Chat with AI Bot 🌟",
        description="Click the button below to start a chat with the AI bot. This feature is exclusive to our main server!",
        color=discord.Color.blue())


        embed.add_field(
            name="How It Works",
            value="By clicking the button, you will initiate a conversation with the AI bot where you can ask questions and receive responses.")
        message = await channel.send(embed=embed, view=ai_view)
        
    elif category != None :
        database.update_defaults(guild_id=guild_id,ai_category_id = category.id)
        
    elif channel.id != None:
        database.update_defaults(guild_id=guild_id,Ai_channel_id=channel.id)
        
        
    defaults = database.check_defaults(guild_id)
    if defaults:
        guild_id, welcome_id, welcome_message, ai_category_id, Ai_channel_id = defaults
        
        
    ai_channel_msg = "Channel ID: <#{}>".format(Ai_channel_id) if Ai_channel_id else "Not set yet"
    ai_category_msg = "Category ID: <#{}>".format(ai_category_id) if ai_category_id else "Not set yet"

    
    # Prepare the embed explaining the feature
    embed = discord.Embed(
        title="Configure AI Channels (Main Server Only :star:)",
        description="Configure AI channels to interact with the AI bot.",
        color=discord.Color.gold()
    )
    embed.add_field(
        name="How It Works",
        value="This feature allows you to specify a text channel and a category where the AI bot will interact with users.\n"
              "To configure, use the command `/ai configuration`.\n"
              "If no channel are provided, This feature won't work!"
        ,inline=False          
    )
    
    embed.add_field(
        name="Default AI Channel",
        value=f"Channel ID: <#{Ai_channel_id}>",
        inline=False
    )
    embed.add_field(
        name="Default AI Category", #change later
        value=f"Category ID: <#{ai_category_id}>",
        inline=False
    )
    await interaction.response.send_message(embed=embed)

@ai_group.command(name="close", description="Close the current chat channel.")
async def close(interaction: Interaction):
    channel = interaction.channel
    guild_id = interaction.guild_id
    user_id = interaction.user.id

    # Retrieve the default settings for the guild
    defaults = database.check_defaults(guild_id)
    if defaults:
        guild_id, welcome_id, welcome_message, ai_category_id, Ai_channel_id = defaults

    # Check if the channel is within the AI category
    if channel.category_id == ai_category_id:
        # Delete the channel's history from the database
        database.delete_ai_channel_history(channel.id)
        # Delete the channel
        await channel.delete()
        await interaction.response.send_message("Chat channel has been closed.", ephemeral=True)
    else:
        await interaction.response.send_message("This command can only be used in the AI chat channels!", ephemeral=True)


def get_AI_group():
    return ai_group