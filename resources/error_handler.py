import discord
from discord import app_commands

class MissingPermissions(app_commands.AppCommandError):
    def __init__(self, missing_perms):
        self.missing_perms = missing_perms
        super().__init__(f"Missing permissions: {', '.join(missing_perms)}")

def has_permissions(**perms):
    def predicate(interaction: discord.Interaction):
        user = interaction.user
        if user.guild_permissions.administrator:
            return True
        missing_perms = [perm for perm, value in perms.items() if getattr(user.guild_permissions, perm, False) != value]
        if missing_perms:
            raise MissingPermissions(missing_perms)
        return True
    return app_commands.check(predicate)


class MissingArguments(app_commands.AppCommandError):
    def __init__(self, missing_args):
        self.missing_args = missing_args
        super().__init__(f"Missing arguments: {', '.join(missing_args)}")
    
    
def validate_arguments(interaction: discord.Interaction, **kwargs):
    missing_args = [arg for arg, value in kwargs.items() if value is None]
    if missing_args:
        raise MissingArguments(missing_args)