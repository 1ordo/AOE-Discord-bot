from discord import app_commands, Intents, Client, Interaction
import discord
from commands.server_commands import get_server_group
from commands.AI_Commands import get_AI_group
#from AutoMod.automod_command import get_automod_group

intents = discord.Intents.all()
intents.message_content = True
intents.guilds = True
intents.guild_messages = True
intents.presences = False
intents.auto_moderation = True
intents.auto_moderation_configuration = True
intents.auto_moderation_execution = True

class appcomm(Client):
    def __init__(self, *, intents: Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
    async def setup_hook(self):
        self.tree.add_command(get_server_group())
        self.tree.add_command(get_AI_group())
        #self.tree.add_command(get_automod_group())

client = appcomm(intents=intents)