
from discord import app_commands, Interaction, Embed, Color, utils, File
from discord.ui import  View, Button, Select, Modal
import discord

class ConfirmButton(Button):
    def __init__(self, item_id: int):
        super().__init__(label="Confirm", style=discord.ButtonStyle.green, custom_id=f"confirm_{item_id}")
        self.item_id = item_id

    async def callback(self, interaction: Interaction):
        """"""
        


class CancelButton(Button):
    def __init__(self, item_id: int):
        super().__init__(label="Cancel", style=discord.ButtonStyle.red, custom_id=f"cancel_{item_id}")
        self.item_id = item_id

    async def callback(self, interaction: Interaction):
        await interaction.response.send_message("", ephemeral=True)