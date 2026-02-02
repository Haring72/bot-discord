import discord
import os
import json
import asyncio
import requests
from discord.ext import commands

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("config.json", "r", encoding = "utf-8") as f:
            config = json.load(f)
        
        self.api_key = config['AI_CREDENTIALS']['AI_API_KEY']
        self.model = config['AI_CREDENTIALS'].get('AI_MODEL', "gemini-1.5-flash")

        if not self.api_key:
            print("AI API key not set in config.json, !ask command will be disabled")
            self.api_url = None
        else:
            self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}" # Default value for Google API while this is not investigated
    
    @commands.command(name = 'ask', help = 'Interact with conversational AI', usage = '!ask <message>')
    async def ask_ai(self, ctx, * , prompt: str):
        if not self.api_key:
            await ctx.reply(f"Este comando no está configurado, por lo que se ha deshabilitado")
            return
        else:
            await ctx.trigger_typing()

            headers = {"Content-Type": "application/json"}
            payload = {
                "contents": [{
                    "parts": [{
                        "text": f"Responde en español a menos que el usuario pida otro idioma o se detecte uno diferente\n\nUsuario: {prompt}"
                    }]
                }],
                "generationConfig": {
                    "maxOutputTokens": 512,
                    "temperature": 0.9
                }
            }

            loop = asyncio.get_running_loop()

            try:
                resp = await loop.run_in_executor(None, lambda: requests.post(self.api_url, headers = headers, json = payload, timeout = 30))
            except requests.Timeout:
                await ctx.reply("ERROR: Tiempo de espera agotado, consulta con un administrador si esto es recurrente...")
                return
            except requests.exceptions.RequestException as error:
                await ctx.reply(f"Se ha producido un error de conexión. Para más detalle, consulta con un administrador")
                print(f"ERROR DE CONEXIÓN: {error}")
                return               
     
            if resp.status_code == 429:
                await ctx.reply(f"Se han alcanzado los límites del plan gratis de este modelo de IA\nSe espera un reset para medianoche (hora del pacífico)")
                return
            elif resp.status_code == 403:
                await ctx.reply(f"Ha ocurrido un error de permisos con la API, por favor, consulta este error con un administrador")
                return
            elif resp.status_code != 200:
                await ctx.reply(f"Se ha producido un error no documentado con la IA, por favor, consulta este error con un administrador ya que este fallo es urgente\nEl código de error es {resp.status_code}")
                return
            
            data = resp.json()

            try:
                response = data["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError) as error:
                await ctx.reply("No se pudo obtener una respuesta válida de la IA")
                print(f"Error con response parsing: {error}")
                return
            
            if len(response) > 2000:
                response = response[:1900] + "..."

            await ctx.reply(response)

async def setup(bot):
    await bot.add_cog(AICog(bot))
