import discord
from discord.ext import commands, tasks
from client import client
from discord import app_commands, Interaction, Embed, Color, utils, File
import typing
import inspect
import asyncio
import os
import typing
from dotenv import load_dotenv
import logging
from database import database
from resources.error_handler import MissingPermissions, has_permissions,MissingArguments
from collections import defaultdict
from commands.poll_commands import polls_data


