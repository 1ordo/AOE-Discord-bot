from client import client
from resources.error_handler import has_permissions, validate_arguments
from discord import app_commands, Interaction, Embed, Color
import discord
import typing
from database import database
from collections import defaultdict


@client.tree.command(name="role_link", description="Link roles together automatically")
@has_permissions(manage_guild=True)
@app_commands.guild_only()
@app_commands.choices(action=[app_commands.Choice(name="Set", value=1),
                              app_commands.Choice(name="Remove", value=2),
                              app_commands.Choice(name="Show", value=3)])
async def role_link(interaction: Interaction,
                    action: int,
                    role: typing.Optional[discord.Role],
                    target_role: typing.Optional[discord.Role],
                    role_link_id: typing.Optional[int]):
    guild = interaction.guild

    if action == 1:  # Set role link
        validate_arguments(interaction, role=role, target_role=target_role, role_link_id=role_link_id)
        
        if not target_role:
            await interaction.response.send_message("You must specify a target role to link.", ephemeral=True)
            return

        # Set role linking in the database
        database.set_linked_role(guild.id, role.id, target_role.id, role_link_id)

        embed = discord.Embed(
            title="Role Linking Set",
            description=f"Linking settings have been updated for {role.mention}.",
            color=discord.Color.green()
        )
        embed.add_field(name="Target Role", value=target_role.mention, inline=False)
        embed.add_field(name="Link ID", value=role_link_id, inline=False)
        await interaction.response.send_message(embed=embed)

    elif action == 2:  # Remove role link
        validate_arguments(interaction, role=role,role_link_id=role_link_id)

        # Remove role linking from the database
        database.remove_linked_role(guild.id, role.id,role_link_id)
        
        embed = discord.Embed(
            title="Role Linking Removed",
            description=f"Linking settings have been removed for {role.mention}.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)

    elif action == 3:  # Show role links
        roles = database.get_linked_roles_by_guild(guild.id)
        if roles:
            grouped_roles = defaultdict(list)

            # Group roles by role_link_id
            for entry in roles:
                role_id, target_role_id, role_link_id = entry[2], entry[3], entry[4]
                source_role = guild.get_role(role_id)
                target_role = guild.get_role(target_role_id)

                # Check if both roles still exist
                if source_role and target_role:
                    grouped_roles[role_link_id].append((source_role, target_role))

            embed = discord.Embed(
                title="Linked Roles",
                description="Here are the current role linking settings for your server:",
                color=discord.Color.blue()
            )

            for link_id, role_group in grouped_roles.items():
                value = "\n".join([f"{role.mention} -> {target_role.mention}"
                                   for role, target_role in role_group])
                embed.add_field(name=f"Link Group {link_id}", value=value, inline=False)

            if grouped_roles:
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("No valid role links found.", ephemeral=True)
        else:
            embed = discord.Embed(
                title="No Role Links",
                description="There are no role linking configurations for this server.",
                color=discord.Color.orange()
            )
            await interaction.response.send_message(embed=embed)

