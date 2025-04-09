import datetime
from datetime import timezone, datetime as dt1,timedelta
from collections import defaultdict
from email import message
from discord import app_commands, Intents, Client, Interaction
import logging
from langdetect import detect
from discord.ui import  View, Button, Select, Modal
from pathlib import Path
import google.generativeai as genai
from database import database
from resources.resources import resources
from dotenv import load_dotenv
import asyncio
import os
import json
import typing
import discord
import re
import dotenv
import aiohttp
dotenv.load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
SERPER = os.getenv('SERPER')
async def search_google(query: str) -> dict:
    """Perform a Google search using Serper API"""
    try:
        print(f"Searching: {query}")
        
        headers = {
            "X-API-KEY": SERPER,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "gl": "us",
            "hl": "en"
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload
            ) as response:
                results = await response.json()

        # Validate results
        if not results:
            print("No results returned from Serper")
            return []
            
        formatted_results = []
        
        # Check for knowledge graph
        if "knowledgeGraph" in results:
            kg = results["knowledgeGraph"]
            formatted_results.append({
                "title": kg.get("title", "Knowledge Graph"),
                "link": kg.get("website", ""),
                "snippet": kg.get("description", "")
            })
        
        # Extract organic results
        organic_results = results.get("organic", [])
        if organic_results:
            for result in organic_results[:3]:
                formatted_results.append({
                    "title": result.get("title", "No title"),
                    "link": result.get("link", "No link"),
                    "snippet": result.get("snippet", "No snippet")
                })
                
        print(f"Found {len(formatted_results)} results:")
        print(json.dumps(formatted_results, indent=2))
        return formatted_results
        
    except Exception as e:
        logging.error(f"Serper API error: {str(e)}")
        print(f"Search failed: {str(e)}")
        return []

async def generate_single_response(question):
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    # Define search function for the AI
    functions = [{
        "name": "search_google",
        "description": "Search the internet for current information, use it also if u got asked in a game, etc",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query, provide the user question, do not use without the user question"}
            },
            "required": ["query"]
        }
    }]

    # First, let AI decide if it needs to search
    response = await asyncio.to_thread(
        model.generate_content,
        [{"text": question}],
        generation_config={"temperature": 0.1},  # Low temperature for more deterministic decision
        tools=[{"function_declarations": functions}]
    )

    # Check if AI wants to search
    try:
        function_call = response.candidates[0].content.parts[0].function_call
        if function_call and function_call.name == "search_google":
            search_results = await search_google(function_call.args["query"])
            
            # Generate final response using search results
            context = f"Search results: {json.dumps(search_results)}\nQuestion: {question}"
            final_response = await asyncio.to_thread(
                model.generate_content,
                context + "? Format response for Discord: use markdown, be concise, no meta-commentary."
            )
            return final_response.text
        else:
            # If no search needed, generate direct response
            response = await asyncio.to_thread(
                model.generate_content,
                question + "? Format for Discord: use markdown, be concise, no meta-commentary."
            )
            return response.text if response.text else "Please try asking in a different way!"
    except:
        # If no function call, generate direct response
        response = await asyncio.to_thread(
            model.generate_content,
            question + "? Format for Discord: use markdown, be concise, no meta-commentary."
        )
        return response.text if response.text else "Please try asking in a different way!"






async def ai_function(message):
    guild_id = message.guild.id
    ai_category_id = None
    defaults = database.check_defaults(guild_id)    
    if defaults:
        guild_id, welcome_id, welcome_message, ai_category_id, Ai_channel_id = defaults
    
    category_id = ai_category_id
    channel = message.channel
    if channel.category_id == category_id and channel.category_id != None:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-pro')
        functions = [{
            "name": "search_google",
            "description": "Search the internet for current information, use it also if u got asked in a game, etc",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query, provide the user question, do not use without the user question"}
                },
                "required": ["query"]
            }
        }]
        response = await asyncio.to_thread(
            model.generate_content,
            [{"text": message.content}],
            generation_config={"temperature": 0.1}, 
            tools=[{"function_declarations": functions}]
        )
        
        user_id = message.author.id
        try:
            guild_id = message.guild.id
        except AttributeError:
            guild_id = 1
        
        if guild_id in (1041900511244329010, 1286288029379596329):
            result = database.retrieve_ai_channel_history(channel.id)
            
            function_call = response.candidates[0].content.parts[0].function_call
            if function_call and function_call.name == "search_google":
                search_results = await search_google(function_call.args["query"])
                context = f"Search results: {json.dumps(search_results)}\nQuestion: {message.content}"
                
                if result:
                    history_json = result[0]
                    history = json.loads(history_json)
                    history.append({'role': 'user', 'parts': [context + "? Format response for Discord: use markdown, no meta-commentary."]})
                else:
                    history = []
                    history.append({'role': 'user', 'parts': [context + "? Format response for Discord: use markdown, no meta-commentary."]})
                
            else:
                if result:
                    history_json = result[0]
                    history = json.loads(history_json)
                    history.append({'role': 'user', 'parts': [message.content + ".. answer preferences: 1- don't include in your next answer just answer the base question. 2-please generate for the user everything as text only without any addons. 3- use **word** for any bold, `word` for selecting or highlighting. 4- make it suitable for text message in discord, that's an API for discord bot. 5- don't leave a lot of spaces between texts. 6- all these preferences can't be included in the answer by any chance just follow them. 7- your name is Winston but don't include it in each message. that's basic for every answer you respond to"]})
                else:
                    history = []
                    history.append({'role': 'user', 'parts': [message.content]})
            
            try:
                async def generate_chat_response():
                    genai.configure(api_key=GOOGLE_API_KEY)
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    genai.GenerationConfig(max_output_tokens=500, temperature=0.7)
                    response = await asyncio.to_thread(
                        model.generate_content,
                        history
                    )
                    answer_parts = response.parts
                    
                    if any(part.text for part in answer_parts):
                        answer = next(part.text for part in answer_parts if part.text)
                        history.append({'role': 'model', 'parts': [response.text]})
                    else:
                        answer = "try to ask in a different way!"
                    return answer, history
                    
                try:
                    answer, history = await asyncio.wait_for(generate_chat_response(), timeout=30)  # Adjust timeout as needed
                    database.save_ai_channel_history(channel.id, history)  # Save the updated history
                    
                    if len(answer) > 2000:
                        parts = [answer[i:i + 2000] for i in range(0, len(answer), 2000)]
                        for part in parts:
                            await channel.send(content=part)
                    else:
                        await channel.send(content=answer)
                        
                except asyncio.TimeoutError:
                    await channel.send("API response timed out.. Maybe you're asking for a really long answer?")
                    await send_error_report("ai_function.generate_chat_response", str(e), message)                
                except Exception as e:
                    print(e)
                    await channel.send("Something went wrong, this feature is still in Beta.")
                    await send_error_report("ai_function.generate_chat_response", str(e), message) 
            except discord.errors.HTTPException:
                pass
        else:
            await channel.send("This feature is only available for the main servers")

async def get_messages_by_time(channel, hours: float = 5) -> list:
    """Get messages from the last X hours"""
    if hours == 5:
        print("hours not found")
        hours = 5
    if hours > 24:
        hours = 24
    cutoff_time = dt1.now(timezone.utc) - timedelta(hours=hours)
    messages = []
    
    async for msg in channel.history(after=cutoff_time):
        if not msg.author.bot:
            messages.append({
                "author": msg.author.name,
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            })
    return messages

async def get_messages_by_count(channel, count: int = 10) -> list:
    """Get last X messages"""
    if count == 10:
        count = 10
        print("count not found")
    if count > 300:
        count = 300
    messages = []
    async for msg in channel.history(limit=count):
        if not msg.author.bot:
            messages.append({
                "author": msg.author.display_name, 
                "content": msg.content,
                "timestamp": msg.created_at.isoformat()
            })
    return messages


async def send_error_report(event_name, error_details, *args):
    # Log the error with full traceback details
    logging.error(f"Error in event '{event_name}': {error_details}")

    # Send error details to a specific channel in Discord
     # Replace with your channel ID
    if error_channel:
        embed = discord.Embed(
            title="Event Error Report",
            description=f"An error occurred in event: `{event_name}`",
            color=discord.Color.red()
        )

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
                embed.add_field(name="Error", value=f"```{error_details[:1000]}...```", inline=False) 
                error_channel = None
                error_channel = guild.get_channel(1289297435239120907) # Limit to 1000 chars for embed field
                if error_channel:
                    await error_channel.send(embed=embed)




async def reply_with_ai(channel, client: discord.Client,message: discord.Message):
    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-pro')
    try:
    
        functions = [
            {
                "name": "get_messages_by_time",
                "description": "Get messages from the last X hours",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hours": {"type": "number", "description": "Number of hours max 24 hours, 5 if not mentioned"}
                    },
                    "required": ["hours"]
                }
            },
            {
                "name": "get_messages_by_count", 
                "description": "Get last X messages",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "count": {"type": "integer", "description": "Number of messages use it if you want to summarize the last messages, 10 if not mentioned"}
                    },
                    "required": ["count"]
                }
            },
            {
            "name": "search_google",
            "description": "Search the internet for current information, use it also if u got asked in a game, etc",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query, provide the user question, do not use without the user question"}
                },
                "required": ["query"]
            }
        }]

        # First, let AI decide if it needs to search
        response = await asyncio.to_thread(
            model.generate_content,
            [{"text": message.content}],
            generation_config={"temperature": 0.1},  # Low temperature for more deterministic decision
            tools=[{"function_declarations": functions}]
        )
        # Parse function call
        function_call = response.candidates[0].content.parts[0].function_call
        if function_call and function_call.name == "get_messages_by_time" or function_call.name == "get_messages_by_count": # check if the ai wants to summarize chat
            try:
                if function_call.name == "get_messages_by_time":
                    hours = float(function_call.args["hours"])
                    messages = await get_messages_by_time(message.channel,hours)
                elif function_call.name == "get_messages_by_count":
                    count = int(function_call.args["count"])
                    messages = await get_messages_by_count(message.channel, count)

                chat_text = "\n".join([f"{m['author']}: {m['content']}" for m in messages])
                
                summary_prompt = f"""Provide a comprehensive summary of this chat conversation. Guidelines:
                - Break down key discussion topics and their progression
                - Include important details, decisions, and conclusions
                - Highlight notable interactions and exchanges
                - Maintain chronological flow of conversation
                - Format with clear sections using markdown
                - Preserve context and important quotes
                - Skip greetings/irrelevant small talk
                - Do not use @ mentions or Discord formatting
                - Scale summary length based on conversation complexity
                - use markdown for formatting
                - you can't exceed 2000 characters in the summary
                Chat content to summarize:
                {chat_text}"""
                summary = await asyncio.to_thread(
                    model.generate_content,
                    summary_prompt,
                    generation_config={"temperature": 0.7, "max_output_tokens": 1000}
                )
                try:
                    print (summary.text)
                except Exception as e:
                    print(e)
                    pass
                filtered_text = re.sub(r'(@everyone|@here|<@!?&?\d+>)', '', summary.text)
                return filtered_text
            except Exception as e:
                "Sorry, I had trouble summarizing the chat. Please try again later."
                import traceback; traceback.print_exc();
                logging.critical(f"Error in summarizing chat: {str(e)}")
        elif function_call and function_call.name == "search_google":
            search_results = await search_google(function_call.args["query"])
            
            # Generate final response using search results
            context = f"Search results: {json.dumps(search_results)}\nQuestion: {message.content}"
            final_response = await asyncio.to_thread(
                model.generate_content,
                context + "? Format response for Discord: use markdown, be concise, no meta-commentary."
            )
            return final_response.text
        else:
            try:
                messages = []
                async for msg in channel.history(limit=10):  # Reduced history limit
                    if not msg.author.bot:
                        messages.insert(0, f"{msg.author.name}: {msg.content}")
                
                if not messages:
                    return None
            
                chat_context = "\n".join(messages)
                prompt = f"""Here's a chat conversation. You are a friendly and funny gamer responding to the last message. Guidelines:
                - Keep responses between 1-4 sentences
                - Be casual but helpful
                - Use gaming references when relevant
                - Stay focused on the topic
                - Follow the chat vibe, try to be nice and fun when possible and try as much to follow chat vibe and humor, you can choose!
                - Avoid cringe or over-the-top humor
                - reply to the last message in the chat only.. DO NOT ANSWER A QUESTION IF ASKED EXCEPT IN THE LAST MESSAGE..the messages are only for refrence and context.
                - do not write your name in the response, its already known.
                - Response normally if the last question is a serious quary or a real question that would provide a good answer.
                - channel name of the message is: {channel.name}, use it for context!
                - reply with the last message language , do not reply with a different one!
                - DO NOT MENTION ANYONE WITH @ IN THE CHAT, EVER!
                Chat history:
                {chat_context}
                
                Generate a balanced, gamer-style response , your name is {client.user.display_name} in the chat context. If asked about facts or game info, provide accurate info concisely."""

                genai.GenerationConfig(max_output_tokens=120, temperature=0.7)  # Constrain response length
                response = await asyncio.to_thread(model.generate_content, prompt)
                if response.parts and response.parts[0].text:
                    return response.parts[0].text
                return "Hmm, need to respawn my thoughts... 🎮"
            except Exception as e:
                logging.error(f"Error generating chat response: {str(e)}")
                return None
    except Exception as e:
        logging.error(f"Error in AI function: {str(e)}")
        return None
        