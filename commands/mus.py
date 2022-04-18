import asyncio as asyncio
from io import StringIO

import discord
from discord.ext import commands
from services.youtube import Youtube
from services.utils import ArrayManager
from services.player import Player


class MusicCog(discord.ext.commands.Cog):
    def __init__(self, bot, vk_audio_):
        self.bot = bot
        self.vk_audio = vk_audio_

    servers = {}

    class YouTubeCommands:
        @staticmethod
        async def find(self, ctx: commands.Context, *args):
            self.check_guild(ctx.guild.id)
            args = await self.check_args(ctx, *args)
            if not args:
                return
            emojis = {'1⃣': 0, '2⃣': 1, '3⃣': 2, '4⃣': 3, '5⃣': 4}
            channel = await self.check_voice(ctx)
            if not channel:
                return
            message: discord.Message = await ctx.reply(f'Ищу {" ".join(arg for arg in args)}')
            names, urls, duration = Youtube.get_with_names(query=' '.join(arg for arg in args), count=5)
            await message.edit(content=('\n'.join(f'{i + 1} {name} {duration[i]}' for i, name in
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
                await message.edit(content=f'Выбрано: {names[variant]} ({duration[variant]})')
                await self.get_guild_voice(ctx.guild.id, channel)
                await message.clear_reactions()
                self.add_in_q(ctx, MusicCog.Music(names[variant], urls[variant], duration=duration[variant]))

        @staticmethod
        async def play(self, ctx: commands.Context, *args):
            self.check_guild(ctx.guild.id)
            args = await self.check_args(ctx, *args)
            if not args:
                return
            channel = await self.check_voice(ctx)
            if not channel:
                return
            message: discord.Message = await ctx.reply(f'Ищу {" ".join(arg for arg in args)}')
            await self.get_guild_voice(ctx.guild.id, channel)
            name, url, duration = Youtube.get_with_names(query=' '.join(arg for arg in args), count=1)
            await message.edit(content=f'Включаю {name[0]}')
            self.add_in_q(ctx, self.Music(name[0], url[0], duration=duration[0] if duration else None))

    class VkMusicCommands:
        @staticmethod
        async def play(self, ctx: commands.Context, *args):
            vk = self.vk_audio
            count = args[1] if len(args) > 1 else None
            print(len(args))
            self.check_guild(ctx.guild.id)
            args = await self.check_args(ctx, *args)
            channel = await self.check_voice(ctx)
            if not (0 < len(args) <= 2):
                await ctx.reply('Аргументом должна быть только ссылка и колличество треков')
                return
            if not channel and args:
                return
            message: discord.Message = await ctx.reply(f'Пытаюсь включить плейлист по ссылке {args[0]}')
            await self.get_guild_voice(ctx.guild.id, channel)
            playlist = vk.get_vk_playlist_with_link(args[0], count)
            names_added = []
            await message.edit(content='Подождите...')
            while True:
                song = next(playlist, None)
                name, url, duration = song or (False, False, False)
                if name and url:
                    names_added.append(name)
                    self.add_in_q(ctx, self.Music(name, url, duration=duration, vk=True))
                    await message.edit(content=('Добавленные треки:\n' +
                                                ("\n".join(song_name for song_name in names_added[:25])) +
                                                (f' и еще {len(names_added[25:])}' if len(names_added) > 25 else '')))
                else:
                    break

    class Music:
        def __init__(self, name, url, vk=False, duration=None):
            self.url = url
            self.name = name
            self.vk = vk
            self.duration = duration

        def play(self, voice_client):
            if not self.vk:
                Player.play_youtube(voice_client, self.url)
            else:
                Player.play_vk(voice_client, self.url)

        def __str__(self):
            return '{' + f'"name":{self.name}, "link":{self.url}, "duration":{self.duration}' + '}'

    class ServerMusicQ:
        def __init__(self, voice_client: discord.voice_client.VoiceClient = None):
            self.q = []
            self.voice_client = voice_client
            self.playlist_message = None
            self.now_playing = None

    def add_in_q(self, ctx, music):
        serv_id = ctx.guild.id
        self.servers[serv_id].q.append(music)
        if not self.servers[serv_id].voice_client.is_playing():
            self.next_track(ctx)
        self.update_q(ctx)

    def next_track(self, ctx: discord.ext.commands.Context):
        serv_id = ctx.guild.id
        music = self.servers[serv_id].q[0]
        music.play(voice_client=self.servers[serv_id].voice_client)
        print(self.servers[serv_id].q[0])
        self.servers[serv_id].now_playing = music.name
        asyncio.create_task(self.wait_for_track(ctx))
        self.update_q(ctx)
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

    def update_q(self, ctx):
        if self.servers[ctx.guild.id].playlist_message:
            asyncio.create_task(self.queue(ctx=ctx, message=self.servers[ctx.guild.id].playlist_message))

    async def wait_for_track(self, ctx):
        voice_client = ctx.voice_client
        while voice_client and (voice_client.is_playing()):
            await asyncio.sleep(1)
        else:
            if voice_client and voice_client.is_connected():
                if len(self.servers[ctx.guild.id].q) != 0:
                    self.next_track(ctx)
                else:
                    return

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
            await MusicCog.YouTubeCommands.find(self, ctx, *args[1:])
        elif args[0] == 'play':
            await self.YouTubeCommands.play(self, ctx, *args[1:])

    @commands.command('vk')
    async def vk(self, ctx, *args):
        if args[0] == 'play':
            await self.VkMusicCommands.play(self, ctx, *args[1:])

    @commands.command('skip')
    async def skip(self, ctx: commands.Context, *args, print_message=True):
        voice_client: discord.voice_client.VoiceClient = self.servers[ctx.guild.id].voice_client
        print(self.servers[ctx.guild.id].q)
        if voice_client and voice_client.is_playing():
            if len(self.servers[ctx.guild.id].q) != 0:
                voice_client.stop()
                if print_message:
                    await ctx.reply(f'Пропущен {self.servers[ctx.guild.id].now_playing}')
                print(voice_client.is_playing())
                if not voice_client.is_playing():
                    self.next_track(ctx)
            else:
                voice_client.stop()
                print(self.servers[ctx.guild.id].voice_client)

                if print_message:
                    await ctx.reply(f'Пропущен {self.servers[ctx.guild.id].now_playing}')
                self.servers[ctx.guild.id].now_playing = None
        else:
            if len(self.servers[ctx.guild.id].q) != 0:
                self.next_track(ctx)

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

    @commands.command('q')
    async def queue(self, ctx: discord.ext.commands.Context, *args, message: discord.Message = None):
        self.check_guild(ctx)
        self.check_guild(ctx.guild.id)

        text = ('Очередь:\n' + "\n".join(f'{i + 1}) {song.name} {song.duration}'
                                         for i, song in enumerate(self.servers[ctx.guild.id].q))
                if len(self.servers[ctx.guild.id].q) > 0 else 'Очередь пуста')

        if len(args) == 1 and args[0] == 'full':
            file = StringIO(text)
            await ctx.reply(file=discord.file.File(file, filename='playlist.txt'))

        elif not args:
            text = text.split('\n')
            print(text)
            if not message:
                playlist_message: discord.Message = await ctx.reply(
                    '\n'.join(line for line in text[:25]) + ('\n' f'И еще {len(text[25:])}'
                                            if len(text) > 25 else ''))
                self.servers[ctx.guild.id].playlist_message = playlist_message
            else:
                await message.edit(content='\n'.join(line for line in text[:25]) + ('\n' f'И еще {len(text[25:])}'
                                            if len(text) > 25 else ''))

        elif len(args) == 2 and args[0] == 'next':
            try:
                i = int(args[1]) - 1
                track_q = self.servers[ctx.guild.id].q
                if len(track_q) > 2 and len(track_q) >= i:
                    track_q[i], track_q[0] = track_q[0], track_q[i]
                    await ctx.reply(f'{track_q[0].name} будет сыгран следующим')
                    self.update_q(ctx)
            except (ValueError, IndexError):
                await ctx.reply('?')

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
        self.add_in_q(ctx, self.Music(name='a', url=arg))
