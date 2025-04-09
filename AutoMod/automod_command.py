from operator import ne
import discord
from discord import app_commands, Intents, Client, Interaction, SelectOption, Button
import typing
import datetime
import logging
from database import database
from discord.ui import View, Button, Select
from typing import List, Optional, Dict
from AutoMod.automod_embeds import automod_embeds
import asyncio
from resources.error_handler import has_permissions , MissingPermissions

# Todo : ADD QUARANTINE TO CHANNEL CREATE AND APPLY FOR EACH EXITING
# Todo : ADD QUARANTINE TO CHANNEL DELETE AND APPLY FOR EACH EXITING
# Todo : make channel selection for logs
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


Automod = app_commands.Group(name="automod", description="AutoMod Commands")


class ConfigView(View):
    def __init__(self, pages: List[discord.Embed],interaction: Interaction):
        super().__init__(timeout=180)
        self.interaction = interaction
        self.pages = pages
        self.current_page = 0
        self.prev_button = Button(
            label="Previous",
            style=discord.ButtonStyle.primary,
            disabled=True,
            row=1
        )
        self.prev_button.callback = self.prev_callback
        
        self.next_button = Button(
            label="Next",
            style=discord.ButtonStyle.primary,
            disabled=len(pages) <= 1,
            row=1
        )
        self.next_button.callback = self.next_callback

            
            
        
        # Create and add the select menu
        self.auto_mod_enable_select = Select(
            custom_id="auto_mod_enable_select",
            placeholder=f"Enable/Disable Features, current settings: {"enabled" if database.get_automod_settings(self.interaction.guild.id,'chosen_setting') else "disabled"}",
            options= self.options_selection(),
            row=0
        )
        
        self.auto_mod_enable_select.callback = self.select_callback
        
        if self.current_page == 0:
            self.add_item(self.auto_mod_enable_select)
            
        self.add_item(self.prev_button)
        self.add_item(self.next_button)

    def options_selection(self):
        if self.current_page == 0: # main_page
            options = [
                SelectOption(label="Enable All", value="enable_all", description="Enable all AutoMod features"),
                SelectOption(label="Disable All", value="disable_all", description="Disable all AutoMod features"),
                SelectOption(label="Custom", value="custom", description="Customize individual features")
            ]
        elif self.current_page == 1:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable Anti-Spam"),
                SelectOption(label="Disable", value="disable", description="Disable Anti-Spam")
            ]
        elif self.current_page == 2:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable Mention Spam"),
                SelectOption(label="Disable", value="disable", description="Disable Mention Spam")
            ]
        elif self.current_page == 3:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable Suspicious Link Detection"),
                SelectOption(label="Disable", value="disable", description="Disable Suspicious Link Detection")
            ]
        elif self.current_page == 4:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable Suspicious Account Detection"),
                SelectOption(label="Disable", value="disable", description="Disable Suspicious Account Detection")
            ]
        elif self.current_page == 5:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable New Account Restrictions"),
                SelectOption(label="Disable", value="disable", description="Disable New Account Restrictions")
            ]
        elif self.current_page == 6:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable Raid Protection"),
                SelectOption(label="Disable", value="disable", description="Disable Raid Protection")
            ]
        elif self.current_page == 7:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable Anti-Nuke Protection"),
                SelectOption(label="Disable", value="disable", description="Disable Anti-Nuke Protection")
            ]
        elif self.current_page == 8:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable Mass Ban/Kick Protection"),
                SelectOption(label="Disable", value="disable", description="Disable Mass Ban/Kick Protection")
            ]
        elif self.current_page == 9:
            options = [
                SelectOption(label="Enable", value="enable", description="Enable Suspicious Keyword Detection"),
                SelectOption(label="Disable", value="disable", description="Disable Suspicious Keyword Detection")
            ]
        else:
            options = []
        
        return options
    async def prev_callback(self, interaction: Interaction):
        self.current_page = max(0, self.current_page - 1)
        await self.update_message(interaction)

    async def next_callback(self, interaction: Interaction):
        self.current_page = min(len(self.pages) - 1, self.current_page + 1)
        await self.update_message(interaction)

    async def select_callback(self, interaction: Interaction):
        try:
            selected_value = self.auto_mod_enable_select.values[0]
            if selected_value == "enable_all":
                database.insert_all_true_settings(interaction.guild_id)
                updated_embed = discord.Embed(title="AutoMod Settings Updated", description="All AutoMod features have been enabled.", color=discord.Color.green())
                await self.update_message(interaction)
                await interaction.followup.send(embed=updated_embed, ephemeral=True)
            elif selected_value == "disable_all":
                await interaction.response.send_message("Disabling all AutoMod features...", ephemeral=True)
            elif selected_value == "custom":
                await interaction.response.send_message("Opening custom configuration...", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

    async def update_message(self, interaction: Interaction):
        try:
            buttons = [item for item in self.children if isinstance(item, Button)]
            buttons[0].disabled = self.current_page == 0
            buttons[1].disabled = self.current_page == len(self.pages) - 1
            await interaction.response.edit_message(embed=self.pages[self.current_page], view=self)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)



@has_permissions(manage_guild=True)
@Automod.command(name="config", description="Configure AutoMod settings")
async def automod_config(interaction: Interaction):
    try:
        
        guild_id = interaction.guild_id
        automod_settings = database.get_all_automod_settings(guild_id)
        
        start_embed = automod_embeds.start_auto_mod_config()
        spam_embed = automod_embeds.Anti_spam_embed(automod_settings[3] if automod_settings else False)
        mention_spam_embed = automod_embeds.Mention_spam_embed(automod_settings[7] if automod_settings else False)
        suspicious_link_embed = automod_embeds.Suspicious_link_embed(automod_settings[10] if automod_settings else False)
        suspicious_account_embed = automod_embeds.Suspicious_account_embed(automod_settings[13] if automod_settings else False)
        new_account_restrictions_embed = automod_embeds.New_account_restrictions_embed(automod_settings[15] if automod_settings else False)
        raid_protection_embed = automod_embeds.Raid_protection_embed(automod_settings[17] if automod_settings else False)
        anti_nuke_protection_embed = automod_embeds.Anti_nuke_protection_embed(automod_settings[20] if automod_settings else False)
        mass_ban_kick_protection_embed = automod_embeds.Mass_ban_kick_protection_embed(automod_settings[23] if automod_settings else False)
        suspicious_keyword_detection_embed = automod_embeds.Suspicious_keyword_detection_embed(automod_settings[26] if automod_settings else False)
        
        pages = [
                start_embed,
                spam_embed,
                mention_spam_embed,
                suspicious_link_embed,
                suspicious_account_embed,
                new_account_restrictions_embed,
                raid_protection_embed,
                anti_nuke_protection_embed,
                mass_ban_kick_protection_embed,
                suspicious_keyword_detection_embed
                 ]  # Add more embeds here as needed
        view = ConfigView(pages,interaction)
        await interaction.response.send_message(embed=start_embed, view=view)
    except Exception as e:
        import traceback; traceback.print_exc();
        await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)

def get_automod_group() -> app_commands.Group:
    return Automod