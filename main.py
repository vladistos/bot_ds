import json

from services.vk_audio import VkAudio
from discord.ext import commands
import discord

import services.player
from commands import mus, basic

config_data = json.load(open(file='config.json'))['Data']
services.player.Player.executable = config_data['player']['path']
print(config_data['vk']['login'])
vk_audio_ = VkAudio(login=config_data['vk']['login'], password=config_data['vk']['password'])
ds_token = config_data['discord']['token']

ds_bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

ds_bot.add_cog(mus.MusicCog(ds_bot, vk_audio_))
ds_bot.add_cog(basic.Basic())

if __name__ == '__main__':
    ds_bot.run(ds_token)
