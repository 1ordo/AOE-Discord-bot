

from discord import app_commands, Interaction, Embed, Color, utils, File
from discord.ui import  View, Button, Select, Modal
import discord
class StoreDropdown(Select):
    def __init__(self, items):
        if items:
            
            options = [
            discord.SelectOption(label=item["item_name"], description=f"{f"{item["item_details"]} |" if item["item_details"] else ""} Price: {item["item_price"]}", value=str(item["item_id"]),emoji=item["item_image"])
                for item in items
            ]
            options.append(discord.SelectOption(label="Reset", description="Clear your selection", value="reset"))
        else:
            # If no items are available, create a single disabled option
            options = [discord.SelectOption(label="No items available", description="Please check back later", value="empty")]
        
        # If no items, disable the dropdown
        super().__init__(placeholder="Select an item to purchase" if items else "No items available", 
                         min_values=1, max_values=1, options=options, disabled=not items)

    def update_options(self, items):
        if items:
            self.options = [
            discord.SelectOption(label=item["item_name"], description=f"{f"{item["item_details"]} |" if item["item_details"] else ""} Price: {item["item_price"]}", value=str(item["item_id"]),emoji=item["item_image"])
                for item in items
            ]
        else:
            self.options = [discord.SelectOption(label="No items available", description="Please check back later", value="empty")]
            self.options.append(discord.SelectOption(label="Reset", description="Clear your selection", value="reset"))
        self.disabled = not items
    
    
    async def callback(self, interaction: Interaction):
        if self.values[0] == "reset":
            # Handle the reset case
            await interaction.response.send_message("Selection has been reset.", ephemeral=True)
            return