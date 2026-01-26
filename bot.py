import os
import discord
import json
from discord.ext import commands



intents = discord.Intents.default()

bot = commands.Bot(command_prefix='!', intents=intents)
intents.message_content = True

with open('config.json') as f:
    config = json.load(f)

@bot.event
async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event

### @bot.remove_command('help') # This requires more testing

@bot.command(name = 'help')
async def custom_help_command(ctx):
    help_message = "Estos son los comandos disponibles:\n"

    for command in bot.commands:
        help_message += f"!{command.name}: {command.help}\n"
    
    await ctx.send(help_message)
    


async def on_ready():
    print(f'Bot started as {bot.user}')

import asyncio
async def main():
    await load_cogs()
    print(f'Cogs loaded successfully.')
    await bot.start(config['token'])

if __name__ == '__main__':
    asyncio.run(main())