import requests
import deepl
import discord
from client import client
import os
import asyncio
from discord_webhook import DiscordWebhook
import dotenv
from io import BytesIO
from database import database
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
import aiohttp
import re

dotenv.load_dotenv()
DEEPL_API_KEY = os.getenv('DEEPL_TOKEN')


class RateLimitedQueue:
    def __init__(self, max_retries=3, retry_delay=2):
        self.queue = asyncio.Queue()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.lock = asyncio.Lock()

    async def add_to_queue(self, item):
        await self.queue.put(item)
        await self.process_queue()

    
    async def process_queue(self):
        async with self.lock:
            while not self.queue.empty():
                item = await self.queue.get()
                success = await self.send_with_retries(item)
                if not success:
                    await self.queue.put(item)
    
    async def send_with_retries(self, item):
        url, username, avatar_url, content ,image = item
        retries = 0
        while retries < self.max_retries:
            try:
                webhook = DiscordWebhook(url=url, username=username, avatar_url=avatar_url)
                try:
                    if image:
                        # Download the image
                        image_url = image.url
                        response = requests.get(image_url)
                        response.raise_for_status()  # Ensure we got a successful response
                        
                        image_bytes = BytesIO(response.content)
                except:
                    image = None
                try:
                    if image:
                        webhook.add_file(file=image_bytes, filename=image.filename)
                except:
                    pass
                webhook.content = content
                webhook.execute()
                logger.info(f"Message sent to webhook: {url}")
                return True
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit error
                    retry_after = int(e.response.headers.get('Retry-After', 1))
                    logger.warning(f"Rate limited. Retrying in {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                else:
                    logger.error(f"Error sending webhook: {e}")
                    return False
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return False
            retries += 1
            await asyncio.sleep(self.retry_delay)

queue = RateLimitedQueue()

def translate_text(text,source_lang, target_lang):
    try:
        if text == "":
            return text
        if not DEEPL_API_KEY:
            raise ValueError("DeepL API key not found in environment variables.")
        translator = deepl.Translator(DEEPL_API_KEY)
        source_lang = "EN" if source_lang == "EN-US" else source_lang
        result = translator.translate_text(text,source_lang=source_lang, target_lang=target_lang)
        translated_text = result.text
        logger.info(f"Translated text: '{translated_text}' ({target_lang})")
        return translated_text
    except deepl.exceptions.DeepLException as e:
        logger.error(f"DeepL API error: {e}")
    except Exception as e:
        logger.error(f"Error translating: {e}")
    return None

async def resend_message_with_webhook(webhook_url, username, avatar_url, content, image_url=None):
    await queue.add_to_queue((webhook_url, username, avatar_url, content, image_url))
    



async def translator_func(message: discord.Message):
    try:
        
        current_channel = database.get_translation_channel_by_channel(message.guild.id, message.channel.id)
        
        if not current_channel:
            return

        _, guild_id, current_channel_id, current_language, channel_link_id, _ = current_channel

        grouped_channels = database.get_translation_channel_by_link_id(message.guild.id, channel_link_id)

        if not grouped_channels:
            logger.info(f"No linked channels found for channel group: {channel_link_id}")
            return

        message_attachment = message.attachments[0] if message.attachments else None

        channel_mentions = re.findall(r'<#(\d+)>', message.content)

        for entry in grouped_channels:
            _, guild_id, channel_id, channel_language, channel_link_id, channel_webhook = entry

            if channel_id == current_channel_id: 
                continue
            translated_text = ""
            translated_text = message.content  
            try:
                for mention in channel_mentions:
                    mentioned_channel_id = int(mention)
                    mention_translation_settings = database.get_translation_channel_by_channel(guild_id,mentioned_channel_id)
                    if mention_translation_settings:
                        corresponding_channel_settings = database.get_corresponding_channel_by_link_id(mentioned_channel_id,mention_translation_settings[4],channel_language,message.guild.id)
                        print(corresponding_channel_settings)
                        if corresponding_channel_settings:
                            translated_text = translated_text.replace(f"<#{mentioned_channel_id}>", f"<#{corresponding_channel_settings}>")
                        else:
                            logger.info(f"No corresponding channel found for mention: <#{mentioned_channel_id}>")
                translated_text = await replace_forum_and_thread_mentions(translated_text,guild_id,channel_language)
            except Exception as e:
                import traceback; traceback.print_exc();
                print(e)
            try:
                translated_text = translate_text(translated_text, source_lang=current_language, target_lang=channel_language)
            except:
                pass
            if translated_text:
                message_parts = split_message_into_parts(translated_text, 2000)
                for i, part in enumerate(message_parts):
                    # Send attachment only with the last part
                    if i == len(message_parts) - 1:
                        await resend_message_with_webhook(
                            channel_webhook, 
                            message.author.display_name, 
                            message.author.display_avatar.url, 
                            part, 
                            message_attachment  # Include attachment in the last message
                        )
                    else:
                        await resend_message_with_webhook(
                            channel_webhook, 
                            message.author.display_name, 
                            message.author.display_avatar.url, 
                            part, 
                            None  # No attachment for the earlier parts
                        )
            elif message_attachment:
                await resend_message_with_webhook(
                            channel_webhook, 
                            message.author.display_name, 
                            message.author.display_avatar.url, 
                            None, 
                            message_attachment  # Include attachment in the last message
                        )
        
    except Exception as e:
        logger.error(f"Error in translator_func: {e}")

def split_message_into_parts(text: str, max_length: int):
    """
    Splits the message into smaller parts, keeping words intact and respecting max_length.
    """
    parts = []
    
    while len(text) > max_length:
        # Find the last space before the max_length limit
        split_index = text.rfind(' ', 0, max_length)
        
        # If no space is found, force split at max_length
        if split_index == -1:
            split_index = max_length
        
        # Add the chunk to the list of parts
        part = text[:split_index].strip()
        parts.append(part)
        
        # Remove the chunk from the text and continue
        text = text[split_index:].strip()
    
    # Append the last remaining part
    if text:
        parts.append(text)
    
    return parts
async def translator_func_announcement(message: discord.Message):
    try:
        # Check if the message comes from an announcement (news) channel
        if message.channel.type == discord.ChannelType.news:
            logger.info(f"Processing message from an announcement channel: {message.channel.name}")
        
        # Retrieve translation settings from the database
        current_channel = database.get_translation_channel_by_channel(message.guild.id, message.channel.id)
        
        if not current_channel:
            return

        _, guild_id, current_channel_id, current_language, channel_link_id, _ = current_channel

        # Get all channels linked for translation
        grouped_channels = database.get_translation_channel_by_link_id(message.guild.id, channel_link_id)

        if not grouped_channels:
            logger.info(f"No linked channels found for channel group: {channel_link_id}")
            return

        message_attachment = message.attachments[0] if message.attachments else None
        channel_mentions = re.findall(r'<#(\d+)>', message.content)

        # Iterate over linked channels and translate message
        for entry in grouped_channels:
            _, guild_id, channel_id, channel_language, channel_link_id, channel_webhook = entry

            if channel_id == current_channel_id:
                continue

            # Handle text translation
            translated_text = message.content

            for mention in channel_mentions:
                mentioned_channel_id = int(mention)
                mention_translation_settings = database.get_translation_channel_by_channel(guild_id, mentioned_channel_id)
                if mention_translation_settings:
                    corresponding_channel_settings = database.get_corresponding_channel_by_link_id(mentioned_channel_id, mention_translation_settings[4], channel_language, message.guild.id)
                    if corresponding_channel_settings:
                        translated_text = translated_text.replace(f"<#{mentioned_channel_id}>", f"<#{corresponding_channel_settings}>")
            translated_text = translate_text(translated_text, source_lang=current_language, target_lang=channel_language)
            translated_embeds = []
            if message.embeds:
                for embed in message.embeds:
                    new_embed = discord.Embed(
                        title=translate_text(embed.title, current_language, channel_language) if embed.title else None,
                        description=translate_text(embed.description, current_language, channel_language) if embed.description else None,
                        color=embed.color
                    )

                    for field in embed.fields:
                        translated_name = translate_text(field.name, current_language, channel_language)
                        translated_value = translate_text(field.value, current_language, channel_language)
                        new_embed.add_field(name=translated_name, value=translated_value, inline=field.inline)

                    if embed.footer:
                        new_embed.set_footer(text=translate_text(embed.footer.text, current_language, channel_language))

                    if embed.image:
                        new_embed.set_image(url=embed.image.url)

                    translated_embeds.append(new_embed)

            channel = message.guild.get_channel(channel_id)

            if channel:
                try:
                    # Try sending the message with embeds and attachment first
                    if translated_embeds:
                        if message_attachment:
                            file = await message_attachment.to_file()  # Convert the attachment to a discord.File
                            await channel.send(content=translated_text, embeds=translated_embeds, file=file)
                        else:
                            await channel.send(content=translated_text, embeds=translated_embeds)
                    else:
                        if message_attachment:
                            file = await message_attachment.to_file()  # Convert the attachment to a discord.File
                            await channel.send(content=translated_text, file=file)
                        else:
                            await channel.send(content=translated_text)
                except Exception as e:
                    logger.error(f"Error sending message to channel {channel_id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())

                    # Attempt to send again without embeds or attachment
                    try:
                        if translated_embeds:
                            await channel.send(content=translated_text, embeds=translated_embeds)
                        else:
                            await channel.send(content=translated_text)
                    except Exception as resend_error:
                        logger.error(f"Failed to resend message without attachment or embeds: {resend_error}")
                        # Optional: Log or handle the final failure if needed
            
            
    except Exception as e:
        logger.error(f"Error in translator_func_announcement: {e}")


async def replace_forum_and_thread_mentions(content: str, guild_id: int, target_language: str):
    mentions = re.findall(r'<#(\d+)>', content)
    corresponding_forum = None
    if mentions:
        for mention in mentions:
            mention_id = int(mention)
            thread_settings = database.get_translation_thread_by_thread_id(guild_id,mention_id)
            if thread_settings:
                cross_data = database.get_corresponding_thread_by_link_id(thread_settings[4], target_language, guild_id)
                if cross_data:
                    cross_furom,parent_channel_id = cross_data
                    
                    if cross_furom == 0 and parent_channel_id != None and cross_furom != None:
                        corresponding_forum = parent_channel_id
                    else:
                        corresponding_forum = cross_furom
                    if corresponding_forum:
                        content = content.replace(f"<#{mention_id}>", f"<#{corresponding_forum}>")
                    else:
                        logger.info(f"No corresponding forum found for mention: <#{mention_id}>")
        
    return content



async def translator_func_threads(message: discord.Message):
    
    try:
        current_channel = database.get_translation_thread_by_channel_and_thread_id(message.guild.id, message.channel.parent_id,message.channel.id)

        print(current_channel)
        if not current_channel:
            logger.info(f"didn't find anything for the channel {message.channel.id}")
            return
        current_channel = current_channel[0]
        _, _, current_channel_id,thread_id, thread_link_id, current_language, _ = current_channel


        grouped_channels = database.get_translation_thread_by_link_id(message.guild.id, thread_link_id)

        if not grouped_channels:
            logger.info(f"No linked channels found for channel group: {thread_link_id}")
            return

        message_attachment = message.attachments[0] if message.attachments else None

        channel_mentions = re.findall(r'<#(\d+)>', message.content)

        # Translate and send the message to each channel in the group (except the current one)
        for entry in grouped_channels:

            _, _, channel_id,thread_id,thread_link_id, channel_language, channel_webhook = entry

            
            if channel_id == current_channel_id: 
                continue
            
            if thread_id == 0:
                continue
            
            

            
            translated_text = translate_text(message.content,source_lang=current_language, target_lang=channel_language)
            translated_text = await replace_forum_and_thread_mentions(translated_text,message.guild.id,channel_language)
            for mention in channel_mentions:
                mentioned_channel_id = int(mention)
                mention_translation_settings = database.get_translation_channel_by_channel(message.guild.id, mentioned_channel_id)
                if mention_translation_settings:
                    corresponding_channel_settings = database.get_corresponding_channel_by_link_id(mentioned_channel_id, mention_translation_settings[4], channel_language, message.guild.id)
                    if corresponding_channel_settings:
                        translated_text = translated_text.replace(f"<#{mentioned_channel_id}>", f"<#{corresponding_channel_settings}>")
                        
            if translated_text:
                await send_to_threads_with_webhooks(channel_webhook, message.author.display_name, message.author.display_avatar.url, translated_text, message_attachment,thread_id)

    except Exception as e:
        logger.error(f"Error in translator_func_thread: {e}")
        import traceback; traceback.print_exc();






async def send_to_threads_with_webhooks(url, username, avatar_url, content ,image,thread_id):
    try:
        webhook = DiscordWebhook(url=url, username=username, avatar_url=avatar_url,thread_id=thread_id)
        try:
            if image:
                # Download the image
                image_url = image.url
                response = requests.get(image_url)
                response.raise_for_status()  # Ensure we got a successful response
                
                image_bytes = BytesIO(response.content)
        except:
            image = None
        try:
            if image:
                webhook.add_file(file=image_bytes, filename=image.filename)
        except:
            pass
        webhook.content = content
        webhook.execute()
        logger.info(f"Message sent to webhook: {url}")
        return True
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:  # Rate limit error
            retry_after = int(e.response.headers.get('Retry-After', 1))
            logger.warning(f"Rate limited. Retrying in {retry_after} seconds...")
            await asyncio.sleep(retry_after)
        else:
            logger.error(f"Error sending webhook: {e}")
            return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False



async def send_to_threads_with_webhooks_with_multiple_files(url, username, avatar_url, content, files, thread_id):
    try:
        webhook = DiscordWebhook(url=url, username=username, avatar_url=avatar_url, thread_id=thread_id)

        # Split content into parts while respecting word boundaries
        max_content_length = 2000
        parts = []

        while len(content) > max_content_length:
            # Find the last space within the limit
            last_space = content.rfind(' ', 0, max_content_length)
            if last_space == -1:  # If no space is found, split at max_content_length
                last_space = max_content_length

            parts.append(content[:last_space].strip())
            content = content[last_space:].strip()

        # Add the remaining content
        if content:
            parts.append(content)

        # Handle each part
        for i, part in enumerate(parts):
            # Set the content for the current part
            webhook.content = part
            
            # If it's the last part, add files
            if i == len(parts) - 1:
                # Handle each file (including images)
                for file in files:
                    try:
                        file_url = file.url  # Ensure this is the correct way to get the URL
                        async with aiohttp.ClientSession() as session:
                            async with session.get(file_url) as response:
                                response.raise_for_status()  # Ensure we got a successful response
                                file_bytes = BytesIO(await response.read())  # Read the response content as bytes
                        
                        webhook.add_file(file=file_bytes, filename=file.filename)

                    except Exception as e:
                        logger.error(f"Error processing file {file.filename}: {e}")

            # Execute the webhook
            webhook.execute()
            logger.info(f"Message part sent to webhook: {url}")

        return True

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    
    

async def translate_all_messages_in_thread(thread: discord.Thread, current_language: str, grouped_channels: list):
    try:
        async for message in thread.history(limit=None):  # Fetch all messages in the thread
            if message.author.bot:
                continue  # Skip messages sent by bots
            
            message_attachment = message.attachments[0] if message.attachments else None
            channel_mentions = re.findall(r'<#(\d+)>', message.content)
            
            # Iterate over grouped channels and send translated messages
            for entry in grouped_channels:
                _, _, channel_id, thread_id, thread_link_id, channel_language, channel_webhook = entry
                
                # Skip current channel or channels without threads
                if channel_id == thread.id or thread_id == 0:
                    continue

                # Translate the message content
                translated_text = translate_text(message.content, source_lang=current_language, target_lang=channel_language)
                translated_text = await replace_forum_and_thread_mentions(translated_text, message.guild.id, channel_language)

                # Handle mentions translation
                for mention in channel_mentions:
                    mentioned_channel_id = int(mention)
                    mention_translation_settings = database.get_translation_channel_by_channel(message.guild.id, mentioned_channel_id)
                    if mention_translation_settings:
                        corresponding_channel_settings = database.get_corresponding_channel_by_link_id(
                            mentioned_channel_id, mention_translation_settings[4], channel_language, message.guild.id)
                        if corresponding_channel_settings:
                            translated_text = translated_text.replace(f"<#{mentioned_channel_id}>", f"<#{corresponding_channel_settings}>")

                # Send the translated message via webhook
                if translated_text:
                    await send_to_threads_with_webhooks(channel_webhook, message.author.display_name, message.author.display_avatar.url, translated_text, message_attachment, thread_id)

    except Exception as e:
        logger.error(f"Error in translating messages in thread {thread.id}: {e}")
        import traceback
        traceback.print_exc()



def get_first_n_words(text, n=10):
    """Extract the first N words from the text."""
    words = text.split()[:n]  # Split and grab the first N words
    return ' '.join(words)

async def tr_roles_and_emojies(text,target_lang):
    try:
        if text == "":
            return text
        if not DEEPL_API_KEY:
            raise ValueError("DeepL API key not found in environment variables.")
        translator = deepl.Translator(DEEPL_API_KEY)
        result = translator.translate_text(text, target_lang=target_lang)
        translated_text = result.text
        logger.info(f"Translated text: '{translated_text}' ({target_lang})")
        return translated_text
    except deepl.exceptions.DeepLException as e:
        logger.error(f"DeepL API error: {e}")
    except Exception as e:
        logger.error(f"Error translating: {e}")
    return None
