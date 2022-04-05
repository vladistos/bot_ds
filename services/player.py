import json

import discord


class Player:
    config_youtube = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

    config_vk = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -http_persistent false',
                 'options': '-vn'}
    executable = None

    @staticmethod
    def play_youtube(voice_client, src):
        source = discord.FFmpegPCMAudio(executable=Player.executable, source=src, **Player.config_youtube)
        voice_client.play(source)

    @staticmethod
    def play_vk(voice_client, src):
        source = discord.FFmpegPCMAudio(executable=Player.executable, source=src, **Player.config_vk)
        voice_client.play(source)
