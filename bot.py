import os
import discord
import json
import asyncio
from discord.ext import commands



intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

BOT_CONFIG = {
    "token": "YOUR_BOT_TOKEN",

    "welcome_channel_id": 1234567890123456789,

    "twitch_app_credentials": {
        "client_id": "TWITCH_APP_CLIENT_ID",
        "client_secret": "TWITCH_APP_CLIENT_SECRET"
    },

    "AI_CREDENTIALS": {
        "AI_API_KEY": "API_KEY_HERE",
        "AI_MODEL": ""
    }
}

def load_config():
    if not os.path.exists('config.json'):
        with open('config.json', 'w', encoding='utf-8') as f:
            json.dump(BOT_CONFIG, f, indent=4)
        print("config.json file created with default values. Please fill it to continue")

    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print("config.json is invalid. Fix it or delete and run the bot again to regenerate")
        exit(1)

    if not config.get('token'):
        print("config.json is missing the token")
        exit(1)

    return config

config = load_config()

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f'Bot started as {bot.user}')
    


async def main():
    bot.remove_command('help')
    await load_cogs()
    print(f'Cogs loaded successfully.')
    await bot.start(config['token'])

if __name__ == '__main__':
    asyncio.run(main())