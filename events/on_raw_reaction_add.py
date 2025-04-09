
import discord
from datetime import timezone, datetime as dt1,timedelta
from langdetect import detect
from database import database #database.py
import datetime
import pytz
from client import client
import logging
from collections import defaultdict
import re
from resources.error_handler import MissingPermissions, has_permissions,MissingArguments
import resources.error_tracer
from resources.translation_functions import tr_roles_and_emojies
from discord import Embed

announcement_translation_cache = defaultdict(dict)
logger = logging.getLogger(__name__)
@client.event
async def on_raw_reaction_add(payload:discord.RawReactionActionEvent):
    if payload.user_id == client.user.id:
        return

    guild = client.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    logger.info("found emoji reaction")
    if channel:
        message = await channel.fetch_message(payload.message_id)
        user = guild.get_member(payload.user_id) or await guild.fetch_member(payload.user_id)

        
        poll_info = database.get_poll_by_message_id(guild.id, channel.id, message.id)
        if poll_info:

            emoji_to_option = {
                "1️⃣": 0, "2️⃣": 1, "3️⃣": 2, "4️⃣": 3, "5️⃣": 4,
                "6️⃣": 5, "7️⃣": 6, "8️⃣": 7, "9️⃣": 8, "🔟": 9
            }
            if str(payload.emoji) in emoji_to_option:
                poll_id = poll_info[4]
                option_index = emoji_to_option[str(payload.emoji)]

                database.increment_vote(poll_id, option_index)
    
    language = database.check_translation_emoji(payload.guild_id,payload.emoji.id)
    
    emoji = str(payload.emoji)
    custom_emoji = payload.emoji.id if hasattr(payload.emoji, "id") else None

    if custom_emoji:
        language = database.check_translation_emoji(payload.guild_id, custom_emoji)
    else:
        language = database.check_translation_emoji(payload.guild_id, emoji)


    if language:
            logger.info(f"found emoji language {language}")
            filtered_text = re.sub(r'@everyone|@here', '', message.content)
            if message.flags.value == 2:
                # Cache the translated message for announcements
                if payload.message_id in announcement_translation_cache and language in announcement_translation_cache[payload.message_id]:
                    translated_text = announcement_translation_cache[payload.message_id][language]
                    translated_embeds = announcement_translation_cache[payload.message_id].get(f"{language}_embeds", [])
                else:
                    translated_text = await tr_roles_and_emojies(filtered_text, language) if message.content and filtered_text else None
                    translated_embeds = []

                    if message.embeds:
                        for embed in message.embeds:
                            translated_embed = Embed(
                                title=await tr_roles_and_emojies(embed.title, language) if embed.title else None,
                                description=await tr_roles_and_emojies(embed.description, language) if embed.description else None,
                                color=embed.color
                            )
                            for field in embed.fields:
                                translated_embed.add_field(
                                    name=await tr_roles_and_emojies(field.name, language),
                                    value=await tr_roles_and_emojies(field.value, language),
                                    inline=field.inline
                                )
                            translated_embeds.append(translated_embed)

                    # Cache both text and embed translations
                    announcement_translation_cache[payload.message_id][language] = translated_text
                    announcement_translation_cache[payload.message_id][f"{language}_embeds"] = translated_embeds

                try:
                    if translated_text:
                        await user.send(f"**Translated message from {channel.mention}:**\n{translated_text}")
                    if translated_embeds:
                        await user.send(embeds=translated_embeds)
                except discord.Forbidden:
                    print(f"Could not send DM to {user.name}.")
            else:
                if str(emoji) in [str(r.emoji) for r in message.reactions]:
                    reaction = discord.utils.get(message.reactions, emoji=emoji)
                    reaction_count = reaction.count if reaction else 0

                    if reaction_count == 1:
                        translated_text = await tr_roles_and_emojies(filtered_text, language) if message.content and filtered_text else None
                        translated_embeds = []

                        if message.embeds:
                            for embed in message.embeds:
                                translated_embed = Embed(
                                    title=await tr_roles_and_emojies(embed.title, language) if embed.title else None,
                                    description=await tr_roles_and_emojies(embed.description, language) if embed.description else None,
                                    color=embed.color
                                )
                                for field in embed.fields:
                                    translated_embed.add_field(
                                        name=await tr_roles_and_emojies(field.name, language),
                                        value=await tr_roles_and_emojies(field.value, language),
                                        inline=field.inline
                                    )
                                translated_embeds.append(translated_embed)

                        # Send translated text and embeds separately
                        if translated_text:
                            sent_message = await channel.send(f"**{user.mention}, here's the translation:\n**{translated_text}",reference=message)
                            database.add_message_ignore(message.guild.id,sent_message.id)
                        if translated_embeds:
                            sent_message = await channel.send(embeds=translated_embeds,reference=message)
                            database.add_message_ignore(message.guild.id,sent_message.id)
        