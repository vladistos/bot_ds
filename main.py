import json

import discord
from discord.ext import commands

import services.player
from commands import mus

config_data = json.load(open(file='config.json'))['Data']
services.player.Player.executable = config_data['player']['path']
ds_token = config_data['discord']['token']

ds_bot = commands.Bot(command_prefix='бот ', intents=discord.Intents.all())

ds_bot.add_cog(mus.MusicCog(ds_bot))

ds_bot.run(ds_token)