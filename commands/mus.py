import asyncio as asyncio
import threading

import discord
import interactions
from discord.ext import commands
from services.youtube import Youtube
from services.player import Player


class MusicCog(interactions.Extension):
    def __init__(self, bot):
        self.bot = bot

    class YouTubeCommands:

        @staticmethod
        async def yt_find(self, ctx: commands.Context, *args):
            self.check_guild(ctx.guild.id)
            args = await self.check_args(ctx, *args)
            if not args:
                return
            emojis = {'1⃣': 0, '2⃣': 1, '3⃣': 2, '4⃣': 3, '5⃣': 4}
            channel = await self.check_voice(ctx)
            if not channel:
                return
            message: discord.Message = await ctx.reply(f'Ищу {" ".join(arg for arg in args)}')
            names, urls = Youtube.get_with_names(query=' '.join(arg for arg in args), count=5)
            await message.edit(content=('\n'.join(f'{i + 1} {name}' for i, name in
                                                  enumerate(names))) if len(names) > 1 else names[0])
            for emoji in emojis.keys():
                await message.add_reaction(emoji)

            def check(reaction_event: discord.RawReactionActionEvent):
                return reaction_event.member == ctx.author and reaction_event.message_id == message.id

            try:
                reaction = await self.bot.wait_for("raw_reaction_add", timeout=10.0, check=check)
            except asyncio.exceptions.TimeoutError:
                await message.edit(content='Время ожидания истекло')
                await message.clear_reactions()
                return
            if reaction.emoji.name in emojis.keys():
                variant = emojis[reaction.emoji.name]
                await message.edit(content=f'Выбрано: {names[variant]}')
                await self.get_guild_voice(ctx.guild.id, channel)
                await message.clear_reactions()
                self.add_in_q(ctx.guild.id, self.Music(names[variant], urls[variant]))
                await self.wait_for_track(ctx)

        @staticmethod
        async def yt_play(self, ctx: commands.Context, *args):
            self.check_guild(ctx.guild.id)
            args = await self.check_args(ctx, *args)
            if not args:
                return
            channel = await self.check_voice(ctx)
            if not channel:
                return
            message: discord.Message = await ctx.reply(f'Ищу {" ".join(arg for arg in args)}')
            await self.get_guild_voice(ctx.guild.id, channel)
            name, url = Youtube.get_with_names(query=' '.join(arg for arg in args), count=1)
            await message.edit(content=f'Включаю {name[0]}')
            self.add_in_q(ctx.guild.id, self.Music(name[0], url[0]))
            await self.wait_for_track(ctx)

    class Music:
        def __init__(self, name, url):
            self.url = url
            self.name = name

        def play(self, voice_client):
            Player.play_youtube(voice_client, self.url)

        def __str__(self):
            return '{' + f'"name":{self.name}, "link":{self.url}' + '}'

    class ServerMusicQ:
        def __init__(self, voice_client: discord.voice_client.VoiceClient = None):
            self.q = []
            self.voice_client = voice_client
            self.now_playing = None

    servers = {}

    def add_in_q(self, serv_id, music):
        self.servers[serv_id].q.append(music)
        if not self.servers[serv_id].voice_client.is_playing():
            self.next_track(serv_id)

    def next_track(self, serv_id):
        music = self.servers[serv_id].q[0]
        music.play(voice_client=self.servers[serv_id].voice_client)
        print(self.servers[serv_id].q[0])
        self.servers[serv_id].now_playing = music.name
        self.servers[serv_id].q.pop(0)

    def check_guild(self, guild_id):
        try:
            self.servers[guild_id]
        except KeyError:
            self.servers[guild_id] = self.ServerMusicQ()

    @staticmethod
    async def check_voice(ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            return channel
        else:
            await ctx.send('Вы не находитесь в голосовом канале')
            return False

    async def wait_for_track(self, ctx):
        voice_client = self.servers[ctx.guild.id].voice_client
        while voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            await asyncio.sleep(1)
        else:
            if voice_client and voice_client.is_connected():
                if len(self.servers[ctx.guild.id].q) != 0:
                    self.next_track(ctx.guild.id)
                else:
                    await asyncio.sleep(5)
                    await voice_client.disconnect()

    async def get_guild_voice(self, guild_id, voice_channel):
        self.servers[guild_id].voice_client = await voice_channel.connect(reconnect=True, timeout=None) \
            if self.servers[guild_id].voice_client is None or \
               not self.servers[guild_id].voice_client.is_connected() else self.servers[guild_id].voice_client

    async def check_args(self, ctx, *args):
        args = list(args)
        if '-скип' in args:
            args.remove('-скип')
            skip = True
        else:
            skip = False
        if skip:
            await self.skip(ctx)

        if '--скип' in args:
            args.remove('--скип')
            skip_all = True
        else:
            skip_all = False
        if skip_all:
            await self.skip_all(ctx)

        if args:
            return args
        else:
            await ctx.reply('Ошибка! Пустое сообщение')
            return False

    @commands.command('youtube')
    async def youtube(self, ctx, *args):
        if args[0] == 'search':
            await MusicCog.YouTubeCommands.yt_find(self, ctx, *args[1:])
        elif args[0] == 'play':
            await self.YouTubeCommands.yt_play(self, ctx, *args[1:])

    @commands.command('skip')
    async def skip(self, ctx: commands.Context, *args, print_message=True):
        voice_client = self.servers[ctx.guild.id].voice_client
        print(self.servers[ctx.guild.id].q)
        if voice_client and voice_client.is_playing():
            if len(self.servers[ctx.guild.id].q) != 0:
                voice_client.stop()
                if print_message:
                    await ctx.reply(f'Пропущен {self.servers[ctx.guild.id].now_playing}')
                self.next_track(ctx.guild.id)
            else:
                voice_client.pause()
                if print_message:
                    await ctx.reply(f'Пропущен {self.servers[ctx.guild.id].now_playing}')
                self.servers[ctx.guild.id].now_playing = None

    @commands.command('skip_all')
    async def skip_all(self, ctx):
        voice_client = self.servers[ctx.guild.id].voice_client
        if voice_client and voice_client.is_playing():
            if len(self.servers[ctx.guild.id].q) != 0:
                self.servers[ctx.guild.id].q.clear()
                await self.skip(ctx=ctx, print_message=False)

    @commands.command('now')
    async def now_playing(self, ctx):
        self.check_guild(ctx)
        await ctx.reply(f'cейчас играет: {self.servers[ctx.guild.id].now_playing}'
                        if self.servers[ctx.guild.id].now_playing else 'Сейчас ничего не играет')

    @commands.command('queue')
    async def queue(self, ctx):
        self.check_guild(ctx)
        await ctx.reply(('Очередь:\n' + "\n".join(song.name for song in self.servers[ctx.guild.id].q)) if
                        len(self.servers[ctx.guild.id].q) > 0 else 'Очередь пуста')

    @commands.command('тест')
    async def test(self, ctx, arg):
        self.check_guild(ctx.guild.id)
        if ctx.author.voice:
            channel = ctx.author.voice.channel
        else:
            await ctx.send('Вы не находитесь в голосовом канале')
            return
        self.servers[ctx.guild.id].voice_client = await channel.connect(reconnect=True, timeout=None) \
            if self.servers[ctx.guild.id].voice_client is None or \
               not self.servers[ctx.guild.id].voice_client.is_connected() else self.servers[
            ctx.guild.id].voice_client
        self.add_in_q(ctx.guild.id, self.Music(name='a', url=arg))


def setup(bot: interactions.Client):
    print(bot)

