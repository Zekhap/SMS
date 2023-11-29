from flask import Flask, request
import concurrent.futures
from discord.ext import commands
import discord
from datetime import datetime
import pytz

# Discord bot setup
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
DISCORD_CHANNEL_ID = 1173979909056626748  # Replace with your Discord channel ID

# Shared data structures
recent_texts = []
last_request_time = None

app = Flask(__name__)

# Function to extract numbers from a string
def extract_numbers(text):
    return ''.join(filter(str.isdigit, text))

# Discord bot command to send codes
@bot.command(name='kod', description='Skickar kod')
async def kod_command(ctx):
    global recent_texts, last_request_time

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

# Twilio SMS webhook endpoint
@app.route('/sms', methods=['POST'])
def sms():
    global recent_texts

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

# Discord bot events
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

def run_discord_bot():
    bot.run('YOUR_DISCORD_BOT_TOKEN')

def run_flask():
    app.run(port=3000, debug=False)

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        executor.submit(run_flask)
        executor.submit(run_discord_bot)