import discord
from discord.ext import commands, tasks
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import json
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from client import client
import os
import dotenv
from resources.translation_functions import translate_text

dotenv.load_dotenv()
WOE_ID = int(os.getenv('WOE_ID'))
WOE_ID_ES = int(os.getenv('WOE_ID_ES'))
WOE_ID_FR = int(os.getenv('WOE_ID_FR'))



SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', "resources/credentials.json")
SPREADSHEET_ID = os.getenv('QUOTE_SPREADSHEET_ID')
WORKSHEET_NAME = os.getenv('QUOTE_WORKSHEET_NAME', "Daily Quotes")
central = pytz.timezone('America/Chicago')
QUOTE_SEND_HOUR = int(os.getenv('QUOTE_SEND_HOUR', 5))




USED_QUOTES_FILE = "used_quotes.json"

def load_used_quotes():
    try:
        with open(USED_QUOTES_FILE, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_used_quotes(used_quotes):
    with open(USED_QUOTES_FILE, 'w') as file:
        json.dump(used_quotes, file)


def init_gspread():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        return client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    except Exception as e:
        print(f"Error initializing Google Sheets client: {e}")
        raise

def get_random_quote():
    sheet = init_gspread()
    quotes = sheet.col_values(1)[1:]  
    used_quotes = load_used_quotes()
    sources = sheet.col_values(2)[1:] 

    # Filter unused quotes
    unused_quotes = [quote for quote in quotes if quote not in used_quotes]
    
    if not unused_quotes:
        used_quotes = []
        unused_quotes = quotes
    
    # Select a random quote
    quote = random.choice(unused_quotes)
    quote_index = quotes.index(quote)  
    
    # Get the corresponding source
    source = sources[quote_index] if quote_index < len(sources) else "Unknown source"
    
    # Update the list of used quotes
    used_quotes.append(quote)
    save_used_quotes(used_quotes)
    
    return quote, source



async def send_daily_quote():
    now = datetime.now(central)
    if now.hour == QUOTE_SEND_HOUR:
        quote,source = get_random_quote()
        try:
            channel = client.get_channel(WOE_ID)
            if channel:
                embed = discord.Embed(title="Quote of the Day",description=f"\"{quote}\"",color=discord.Color.green())
                embed.add_field(name="Source",value=source if source else "Unknown")
                await channel.send(embed=embed)
        except:
            pass
        try:
            channel = client.get_channel(WOE_ID_ES)
            quote_translated_es = translate_text(quote,"EN-US","ES")
            if channel:
                embed = discord.Embed(title="Cita del día",description=f"\"{quote_translated_es}\"",color=discord.Color.green())
                embed.add_field(name="Fuente",value=source if source else "Desconocido")
                await channel.send(embed=embed)
        except:
            pass
        try:
            channel = client.get_channel(WOE_ID_FR)
            quote_translated_fr = translate_text(quote,"EN-US","FR")
            if channel:
                embed = discord.Embed(title="Citation du jour",description=f"\"{quote_translated_fr}\"",color=discord.Color.green())
                embed.add_field(name="Source",value=source if source else "Inconnu")
                await channel.send(embed=embed)
        except:
            pass                
            
        
        
        



# Scheduler setup
scheduler = AsyncIOScheduler()

scheduler.add_job(send_daily_quote, 'cron', hour=QUOTE_SEND_HOUR, minute=0, timezone=central)

