from client import client
from resources.error_handler import has_permissions, validate_arguments
from discord import app_commands, Interaction, Embed, Color
import discord
import typing
from database import database
from collections import defaultdict
import logging
from resources.translation_functions import translate_text
import json
from discord.ui import View, Button, Modal, TextInput
import discord
import logging
import re
from datetime import datetime, timedelta
from discord.ext import tasks

polls_data = defaultdict(lambda: {"title": None, "description": None, "footer": None, "options": [], "messages": {}, "channel_id": None, "end_vote":None})

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# View to interactively create the poll
class PollSetupView(View):
    def __init__(self, interaction,channel, poll_id):
        super().__init__(timeout=1000)
        self.interaction = interaction
        self.poll_id = poll_id
        self.poll_message = None  # This will be set once the message is sent
        
    async def update_poll_message(self):
        poll_data = polls_data[self.poll_id]
        if self.poll_message:
            embed = Embed(title=poll_data["title"], description=poll_data["description"], color=Color.blue())
            embed.set_footer(text="Poll ends in : `Time`")
            for i, option in enumerate(poll_data["options"], start=1):
                embed.add_field(name=f"{i}. {option}", value="", inline=False)

            # Update the poll message
            await self.poll_message.edit(embed=embed)

    @discord.ui.button(label="Edit Title", style=discord.ButtonStyle.primary,row=0)
    async def edit_title(self, interaction: Interaction, button: Button):
        modal = PollTitleModal(self.poll_id, self)
        self.poll_message = interaction.message
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Edit Description", style=discord.ButtonStyle.primary,row=0)
    async def edit_description(self, interaction: Interaction, button: Button):
        modal = PollDescriptionModal(self.poll_id, self)
        self.poll_message = interaction.message
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Add Option", style=discord.ButtonStyle.secondary,row=0)
    async def add_option(self, interaction: Interaction, button: Button):
        modal = PollOptionModal(self.poll_id, add=True, view=self)
        self.poll_message = interaction.message
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Remove Option", style=discord.ButtonStyle.danger,row=0)
    async def remove_option(self, interaction: Interaction, button: Button):
        modal = PollOptionModal(self.poll_id, add=False, view=self)
        self.poll_message = interaction.message
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Send Poll", style=discord.ButtonStyle.success,row=1)
    async def send_poll(self,interaction: Interaction, button: Button):
        await interaction.response.defer()
        poll_data = polls_data[self.poll_id]
        channel = interaction.guild.get_channel(poll_data["channel_id"])
        # Check if all necessary fields are set
        if not poll_data["title"] or not poll_data["description"] or len(poll_data["options"]) < 2:
            await interaction.response.send_message("Poll must have a title, description, and at least two options!", ephemeral=True)
            return
        
        
        poll_end_time = poll_data["end_vote"]
        if poll_end_time == 0 or None:
            poll_end_time_actual = None
        else:
            poll_end_time_actual = datetime.now() + timedelta(minutes=poll_end_time)
            
            
        # Create and send the poll embed
        embed = Embed(title=poll_data["title"], description=poll_data["description"], color=Color.blue())
        embed.set_footer(text=f"Poll ends in: {poll_end_time_actual if poll_end_time_actual else "Not Specified"}")
        for i, option in enumerate(poll_data["options"], start=1):
            embed.add_field(name=f"{i}. {option}", value="", inline=False)

        # Send poll in the selected channel
        poll_message = await channel.send(embed=embed)

        # Add reactions for each option
        for emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][:len(poll_data["options"])]:
            await poll_message.add_reaction(emoji)
        poll_options_json = json.dumps(poll_data["options"])
        
        
        
        
        # Store the poll in the database for syncing
        database.set_linked_poll(
            guild_id=interaction.guild.id,
            channel_id=poll_data["channel_id"],
            message_id=poll_message.id,
            poll_link_id=self.poll_id,
            poll_title=poll_data["title"],
            poll_description=poll_data["description"],
            poll_footer=poll_data["footer"],
            poll_options=poll_options_json,
            poll_end_time= poll_end_time_actual, # You can add an end time if needed
            is_original=True
        )

        # Send to translation channels
        await send_poll_to_translation_channels(
            interaction,channel ,poll_data["title"], poll_data["description"], poll_data["options"], self.poll_id,poll_end_time_actual
        )
        
        await interaction.message.edit(embed=Embed(title="Poll has been sent successfully!",color=Color.green()),view=None)
        polls_data.clear()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger,row=1)
    async def cancel_poll(self,interaction: Interaction, button: Button):
        # Remove poll data and stop interaction
        polls_data.pop(self.poll_id, None)
        await interaction.message.edit(embed=Embed(title="Poll has been cancelled.",color=Color.orange()),view=None)
        polls_data.clear()
        self.stop()

# Modal for editing the title
class PollTitleModal(Modal):
    def __init__(self, poll_id, view):
        super().__init__(title="Edit Poll Title")
        self.poll_id = poll_id
        self.view = view
        self.title_input = TextInput(label="Poll Title", placeholder="Enter the title of the poll", required=True)
        self.add_item(self.title_input)

    async def on_submit(self, interaction: Interaction):
        polls_data[self.poll_id]["title"] = self.title_input.value
        await interaction.response.defer()
        
        # Update the poll message using the view instance
        if self.view:
            await self.view.update_poll_message()


# Modal for editing the description
class PollDescriptionModal(Modal):
    def __init__(self, poll_id, view):
        super().__init__(title="Edit Poll Description")
        self.poll_id = poll_id
        self.view = view
        self.description_input = TextInput(label="Poll Description", placeholder="Enter the description of the poll", required=True)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: Interaction):
        polls_data[self.poll_id]["description"] = self.description_input.value
        await interaction.response.defer()
        
        # Update the poll message using the view instance
        if self.view:
            await self.view.update_poll_message()


class PollOptionModal(Modal):
    def __init__(self, poll_id, add=True, view=None):
        super().__init__(title="Add Option" if add else "Remove Option")
        self.poll_id = poll_id
        self.add = add
        self.view = view
        self.option_input = TextInput(label="Option", placeholder="Enter the poll option", required=True)
        self.add_item(self.option_input)

    async def on_submit(self, interaction: Interaction):
        option = self.option_input.value
        if self.add:
            polls_data[self.poll_id]["options"].append(option)
            await interaction.response.defer()
        else:
            if option in polls_data[self.poll_id]["options"]:
                polls_data[self.poll_id]["options"].remove(option)
                await interaction.response.defer()
            else:
                await interaction.response.send_message(embed=Embed(title=f"Option '{option}' not found.",color=Color.red()), ephemeral=True)

        # Update the poll message using the view instance
        if self.view:
            await self.view.update_poll_message()



def convert_to_minutes(time_str: str) -> int:
      pattern = r"(?:(\d+)h)?\s*(?:(\d+)m)?"
      match = re.match(pattern, time_str.lower().strip())
      
      if not match:
            return None
      
      hours = int(match.group(1)) if match.group(1) else 0
      minutes = int(match.group(2)) if match.group(2) else 0
      return hours * 60 + minutes


# Command to start the poll setup
@client.tree.command(name="poll", description="Create a poll with buttons to edit and send.")
@has_permissions(manage_guild=True)
@app_commands.describe(channel="The channel to send the poll in")
async def poll(interaction: Interaction, channel: discord.TextChannel,poll_id:int,end_time:str):
    polls_data[poll_id]["channel_id"] = channel.id
    view = PollSetupView(interaction,channel, poll_id)
    end_time_minutes = convert_to_minutes(end_time)
    polls_data[poll_id]["end_vote"] = end_time_minutes
    await interaction.response.send_message(embed=Embed(title="example",description="needs to be filled"), view=view)
    

# Function to send poll to translation channels
async def send_poll_to_translation_channels(interaction: Interaction, channel, title, description, options_list, poll_id,poll_end_time_actual):
    current_channel = database.get_translation_channel_by_channel(interaction.guild.id, channel.id)
    if not current_channel:
        return

    _, guild_id, current_channel_id, current_language, channel_link_id, _ = current_channel
    grouped_channels = database.get_translation_channel_by_link_id(interaction.guild.id, channel_link_id)
    footer = f"Poll ends in: {poll_end_time_actual if poll_end_time_actual else "Not Specified"}"
    for entry in grouped_channels:
        _, guild_id, channel_id, channel_language, channel_link_id, _ = entry
        if channel_id == current_channel_id:
            continue

        channel = client.get_channel(channel_id)
        translated_title = translate_text(title,source_lang=current_language, target_lang=channel_language)
        translated_description = translate_text(description,source_lang=current_language, target_lang=channel_language)
        translated_footer = translate_text(footer,source_lang=current_language, target_lang=channel_language)

        embed = Embed(title=translated_title, description=translated_description, color=Color.blue())
        embed.set_footer(text=translated_footer)

        # Translate options and prepare them for storage
        translated_options = [translate_text(option,source_lang=current_language, target_lang=channel_language) for option in options_list]
        i=1
        for option in translated_options:
            embed.add_field(name=f"{i}. {option}", value=f"", inline=False)
            i = i + 1
        translated_options_json = json.dumps(translated_options)
        
        poll_message = await channel.send(embed=embed)
        try:
            database.set_linked_poll(guild_id, channel_id, poll_message.id, poll_id, translated_title, translated_description, translated_footer, translated_options_json, poll_end_time_actual,False)
        except:
            pass
        for emoji in ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][:len(options_list)]:
            await poll_message.add_reaction(emoji)
            
            




votes_data = defaultdict(lambda: defaultdict(int))



@tasks.loop(seconds=10)  # Runs every 30 seconds
async def update_poll_messages():
    now = datetime.now()
    for guild in client.guilds:
        guild_id = guild.id
        all_polls = database.get_linked_poll_by_guild_and_original(guild_id,True)  
        if all_polls:
            for poll in all_polls:
                poll_id = poll[4]  #! Poll ID is stored in the 5th column
                poll_data = {
                    "title": poll[5],
                    "description": poll[6],
                    "options": json.loads(poll[8]),
                    "end_vote": poll[10],
                    "channel_id": poll[2]
                }
                try:
                    poll_end_time = poll_data["end_vote"]
                    if poll_end_time and now > poll_end_time:
                        continue  # Skip ended polls

                    remaining_time = poll_end_time - now if poll_end_time else None
                    vote_counts = dict(database.get_votes_for_poll(poll_id))
                    logger.info(f"Vote counts for poll {poll_id}: {vote_counts}")
                    embed = Embed(
                        title=poll_data["title"],
                        description=poll_data["description"],
                        color=Color.blue()
                    )
                    i = 1
                    for option in poll_data["options"]:
                        votes = vote_counts.get(i - 1, 0)
                        embed.add_field(name=f"{i}. {option}", value=f"Votes: {votes}", inline=False)
                        i = i + 1

                    if remaining_time:
                        
                        embed.set_footer(text=f"Time remaining: {remaining_time.seconds // 60} minutes, {remaining_time.seconds % 60} seconds")
                    
                    channel = client.get_channel(poll_data["channel_id"])
                    
                    message_id = database.get_linked_poll_by_poll_link_id_and_channel(guild_id, poll_id, poll_data["channel_id"])[0][3]  # Fetch message_id from the database
                    try:
                        message = await channel.fetch_message(message_id)
                        await message.edit(embed=embed)

                        # Optionally, update in all translation channels
                        await update_translated_poll_messages(guild_id,channel,poll_id,vote_counts,remaining_time)
                    except Exception as e:
                        print(e)
                        pass
                except Exception as e:
                    import traceback; traceback.print_exc();
                    print(e)
                    pass



async def update_translated_poll_messages(guild_id,channel,poll_id,vote_counts,remaining_time):
    # Fetch all linked translation channels
    linked_channels = database.get_translation_channel_by_channel(guild_id,channel.id)
    if linked_channels:
        _, guild_id, current_channel_id, current_language, channel_link_id, _ = linked_channels
        trans_channels = database.get_translation_channel_by_link_id(guild_id,channel_link_id)

        if trans_channels:
            for channel_info in trans_channels:
                try:
                    channel_id = channel_info[2]
                    language = channel_info[3]
                    req_data = database.get_linked_poll_by_poll_link_id_and_channel_and_original(guild_id,poll_id,channel_id,False)
                    if req_data:
                        message_id = req_data[0][3]
                        options = req_data[0][8]
                        
                        channel = client.get_channel(channel_id)
                        
                        try:
                            message = await channel.fetch_message(message_id)
                            translated_options = json.loads(options)
                            embed = Embed(title= req_data[0][5],
                                        description=req_data[0][6])
                            i=1
                            if language == "FR":
                                embed.set_footer(text=f"Temps restant : {remaining_time.seconds // 60} minutes, {remaining_time.seconds % 60} secondes")
                            elif language == "ES":
                                embed.set_footer(text=f"Tiempo restante: {remaining_time.seconds // 60} minutos, {remaining_time.seconds % 60} segundos")
                            else:
                                embed.set_footer(text=f"Time remaining: {remaining_time.seconds // 60} minutes, {remaining_time.seconds % 60} seconds")
                            for option in translated_options:
                                votes = vote_counts.get(i - 1, 0)
                                embed.add_field(name=f"{i}. {option}", value=f"Votes: {votes}", inline=False)
                                i = i + 1
                            await message.edit(embed=embed)
                        except Exception as e:
                            logger.error(F"HELP!!!!!:      {e}")
                            pass
                except Exception as e:
                    import traceback; traceback.print_exc();
                    logger.error(F"HELP!!!!: {e}")
                    continue
                    




  # Start the loop when the bot is ready
