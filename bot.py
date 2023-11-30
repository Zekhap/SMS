from flask import Flask, request
import concurrent.futures
import discord
from discord.ext import commands
from discord import Permissions
from datetime import datetime
import pytz
import json
import asyncio
import threading

# Define default configuration values
default_config = {
    'PREFIX': '!',
    'CHANNEL': 0,
    'TOKEN': 'your_default_token'
}
# Keys that are allowed to be modified
allowed_keys = ['PREFIX', 'CHANNEL']

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
        print(f'START');
        await bot.start("MTE3OTgyODY3MzYwMDMwNzI0MQ.G-YUsb.aouqiq7QsTH_b-d0FXEntFY_EtWRuMdXHseulE")
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
DISCORD_CHANNEL_ID = config_data['CHANNEL']

# Function to extract numbers from a string
def extract_numbers(text):
    return ''.join(filter(str.isdigit, text))

def is_admin(ctx):
    # Check if the command invoker is a Discord administrator
    return ctx.author.guild_permissions.administrator


@bot.command(name='setconfig', help='Set configuration data')
@commands.check(is_admin)
async def set_config(ctx, key, value):
    global config_data

    # Check if the specified key is allowed to be modified
    if key in allowed_keys:
        # Update the config data
        config_data[key] = value

        # Update CHANNEL directly if key is CHANNEL
        if key == 'CHANNEL':
            global DISCORD_CHANNEL_ID
            DISCORD_CHANNEL_ID = int(value)

        # Save the updated configuration to the file
        with open('config.json', 'w') as config_file:
            json.dump(config_data, config_file, indent=4)

        await ctx.send(f'Configuration updated: {key} set to {value}')
    else:
        await ctx.send(f'Error: {key} cannot be modified.')

@set_config.error
async def set_config_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command.")


# Discord bot command to send codes
@bot.command(name='kod', description='Skickar kod')
async def kod_command(ctx):
    global recent_texts, last_request_time

    # Check if the saved channel exists or is set to 0
    if config_data['CHANNEL'] == 0:
        await ctx.send("Saved channel does not exist. Set a valid channel using setconfig command.")
        return

    try:
        user_id = ctx.author.id
        stockholm_tz = pytz.timezone('Europe/Stockholm')
        current_time = datetime.now(stockholm_tz)

        new_texts = recent_texts if last_request_time is None else [text for text in recent_texts if text["time"] > last_request_time]

        if not new_texts:
            await ctx.send("Ingen ny kod har anlänt.")
        else:
            for text in new_texts:
                await ctx.send(f"{current_time.strftime('%H:%M:%S')}\nKod: {text['content']}\n<@{user_id}>")

        # Update the last request time
        last_request_time = current_time
    except Exception as e:
        print(f'Error processing !kod command: {e}')
        await ctx.send('An error occurred while processing the command. Please try again later.')


# Twilio SMS webhook endpoint
@app.route('/sms', methods=['POST'])
def sms():
    global recent_texts

    try:
        sms_content = request.form['Body']
    
        print('Received SMS:', sms_content)

        # Extract numbers from the SMS content
        numbers_only = extract_numbers(sms_content)

        # Get the current time in Stockholm's timezone
        stockholm_tz = pytz.timezone('Europe/Stockholm')
        current_time = datetime.now(stockholm_tz)

        if not any(text['content'] == numbers_only for text in recent_texts):
            recent_texts.append({
                "time": current_time,
                "content": numbers_only
            })

        # Optionally, clean up old messages from recent_texts
        recent_texts = [text for text in recent_texts if (current_time - text["time"]).seconds < 600]

        return '', 200
    except Exception as e:
        print(f'Error processing SMS: {e}')
        return 'Internal server error', 500

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

def run_flask():
    app.run(host='0.0.0.0', port=25530, debug=False)

if __name__ == '__main__':
    print("Starting Discord Bot!")
    try:
        # Start the Flask app in the main thread
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.start()

        # Run the Discord bot in a separate thread using asyncio
        loop = asyncio.get_event_loop()
        loop.create_task(run_discord_bot())
        loop.run_forever()
    except KeyboardInterrupt:
        # Handle Ctrl+C to stop the script without traceback
        print("Script interrupted by user.")
    except Exception as e:
        print(f"An error occurred during shutdown: {e}")