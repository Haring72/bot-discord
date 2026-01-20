import os
import discord
import json
from discord.ext import commands



intents = discord.Intents.default()
intents.message_content = True

# Check if necessary to use discord.Client or commands.Bot (first one commented for now)
# client = discord.Client(intents=intents)

bot = commands.Bot(command_prefix = '!', intents=intents)

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

with open('config.json') as f:
    config = json.load(f)

@bot.event
async def on_ready():
    print(f'Started as {bot.user}')



async def main():
    await load_cogs()
    await bot.run(config['token'])

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())