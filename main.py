import json

import interactions
from discord.ext import commands
import discord

import services.player
from commands import mus, basic

config_data = json.load(open(file='config.json'))['Data']
services.player.Player.executable = config_data['player']['path']
ds_token = config_data['discord']['token']

ds_bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())
cmnds = interactions.Client(ds_token)

cmnds.load('commands.mus')


ds_bot.add_cog(mus.MusicCog(ds_bot))
ds_bot.add_cog(basic.Basic())

# ds_bot.run(ds_token)
cmnds.start()
