import discord
import typing
import os
import asyncio
from discord import app_commands, Interaction
from discord.app_commands import Choice
from client import client
from database import database
from resources.error_handler import has_permissions,validate_arguments




@client.tree.command(name = "roles_translate",description="translate using a role")
@app_commands.choices(action = [Choice(name= "add",value=1),Choice(name="remove",value=2)])
@has_permissions(manage_guild = True)
async def roles_translation_management(interaction: Interaction, action: typing.Optional[int],role: typing.Optional[discord.Role], language:typing.Optional[str]):
    is_ephermal = False
    if action == 1:
        if role and language:
            is_ephermal = True
            database.set_translation_roles(interaction.guild.id,role.id,language)
            embed = discord.Embed(title="Translation Role Added",description=f"You have successfully added your translation role! \nRole: {role.mention} \nlanguage: **{language}**",color=discord.Color.green())
    elif action == 2:
        if role:
            is_ephermal = True
            database.delete_translation_role(interaction.guild.id,role.id)
            embed = discord.Embed(title="Translation Role Removed",description="Translation Role has been successfully deleted",color=discord.Color.orange())
    else:
        results = database.get_translation_roles(interaction.guild.id)
        embed = discord.Embed(title="Your current Translation Roles",description="Here is your current translation roles!", color=discord.Color.green())
        if results:
            for result in result:
                _ , role_id , language_db = result
                role = interaction.guild.get_role(role_id)
                if role:
                    embed.add_field(name=role.mention,value=f"Language: {language_db}")
        else:
            embed = discord.Embed(title="No configuration Found.",description="You didn't set up your language roles yet!",color=discord.Color.red())
            is_ephermal = True
    await interaction.response.send_message(embed=embed,ephemeral=is_ephermal)
            

