import json

import discord
from discord.ext import commands
from commands import mus

config_data = json.load(open(file='config.json'))['Data']
ds_token = config_data['discord']['token']

ds_bot = commands.Bot(command_prefix='бот ', intents=discord.Intents.all())

ds_bot.add_cog(mus.MusicCog(ds_bot))

ds_bot.run(ds_token)