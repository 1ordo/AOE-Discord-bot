import discord
from proto import MESSAGE
from client import client
from database import database
from resources.translation_functions import translator_func,translator_func_threads,translator_func_announcement,tr_roles_and_emojies
import re
from discord import MessageFlags
import google.generativeai as genai
import os
import json
import asyncio
from resources.ai_functions import ai_function , reply_with_ai
import discord_webhook
from discord_webhook import DiscordWebhook



@client.event
async def on_message(message: discord.Message):
    
    if client.user in message.mentions or ((message.reference and message.reference.resolved and message.reference.resolved.author.id == client.user.id) and ( message.reference and message.reference.resolved.author.id != message.author.id)):
        defaults = database.check_defaults(message.guild.id)    
        ai_category_id = None
        if defaults:
            _, _, _, ai_category_id, _ = defaults
        if message.channel and (message.channel.category_id != ai_category_id or (ai_category_id is None and message.channel.category_id is None)):
            if message.reference:   
                if database.check_message_ignore(message.guild.id,message.reference.resolved.id):
                    return
                if message.reference.resolved.author.id == message.author.id:
                    return
                if message.author.id == client.user.id:
                    return
            elif client.user in message.mentions and message.author.id == client.user.id:
                return
            
            print("winston got mentioned and generating a reply..")
            
            response = await reply_with_ai(message.channel, client, message)
            try:
                if len(response) > 2000:
                    # Split at closest markdown-safe boundary before 2000 chars
                    chunks = []
                    while response:
                        if len(response) <= 2000:
                            chunks.append(response)
                            break
                        # Find last occurrence of common markdown boundaries
                        split_index = max(
                            response[:2000].rfind('\n\n'),
                            response[:2000].rfind('. '),
                            response[:2000].rfind('! '),
                            response[:2000].rfind('? ')
                        )
                        if split_index == -1:
                            split_index = 2000
                        chunks.append(response[:split_index])
                        response = response[split_index:].lstrip()
                    
                    for i, chunk in enumerate(chunks):
                        if i == 0:
                            sent_message = await message.channel.send(content=chunk, reference=message)
                        else:
                            sent_message = await message.channel.send(content=chunk)
                else:
                    sent_message = await message.channel.send(content=response, reference=message)
            except:
                # If the message couldn't be sent, send an error message
                await message.channel.send("I couldn't send the message. Its probably an issue in my side! i'm still being developed!", delete_after=5)

        

    if client.user.id != message.author.id:
        if message.author.bot:
                return
        if message.content.lower() == "translate":

            if message.reference and isinstance(message.reference.resolved, discord.Message):
                
                original_message = message.reference.resolved
                user_roles = message.author.roles
                if user_roles:
                    for user_role in user_roles:
                        user_role_id = user_role.id 
                        language = database.check_translation_language_with_role(message.guild.id, user_role_id)
                        if language:
                            filtered_text = re.sub(r'@everyone|@here', '', original_message.content)
                            print("filtered_text: ",filtered_text)
                            translated_text = await tr_roles_and_emojies(filtered_text,language)
                            
                            if translated_text:
                                ## await translate_roles_with_webhooks(translated_text,original_message,message,language)
                                max_length = 1950
                                chunks = [translated_text[i:i+max_length] for i in range(0, len(translated_text), max_length)]
                                
                                # Send each chunk separately via the webhook
                                for idx, chunk in enumerate(chunks):
                                    # Add a note to indicate if it's part of a split message
                                    if idx == 0:
                                        content = f"{message.author.mention} - {language}\n{chunk}"
                                    else:
                                        content = f"{chunk}"
                                    sent_message = await message.channel.send(content=content, reference=original_message, mention_author=False)
                                    database.add_message_ignore(message.guild.id,sent_message.id)
            else:
                await message.channel.send("you need to reply to a message to use the translate function",delete_after=5,reference=message)
                    
        if isinstance(message.channel, discord.Thread) or isinstance(message.channel,discord.ForumChannel):
            if message.author.bot:
                return
            await translator_func_threads(message)
        elif message.webhook_id:
            if message.author.bot and not message.webhook_id:
                return
            if message.flags.value == 2:
                print("This message was crossposted from an announcement channel")
                await translator_func_announcement(message)
        else:
            if message.author.bot:
                return
            await translator_func(message)
        await ai_function(message)


def extract_webhook_ids(webhook_urls):
    webhook_ids = []
    for webhook_url in webhook_urls:
        match = re.search(r"https://discord\.com/api/webhooks/(\d+)/", webhook_url)
        if match:
            webhook_ids.append(match.group(1))
    return webhook_ids



async def translate_roles_with_webhooks(translated_text,original_message,message,language):
    webhooks = await message.channel.webhooks()
    if webhooks:
        webhook = webhooks[0]  # Use the first webhook found
        url = webhook.url
    else:
        # No webhooks found, create a new one
        new_webhook = await message.channel.create_webhook(name="Translate Roles Webhook")
        url = new_webhook.url
    webhook = DiscordWebhook(url=url, username=original_message.author.display_name, avatar_url=original_message.author.display_avatar.url)
    max_length = 1950
    chunks = [translated_text[i:i+max_length] for i in range(0, len(translated_text), max_length)]
    
    # Send each chunk separately via the webhook
    for idx, chunk in enumerate(chunks):
        # Add a note to indicate if it's part of a split message
        if idx == 0:
            content = f"{message.author.mention} - {language}\n{chunk}"
        else:
            content = f"{chunk}"
        
        webhook.content = content
        webhook.execute()  


