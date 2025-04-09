
from client import client
from resources.error_handler import has_permissions, validate_arguments
from discord import app_commands, Interaction, Embed, Color
import discord
import typing
from database import database
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@client.tree.command(name="role_all_links", description="Roles all members in the server with the linked configuration")
@has_permissions(manage_guild=True)
@app_commands.guild_only()
async def role_all_links(interaction: discord.Interaction):
    guild = interaction.guild
    linked_roles = database.get_linked_roles_by_guild(guild.id)

    if not linked_roles:
        await interaction.response.send_message("No linked roles configuration found.", ephemeral=True)
        return

    await interaction.response.send_message("Processing role assignments... This might take a while.", ephemeral=True)

    for member in guild.members:
        member_roles = set(member.roles)  # Get current roles for the member

        for entry in linked_roles:
            source_role_id, target_role_id, role_link_id = entry[2], int(entry[3]), entry[4]
            
            source_role = guild.get_role(source_role_id)
            target_role = guild.get_role(target_role_id)

            if not source_role or not target_role:
                continue  # Skip if any role is invalid

            # Check if the member has the source role
            if source_role in member_roles:
                # Get all roles that are required for this linked group
                required_roles = [
                    guild.get_role(entry[2]) 
                    for entry in linked_roles 
                    if entry[4] == role_link_id
                ]
                
                # If the member has all required roles, add the target role
                if all(role in member_roles for role in required_roles):
                    if target_role not in member_roles:
                        await member.add_roles(target_role)
                        logger.info(f"{member.display_name} has been given the {target_role.name} role.")
                # If any of the required roles are missing, remove the target role
                elif target_role in member_roles:
                    await member.remove_roles(target_role)
                    logger.info(f"The {target_role.name} role has been removed from {member.display_name} because they no longer meet the requirements.")

    await interaction.followup.send("Role assignments have been processed.")
