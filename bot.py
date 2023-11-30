from flask import Flask, request
import concurrent.futures
from discord.ext import commands
from discord import Permissions
import discord
from datetime import datetime
import pytz
import json
import asyncio

# Define default configuration values
default_config = {
    'PREFIX': '!',
    'DISCORD_CHANNEL_ID': 0,
    'TOKEN': 'your_default_token'
}
# Keys that are allowed to be modified
allowed_keys = ['PREFIX', 'DISCORD_CHANNEL_ID']

try:
    with open('config.json', 'r') as config_file:
        config_data = json.load(config_file)
except FileNotFoundError:
    # If the file doesn't exist, use the default configuration
    config_data = default_config
    with open('config.json', 'w') as config_file:
        json.dump(config_data, config_file, indent=4)



# Shared data structures
recent_texts = []
last_request_time = None

app = Flask(__name__)

async def run_discord_bot():
    try:
        await bot.start(config_data['TOKEN'])
    except discord.LoginFailure:
        print("Invalid token. Please update the TOKEN in config.json.")
    except Exception as e:
        print(f"An error occurred: {e}")
        print("Reconnecting...")

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix=config_data['PREFIX'], intents=intents)
DISCORD_CHANNEL_ID = config_data['DISCORD_CHANNEL_ID']

@bot.event
async def on_ready():
    print(f'Starting Discord Bot!')
    print(f'Logged in as {bot.user.name}')
    print(f'DISCORD_CHANNEL_ID: {config_data["DISCORD_CHANNEL_ID"]}')

def run_flask():
    app.run(host='0.0.0.0', port=25530, debug=False)

if __name__ == '__main__':
    print("Starting Discord Bot!")
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(run_flask)
        executor.submit(asyncio.run, run_discord_bot)