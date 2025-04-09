import discord
from client import client
from database import database
from resources.translation_functions import translate_text
import pytz
import datetime

@client.event
async def on_thread_create(thread:discord.Thread):
    try:
        guild_id = thread.guild.id
        channel_id = database.log_retrieve(guild_id, "thread_created")
        if channel_id:
            embed = create_embed(f"Thread {thread.name} created.", thread, discord.Color.green(),client)
            await thread.guild.get_channel(channel_id).send(embed=embed)
    except:
        pass
    

    
    
        
def create_embed(description, member, color, client):
    embed = discord.Embed(
        description=description,
        color=color
    )
    # Fallback values
    
    if hasattr(member, 'display_avatar'):
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    
    timezone = pytz.timezone("America/Chicago")

    # Get the current time in the server's timezone
    current_time = datetime.datetime.now(timezone).strftime('%m/%d/%Y %I:%M %p')

    embed.set_footer(text=f"Winston - {current_time}", icon_url=client.user.avatar.url)
    return embed


async def translate(thread):
    
    if thread.owner.id == client.user.id:
        return
    parent_channel = thread.parent
    guild_id = thread.guild.id
    parent_channel_id = parent_channel.id

    parent_translation = database.get_translation_thread_by_channel_and_thread_id(guild_id, parent_channel_id, 0)

    if not parent_translation:

        print(f"No translation settings for parent channel {parent_channel_id} in guild {guild_id}")
        return

    if thread.starter_message:
        thread_message = thread.starter_message.content
    else:
        thread_message = None
        if isinstance(parent_channel, discord.ForumChannel):
            # Fetch the first message if the thread starter message is not directly accessible
            try:
                first_message = await thread.fetch_message(thread.id)  # Fetch the thread's first message
                thread_message = first_message.content
            except discord.NotFound:
                print(f"Starter message for thread {thread.id} not found.")
        else:
            if thread.starter_message:
                thread_message = thread.starter_message.content

    print(f"Start message content: {thread_message}")
    thread_link_id = parent_translation[0][4] 
    thread_language = parent_translation[0][5]
    webhook_link = parent_translation[0][6]
    parent_translations_with_same_link_id = database.get_translation_thread_by_link_id(guild_id, thread_link_id)

    next_link_id = database.get_next_available_link_id(guild_id)
    database.set_threads_translation(
        guild_id=guild_id,
        parent_channel_id=parent_channel_id,
        thread_id=thread.id,
        thread_link_id=next_link_id,
        language=thread_language,
        webhook_link=webhook_link
    )
    print(f"Created and saved thread {thread.id} in parent channel {parent_channel_id} with language {thread_language}.")

    for parent_translation_entry in parent_translations_with_same_link_id:
        try:
            if parent_translation_entry[3] != 0:
                continue
            
            parent_channel_id = parent_translation_entry[2]  
            language = parent_translation_entry[5] 
            webhook_link = parent_translation_entry[6] 
            parent_channel_tr = thread.guild.get_channel(parent_channel_id)

            existing_thread = discord.utils.get(parent_channel_tr.threads, id=thread.id)
            if existing_thread:
                print(f"Thread {existing_thread.id} already exists.")
                continue
            translated_thread_name = translate_text(thread.name,thread_language,language)
            translated_thread_message = translate_text(thread_message,thread_language,language) if thread_message else None
            if isinstance(parent_channel_tr, discord.ForumChannel):
                try:
                    new_thread = await parent_channel_tr.create_thread(
                        name=translated_thread_name,
                        content=translated_thread_message
                    )
                    database.set_threads_translation(
                        guild_id=guild_id,
                        parent_channel_id=parent_channel_id,
                        thread_id=new_thread.thread.id,
                        thread_link_id=next_link_id,
                        language=language,
                        webhook_link=webhook_link
                    )
                    print(f"Created and saved thread {new_thread.thread.id} in parent channel {parent_channel_id} with language {language}.")
                except discord.HTTPException as e:
                    print(f"Failed to create thread in forum channel {parent_channel_id}: {e}")
                    continue
            else:
                
                try:
                    new_thread = await parent_channel_tr.create_thread(
                        name=translated_thread_name,
                        type=discord.ChannelType.public_thread
                    )
                    database.set_threads_translation(
                        guild_id=guild_id,
                        parent_channel_id=parent_channel_id,
                        thread_id=new_thread.id,
                        thread_link_id=next_link_id,
                        language=language,
                        webhook_link=webhook_link
                    )
                    print(f"Created and saved thread {new_thread.id} in parent channel {parent_channel_id} with language {language}.")
                except discord.HTTPException as e:
                    print(f"Failed to create thread in regular channel {parent_channel_id}: {e}")
                    continue
        except:
            import traceback; traceback.print_exc();
            continue
    
    