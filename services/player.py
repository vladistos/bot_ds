import json

import discord


class Player:
    config = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    @staticmethod
    def play(voice_client, src):
        source = discord.FFmpegPCMAudio(executable=json.load(open('/../config.json'))['Data']['player']['path'],
                                        source=src, **Player.config)
        voice_client.play(source)
