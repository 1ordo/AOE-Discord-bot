from client import client
from resources.error_handler import has_permissions,validate_arguments
from discord import app_commands, Interaction, Embed, Color, utils, File
import discord 
import typing
from database import database
from collections import defaultdict
from discord.ui import View
from resources.translation_functions import translate_all_messages_in_thread,send_to_threads_with_webhooks_with_multiple_files,translate_text,replace_forum_and_thread_mentions,send_to_threads_with_webhooks


class thread_translator_paginator(View):
    def __init__(self, grouped_threads: dict[int, list[tuple]], timeout=60):
        super().__init__(timeout=timeout)
        self.grouped_threads = list(grouped_threads.items())  # Convert to a list of tuples (link_id, thread_group)
        self.current_page = 0
        self.total_pages = len(self.grouped_threads) // 10 + (1 if len(self.grouped_threads) % 10 else 0)  # 10 groups per page
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
        groups_to_display = self.grouped_threads[start:end]

        embed = discord.Embed(
            title="Translation Threads",
            description="Here are the current translation settings for your server threads:",
            color=discord.Color.blue()
        )

        # Add grouped threads to the embed
        for link_id, thread_group in groups_to_display:
            value = "\n".join([f"{thread.mention}: {language} [Webhook]({webhook})"
                               for thread, language, webhook in thread_group])
            embed.add_field(name=f"Group {link_id}", value=value, inline=False)

        # Update the message with the new embed
        await interaction.response.edit_message(embed=embed, view=self)






@client.tree.command(name="thread_translation", description="Automatically translate your threads easily")
@has_permissions(manage_guild=True)
@app_commands.guild_only()
@app_commands.choices(action=[
    app_commands.Choice(name="Set", value=1),
    app_commands.Choice(name="Remove", value=2),
    app_commands.Choice(name="Show", value=3)
])
async def thread_translation(interaction: Interaction,
                             action: int,
                             channel: typing.Optional[discord.TextChannel],
                             forum_channel: typing.Optional[discord.ForumChannel],
                             thread_language: typing.Optional[str],
                             thread_link_id: typing.Optional[int]):
    guild = interaction.guild
    channel = channel or forum_channel or interaction.channel
    
    if action == 1:
        validate_arguments(interaction, channel=channel, channel_language=thread_language, channel_link_id=thread_link_id)
        webhooks = await channel.webhooks()
        if webhooks:
            webhook = webhooks[0]  # Use the first webhook if one already exists
        else:
            # Create a new webhook
            webhook = await channel.create_webhook(name=f"{channel.name}-translation-webhook")

        database.set_threads_translation(guild.id, channel.id,0, thread_link_id, thread_language, webhook.url)
        embed = discord.Embed(
            title="Thread Translation Set",
            description=f"Translation settings have been updated for {channel.mention}.",
            color=discord.Color.green()
        )
        embed.add_field(name="Thread Language", value=thread_language, inline=False)
        embed.add_field(name="Thread Link ID", value=thread_link_id, inline=False)
        embed.add_field(name="Webhook Link", value=f"[thread_webhook]({webhook.url})", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    elif action == 2:
        validate_arguments(interaction, channel=channel)
        database.remove_threads_translation(guild.id, channel.id)
        embed = discord.Embed(
            title="Thread Translation Removed",
            description=f"Translation settings have been removed for {channel.mention}.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
    elif action == 3:
        try:
            threads = database.get_translation_thread_by_guild(guild.id)
            if threads:
                grouped_threads = defaultdict(list)

                # Group threads by thread_link_id
                for entry in threads:
                    thread_parent_id, thread_language, thread_link_id, thread_webhook,thread_id = entry[2], entry[5], entry[4], entry[6],entry[3]
                    if thread_id != 0:
                        continue
                    thread = interaction.guild.get_channel(thread_parent_id)
                    if thread:  # Ensure the thread still exists
                        grouped_threads[thread_link_id].append((thread, thread_language, thread_webhook))

                # Create the paginator and pass the grouped threads
                paginator = thread_translator_paginator(grouped_threads)

                # Show the first 10 groups
                embed = discord.Embed(
                    title="Translation Threads",
                    description=f"The next available id to assign to is `{database.get_next_available_link_id(guild.id)}`.\nHere are the current translation settings for your server threads:",
                    color=discord.Color.blue()
                )
                print(thread_parent_id, thread_language, thread_link_id, thread_webhook)
                for link_id, thread_group in list(grouped_threads.items())[:10]:  # First 10 groups
                    value = "\n".join([f"{thread.mention}: {language} [Webhook]({webhook})"
                                      for thread, language, webhook in thread_group])
                    embed.add_field(name=f"Group {link_id}", value=value, inline=False)

                # Send the initial message
                await interaction.response.send_message(embed=embed, view=paginator)
            else:
                embed = discord.Embed(
                    title="No Translation Threads",
                    description="There are no translation threads configured for this server.",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed)
        except Exception as e:
            print(e)
            import traceback
            traceback.print_exc()


@client.tree.command(name="translate_existing_threads", description="Translate messages in existing threads between two forums")
@has_permissions(manage_guild=True)
@app_commands.guild_only()
@app_commands.describe(
    source_forum="Select the source forum to translate messages from",
    target_forum_es="Select the target forum to translate messages to (Spanish)",
    target_forum_fr="Select the target forum to translate messages to (French)",
    source_language="Language of the messages in the source forum"
)
async def translate_existing_threads(interaction: Interaction, 
                                     source_forum: discord.ForumChannel, 
                                     target_forum_es: discord.ForumChannel,
                                     target_forum_fr: discord.ForumChannel,
                                     source_language: str):
    
    guild = interaction.guild
    await interaction.response.defer()
    
    # Always use EN-US as the source language
    source_language = "EN-US"
    
    # Retrieve all threads from the source forum
    source_threads = [thread for thread in source_forum.threads]
    
    if not source_threads:
        await interaction.response.send_message("The source forum has no threads.", ephemeral=True)
        return

    for src_thread in source_threads:
        link_id = database.get_next_available_link_id(guild.id)
        webhooks_en = await source_forum.webhooks()
        if webhooks_en:
            target_webhook_en = webhooks_en[0]
        else:
            target_webhook_en = await source_forum.create_webhook(name=f"{source_forum.name}-translation-webhook")

        database.set_threads_translation(
            guild_id=guild.id,
            parent_channel_id=source_forum.id,
            thread_id=src_thread.id,
            thread_link_id=link_id,
            language="EN-US",
            webhook_link=target_webhook_en.url  # No webhook for the original
        )

        translated_thread_name_es = translate_text(src_thread.name, source_lang=source_language, target_lang="ES")
        translated_thread_name_fr = translate_text(src_thread.name, source_lang=source_language, target_lang="FR")

        target_thread_es = await target_forum_es.create_thread(name=translated_thread_name_es, content="Translated content from source thread")
        webhooks_es = await target_forum_es.webhooks()
        if webhooks_es:
            target_webhook_es = webhooks_es[0]
        else:
            target_webhook_es = await target_forum_es.create_webhook(name=f"{target_forum_es.name}-translation-webhook")

        target_thread_fr = await target_forum_fr.create_thread(name=translated_thread_name_fr, content="Translated content from source thread")
        webhooks_fr = await target_forum_fr.webhooks()
        if webhooks_fr:
            target_webhook_fr = webhooks_fr[0]
        else:
            target_webhook_fr = await target_forum_fr.create_webhook(name=f"{target_forum_fr.name}-translation-webhook")

        # Now translate and send messages for each thread
        async for message in src_thread.history(limit=None):
            if message.author.bot:
                continue  # Skip bot messages
            translated_message_es = translate_text(message.content, source_lang=source_language, target_lang="es")
            await send_to_threads_with_webhooks_with_multiple_files(
                target_webhook_es.url,
                message.author.display_name,
                message.author.display_avatar.url,
                translated_message_es,
                message.attachments,
                target_thread_es.thread.id
            )
            # Translate the message content for French (FR)
            translated_message_fr = translate_text(message.content, source_lang=source_language, target_lang="fr")
            await send_to_threads_with_webhooks_with_multiple_files(
                target_webhook_fr.url,
                message.author.display_name,
                message.author.display_avatar.url,
                translated_message_fr,
                message.attachments,
                target_thread_fr.thread.id
            )
            
        database.set_threads_translation(
            guild_id=guild.id,
            parent_channel_id=target_forum_es.id,
            thread_id=target_thread_es.thread.id,
            thread_link_id=link_id,
            language="ES",
            webhook_link=target_webhook_es.url
        )
        database.set_threads_translation(
            guild_id=guild.id,
            parent_channel_id=target_forum_fr.id,
            thread_id=target_thread_fr.thread.id,
            thread_link_id=link_id,
            language="FR",
            webhook_link=target_webhook_fr.url
        )
    await interaction.followup.send("Translation of all threads has been completed!", ephemeral=True)
