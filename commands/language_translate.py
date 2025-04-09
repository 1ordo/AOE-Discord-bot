from client import client
from resources.error_handler import has_permissions,validate_arguments
from discord import app_commands, Interaction, Embed, Color, utils, File
import discord 
import typing
from database import database
from collections import defaultdict
from discord.ui import View





class translator_paginator(View):
    def __init__(self, grouped_channels: dict[int, list[tuple]], timeout=60):
        super().__init__(timeout=timeout)
        self.grouped_channels = list(grouped_channels.items())  # Convert to a list of tuples (link_id, channel_group)
        self.current_page = 0
        self.total_pages = len(self.grouped_channels) // 10 + (1 if len(self.grouped_channels) % 10 else 0)  # 10 groups per page
        self.update_buttons()


    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages - 1

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
    async def previous_button(self, interaction: Interaction, button: discord.ui.Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await self.update_message(interaction)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: Interaction, button: discord.ui.Button):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            await self.update_message(interaction)

    async def update_message(self, interaction: Interaction):
        # Get the current 10 groups to display
        start = self.current_page * 10
        end = start + 10
        groups_to_display = self.grouped_channels[start:end]

        embed = discord.Embed(
            title="Translation Channels",
            description="Here are the current translation settings for your server:",
            color=discord.Color.blue()
        )

        # Add grouped channels to the embed
        for link_id, channel_group in groups_to_display:
            value = "\n".join([f"{channel.mention}: {language} [Webhook]({webhook})"
                               for channel, language, webhook in channel_group])
            embed.add_field(name=f"Group {link_id}", value=value, inline=False)

        # Update the message with the new embed
        await interaction.response.edit_message(embed=embed, view=self)










@client.tree.command(name="channel_translation",description="automatically translate your channels easily")
@has_permissions(manage_guild = True)
@app_commands.guild_only()
@app_commands.choices(action=[app_commands.Choice(name="Set",value=1),
                              app_commands.Choice(name="Remove",value=2),
                              app_commands.Choice(name="Show",value=3)])
async def channel_translation(interaction:Interaction,
                      action :int,
                      channel:typing.Optional[discord.TextChannel],
                      channel_language:typing.Optional[str],
                      channel_link_id:typing.Optional[int],
                      ):
      guild = interaction.guild
      if not channel:
            channel = interaction.channel
      if action == 1:
            
            validate_arguments(interaction, channel=channel,channel_language=channel_language,channel_link_id=channel_link_id)
            webhooks = await channel.webhooks()
            if webhooks:
                  webhook = webhooks[0]  # Use the first webhook if one already exists
            else:
                  # Create a new webhook
                  webhook = await channel.create_webhook(name=f"{channel.name}-translation-webhook")
            
            
            database.set_translation_channels(guild.id,channel.id,channel_language,channel_link_id,webhook.url)
            embed = discord.Embed(
            title="Channel Translation Set",
            description=f"Translation settings have been updated for {channel.mention}.",
            color=discord.Color.green()
            )
            embed.add_field(name="Channel Language", value=channel_language, inline=False)
            embed.add_field(name="Channel Link ID", value=channel_link_id, inline=False)
            embed.add_field(name="Webhook Link", value=f"[channel_webhook]({webhook.url})", inline=False)
            await interaction.response.send_message(embed=embed,ephemeral=True)
      if action == 2:
            validate_arguments(interaction, channel=channel)
            database.remove_translation_channels(guild.id,channel.id)
            embed = discord.Embed(
            title="Channel Translation Removed",
            description=f"Translation settings have been removed for {channel.mention}.",
            color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
      elif action == 3:
            try:
                  channels = database.get_translation_channel_by_guild(guild.id)
                  if channels:
                        grouped_channels = defaultdict(list)

                        # Group channels by channel_link_id
                        for entry in channels:
                              channel_id, channel_language, channel_link_id, channel_webhook = entry[2], entry[3], entry[4], entry[5]
                              channel = interaction.guild.get_channel(channel_id)
                              if channel:  # Ensure the channel still exists
                                    grouped_channels[channel_link_id].append((channel, channel_language, channel_webhook))

                        # Create the paginator and pass the grouped channels
                        paginator = translator_paginator(grouped_channels)

                        # Show the first 10 groups
                        embed = discord.Embed(
                        title="Translation Channels",
                        description="Here are the current translation settings for your server:",
                        color=discord.Color.blue()
                        )
                        for link_id, channel_group in list(grouped_channels.items())[:10]:  # First 10 groups
                              value = "\n".join([f"{channel.mention}: {language} [Webhook]({webhook})"
                                                for channel, language, webhook in channel_group])
                              embed.add_field(name=f"Group {link_id}", value=value, inline=False)

                        # Send the initial message
                        await interaction.response.send_message(embed=embed, view=paginator)
                  else:
                        embed = discord.Embed(
                        title="No Translation Channels",
                        description="There are no translation channels configured for this server.",
                        color=discord.Color.orange()
                        )
                        await interaction.response.send_message(embed=embed)
            except Exception as e:
                  print(e)
                  import traceback; traceback.print_exc();

            
      
