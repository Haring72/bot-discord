import os
import discord
import json
import asyncio
from discord.ext import commands



intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

def load_config():
    try:
        with open('config.json') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Config.json file can not be found. Please, create one first")
        exit(1)
    except json.JSONDecodeError:
        print("This config.json is not valid, check documentation for more help")
        exit(1)

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