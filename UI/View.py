from discord import app_commands, Interaction, Embed, Color, utils, File
from discord.ui import  View, Button, Select, Modal
import discord

class StoreView(View):
    def __init__(self, items):
        super().__init__(timeout=None)  # No timeout for the interaction
        self.items = items
        self.original_interaction = None
        #self.dropdown = StoreDropdown(items)
        #self.add_item(StoreDropdown(items))
        #self.add_item(BalanceButton())

    def update_items(self, items):
        self.items = items
        self.dropdown.update_options(items)
    
    
    
    async def on_timeout(self):
        """"""
        #logger.info("View timed out")