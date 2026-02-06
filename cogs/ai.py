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
        
        if config.get('AI_CREDENTIALS') and config['AI_CREDENTIALS'].get('AI_API_KEY'):
            self.api_key = config['AI_CREDENTIALS']['AI_API_KEY']
            self.model = config['AI_CREDENTIALS']['AI_MODEL']

            if not self.model:
                self.model = 'gemini-2.5-flash'

            self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}" # Default value for Google API while this is not investigated
            print("AI configured successfully, !ask command enabled")
        else:
            print("AI_API_KEY not set in config.json, !ask command will be disabled")
            self.api_key = None
            self.model = None
            self.api_url = None


    
    @commands.command(name = 'ask', help = 'Interact with conversational AI', usage = '!ask <message>')
    async def ask_ai(self, ctx, * , prompt: str):
        if not self.api_key:
            await ctx.reply(f"Este comando no está configurado, por lo que se ha deshabilitado")
            return

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

        def make_request():
            return requests.post(self.api_url, headers = headers, json = payload, timeout = 30)

        try:
            resp = await loop.run_in_executor(None, make_request)
            print(f"Status: {resp.status_code}")
        except requests.Timeout:
            await ctx.reply("ERROR: Tiempo de espera agotado, consulta con un administrador si esto es recurrente...")
            return
        except requests.exceptions.RequestException as error:
            await ctx.reply(f"Se ha producido un error de conexión. Para más detalle, consulta con un administrador")
            print(f"ERROR DE CONEXIÓN: {error}")
            return
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            await ctx.reply("Hubo un error de conexión")
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
            if "candidates" not in data or not data["candidates"]:
                await ctx.reply("No se pudo generar una respuesta")
                return
            
            candidate = data["candidates"][0]

            if "content" not in candidate or "parts" not in candidate["content"]:
                await ctx.reply("Formato de respuesta inválido de la IA")
                return
            
            response = candidate["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as error:
            await ctx.reply("No se pudo obtener una respuesta válida de la IA")
            print(f"Error con response parsing: {error}")
            return
        
        if len(response) > 2000:
            response = response[:1900] + "..."

        await ctx.reply(response)

async def setup(bot):
    await bot.add_cog(AICog(bot))
