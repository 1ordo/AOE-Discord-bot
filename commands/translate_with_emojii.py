import discord
import typing
import os
import asyncio
from discord import app_commands, Interaction
from discord.app_commands import Choice
from client import client
from database import database
from resources.error_handler import has_permissions,validate_arguments


@client.tree.command(name = "emoji_translate",description="translate using an emoji")
@app_commands.choices(action = [Choice(name= "add",value=1),Choice(name="remove",value=2)])
@has_permissions(manage_guild = True)
async def roles_translation_management(interaction: Interaction, action: typing.Optional[int],emoji: typing.Optional[str], language:typing.Optional[str]):
    is_ephermal = False
    if action == 1:
        if emoji and language:
            is_ephermal = True
            
            database.set_translation_emoji(interaction.guild.id, emoji, language)
            embed = discord.Embed(
                title="Translation Emoji Added",
                description=f"You have successfully added your translation emoji! \nEmoji: {emoji} \nLanguage: **{language}**",
                color=discord.Color.green()
            )
    elif action == 2:
        if emoji:
            is_ephermal = True

            database.delete_translation_emojies(interaction.guild.id, emoji)

            embed = discord.Embed(
                title="Translation Emoji Removed",
                description="Translation emoji has been successfully deleted",
                color=discord.Color.orange()
            )

    else:
        results = database.get_translation_roles(interaction.guild.id)
        embed = discord.Embed(
            title="Your current Translation Emojis",
            description="Here are your current translation emojis!",
            color=discord.Color.green()
        )
        if results:
            for result in results:
                _, emoji_id, language_db = result
                emoji_display = f"<:emoji:{emoji_id}>" if isinstance(emoji_id, int) else emoji_id
                embed.add_field(name=f"Emoji: {emoji_display}", value=f"Language: {language_db}")
        else:
            embed = discord.Embed(
                title="No Configuration Found",
                description="You haven't set up your translation emojis yet!",
                color=discord.Color.red()
            )
            is_ephermal = True

    await interaction.response.send_message(embed=embed, ephemeral=is_ephermal)