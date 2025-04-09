import discord
from datetime import timezone, datetime as dt1,timedelta
from discord import app_commands
import logging
import traceback
from client import client
from resources.error_handler import has_permissions, MissingArguments,MissingPermissions
from resources.Client_control_panel import error_counts,update_control_panel


@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, MissingPermissions):
        missing_perms = ', '.join(error.missing_perms)
        embed = discord.Embed(
            title="Permission Error",
            description=f"You are missing the following permissions to execute this command: {missing_perms}",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif isinstance(error, MissingArguments):
        missing_args = ', '.join(error.missing_args)
        embed = discord.Embed(
            title="Argument Error",
            description=f"You're missing the following required arguments: {missing_args}",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="Error",
            description="An error occurred while processing the command.",
            color=0xFF0000
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        # Log the error with full traceback details
        error_details = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        logging.error(f"Error in command '{interaction.command}': {error_details}")
        error_counts['command_error'] += 1
        # Send error details to a specific channel in Discord
        error_channel = client.get_channel(1289297435239120907)  # Replace with your channel ID
        if error_channel:
            embed = discord.Embed(
                title="Error Report",
                description=f"An error occurred in command: `{interaction.command}`",
                color=discord.Color.red()
            )
            embed.add_field(name="User", value=interaction.user.mention, inline=True)
            embed.add_field(name="Command", value=interaction.command.name, inline=True)
            embed.add_field(name="Channel", value=interaction.channel.mention, inline=True)
            embed.add_field(name="Guild",value=interaction.guild.name)
            embed.add_field(name="Error", value=f"```{error}```", inline=False)
            embed.add_field(name="Traceback", value=f"```{error_details[:1000]}...```", inline=False)  # Limit to 1000 chars for embed field
            await error_channel.send(embed=embed)

async def send_error_report(event_name, error_details, *args):
    # Log the error with full traceback details
    logging.error(f"Error in event '{event_name}': {error_details}")

    # Send error details to a specific channel in Discord
    error_channel = client.get_channel(1289297435239120907)  # Replace with your channel ID
    if error_channel:
        embed = discord.Embed(
            title="Event Error Report",
            description=f"An error occurred in event: `{event_name}`",
            color=discord.Color.red()
        )
        
        # Add details if available
        if args:
            user = args[0].author if isinstance(args[0], discord.Message) else None
            channel = args[0].channel if isinstance(args[0], discord.Message) else None
            guild = args[0].guild if isinstance(args[0], discord.Message) else None

            if user:
                embed.add_field(name="User", value=user.mention, inline=True)
            if channel:
                embed.add_field(name="Channel", value=channel.mention, inline=True)
            if guild:
                embed.add_field(name="Guild", value=guild.name, inline=True)

        embed.add_field(name="Error", value=f"```{error_details[:1000]}...```", inline=False)  # Limit to 1000 chars for embed field
        await error_channel.send(embed=embed)


@client.event
async def on_error(event, *args, **kwargs):
    error_details = "".join(traceback.format_exc())
    error_counts[event] += 1
    await send_error_report(event, error_details, *args)




