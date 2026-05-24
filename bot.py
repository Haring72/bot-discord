import os
import discord
import asyncio
from discord.ext import commands
from dotenv import load_dotenv



ENV_TEMPLATE = """
# Discord bot token (you need to fill this to work!)
DISCORD_TOKEN=

# Welcome new members in this channel (recommended to fill)
WELCOME_CHANNEL_ID=


# Below this, everything is optional to fill


# Twitch stream tracker integration
TWITCH_CLIENT_ID=
TWITCH_CLIENT_SECRET=

# AI Integration
AI_API_KEY=
AI_MODEL=gemini-2.0-flash-exp
"""

def create_env_if_missing():
    if not os.path.exists('.env'):
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(ENV_TEMPLATE)
        print(".env file created, please fill it properly with any text editor")
        return False
    return True

if not create_env_if_missing():
    exit(1)

load_dotenv()

def env_int(name):
    value = os.getenv(name, '').strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        print(f"Warning: {name} must be a number. Ignoring invalid value")
        return None
    
def get_config_from_env():
    token = os.getenv('DISCORD_TOKEN', '').strip()
    if not token:
        print("DISCORD_TOKEN is missing in .env. Please set it before running the bot")
        exit(1)

    return {
        "token": token,
        "welcome_channel_id": env_int("WELCOME_CHANNEL_ID"),
        "twitch_app_credentials": {
            "client_id": os.getenv("TWITCH_CLIENT_ID", "").strip(),
            "client_secret": os.getenv("TWITCH_CLIENT_SECRET", "").strip()
        },
        "AI_CREDENTIALS": {
            "AI_API_KEY": os.getenv("AI_API_KEY", "").strip(),
            "AI_MODEL": os.getenv("AI_MODEL", "").strip() or "gemini-2.0-flash-exp"
        }
    }

config = get_config_from_env()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
bot.config = config

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