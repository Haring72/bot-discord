import discord
import json
from discord.ext import commands

intents = discord.Intents.default()
client = discord.Client(intents=intents)

with open('config.json') as f:
    config = json.load(f)

@client.event
async def on_ready():
    print(f'Started as {client.user}')

client.run(config['token'])