from flask import Flask, request
import logging
import concurrent.futures
from discord.ext import commands
import discord
from discord import Permissions
from datetime import datetime
import pytz
import json
import asyncio
import threading
import traceback

# Define default configuration values
default_config = {
    'CHANNEL': 0,
    'TOKEN': 'your_default_token'
}
# Keys that are allowed to be modified
allowed_keys = ['CHANNEL']

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
logging.basicConfig(level=logging.ERROR)
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
DISCORD_CHANNEL_ID = config_data['CHANNEL']

# Function to extract numbers from a string
def extract_numbers(text):
    return ''.join(filter(str.isdigit, text))

def is_admin(ctx):
    # Check if the command invoker is a Discord administrator
    return ctx.author.guild_permissions.administrator

@bot.tree.command(name='config', description='Set configuration data')
@app_commands.describe(channel='The id of the channel you want to set')
@commands.check(is_admin)
async def set_config(interaction: discord.Interaction, channel: int):
    global config_data

    if(channel)
        global DISCORD_CHANNEL_ID
        config_data['CHANNEL'] = channel
        DISCORD_CHANNEL_ID = int(channel)
    
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
@bot.tree.command(name='kod', description='Skickar kod')
async def kod(interaction: discord.Interaction):
    try:
        global recent_texts, last_request_time, last_user_id

        user_id = interaction.user.id
        last_user_id = interaction.user.id
        stockholm_tz = pytz.timezone('Europe/Stockholm')
        current_time = datetime.now(stockholm_tz)

        if last_request_time is None:
            new_texts = recent_texts
        else:
            new_texts = [text for text in recent_texts if text["time"] > last_request_time]

        if not new_texts:
            await interaction.response.send_message("Letar efter kod...")
        else:
            for text in new_texts:
                await interaction.response.send_message(f"{current_time.strftime('%H:%M:%S')}\nKod: {text['content']}\n<@{user_id}>")

        last_request_time = current_time
    except Exception as e:
        print(f"An error has occurred in the discord command section: {e}")
        traceback_string = traceback.format_exc()
        logging.error(traceback_string)

# Twilio SMS webhook endpoint
@app.route('/sms', methods=['POST'])
def sms():
    try:
        global recent_texts, last_user_id, last_request_time

        sms_content = request.form['Body']
        print('Received SMS:', sms_content)
        channel = bot.get_channel(DISCORD_CHANNEL_ID)
        numbers_only = extract_numbers(sms_content)

        stockholm_tz = pytz.timezone('Europe/Stockholm')
        current_time = datetime.now(stockholm_tz)

        if not any(text['content'] == numbers_only for text in recent_texts):
            recent_texts.append({
                "time": current_time,
                "content": numbers_only
            })

        recent_texts = [text for text in recent_texts if (current_time - text["time"]).seconds < 600]

        time_diff = (current_time - last_request_time).total_seconds()
        print(f"user: {last_user_id}, time_diff: {time_diff}")
        if time_diff < 120 and last_user_id != None:
            print(f"Sending message to Discord channel...")
            bot.loop.create_task(channel.send(f"-----------\n{current_time.strftime('%H:%M:%S')}\nKod: {numbers_only}\n<@{last_user_id}>"))

    except Exception as e:
        print(f"An error has occured in the flask route: {e}")
        traceback_string = traceback.format_exc()
        logging.error(traceback_string)
        return jsonify({"error": "An internal error occurred"}), 500

    return '', 200

@bot.event
async def on_ready():
    await bot.tree.sync()
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
        exit
    except Exception as e:
        print(f"An error occurred during shutdown: {e}")