import asyncio as asyncio
import discord
from discord.ext import commands
from services.youtube import Youtube
from services.player import Player


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class Music:
        def __init__(self, name, url):
            self.url = url
            self.name = name

        def play(self, voice_client):
            Player.play(voice_client, self.url)

    class ServerMusicQ:
        def __init__(self, voice_client: discord.voice_client.VoiceClient = None):
            self.q = []
            self.voice_client = voice_client

    servers = {}

    def add_in_q(self, serv_id, music):
        self.servers[serv_id].q.append(music)
        if not self.servers[serv_id].voice_client.is_playing():
            self.next_track(serv_id)

    def next_track(self, serv_id):
        music = self.servers[serv_id].q[0]
        music.play(voice_client=self.servers[serv_id].voice_client)
        self.servers[serv_id].q.pop(0)

    def check_guild(self, guild_id):
        try:
            self.servers[guild_id]
        except KeyError:
            self.servers[guild_id] = self.ServerMusicQ()

    @commands.command('н')
    async def find(self, ctx: commands.Context, *args):
        if '--скип' in args:
            list(args).remove('--скип')
            skip = True
        else:
            skip = False
        emojis = {'1⃣': 0, '2⃣': 1, '3⃣': 2, '4⃣': 3, '5⃣': 4}
        if ctx.author.voice:
            channel = ctx.author.voice.channel
        else:
            await ctx.send('Вы не находитесь в голосовом канале')
            return
        message: discord.Message = await ctx.reply(f'Ищу {" ".join(arg for arg in args)}')
        names, urls = Youtube.get_with_names(query=' '.join(arg for arg in args), count=5)
        self.check_guild(ctx.guild.id)
        await message.edit(content=('\n'.join(f'{i + 1} {name}' for i, name in
                                              enumerate(names))) if len(names) > 1 else names[0])
        for emoji in emojis.keys():
            await message.add_reaction(emoji)

        def check(reaction_event: discord.RawReactionActionEvent):
            return reaction_event.member == ctx.author and reaction_event.message_id == message.id

        try:
            reaction = await self.bot.wait_for("raw_reaction_add", timeout=10.0, check=check)
        except Exception:
            await message.edit(content='Время ожидания истекло')
            await message.clear_reactions()
            return
        print(reaction.emoji)
        if reaction.emoji.name in emojis.keys():
            variant = emojis[reaction.emoji.name]
            await message.edit(content=f'Выбрано: {names[variant]}')
            self.servers[ctx.guild.id].voice_client = await channel.connect(reconnect=True, timeout=None) \
                if self.servers[ctx.guild.id].voice_client is None or \
                not self.servers[ctx.guild.id].voice_client.is_connected() else self.servers[
                ctx.guild.id].voice_client
            await message.clear_reactions()
            if skip:
                await self.skip(ctx)
            self.add_in_q(ctx.guild.id, self.Music(names[variant], urls[variant]))
        voice_client = self.servers[ctx.guild.id].voice_client
        while voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            await asyncio.sleep(1)
        else:
            if voice_client:
                if len(self.servers[ctx.guild.id].q) != 0:
                    self.next_track(ctx.guild.id)
                else:
                    await voice_client.disconnect()

    @commands.command('п')
    async def play(self, ctx: commands.Context, *args):
        if '--скип' in args:
            list(args).remove('--скип')
            skip = True
        else:
            skip = False
        if ctx.author.voice:
            channel = ctx.author.voice.channel
        else:
            await ctx.send('Вы не находитесь в голосовом канале')
            return
        message: discord.Message = await ctx.reply(f'Ищу {" ".join(arg for arg in args)}')
        self.check_guild(ctx.guild.id)
        self.servers[ctx.guild.id].voice_client = await channel.connect(reconnect=True, timeout=None) \
            if self.servers[ctx.guild.id].voice_client is None else self.servers[ctx.guild.id].voice_client
        name, url = Youtube.get_with_names(query=' '.join(arg for arg in args), count=1)
        await message.edit(content=f'Включаю {name[0]}')
        if skip:
            await self.skip(ctx)
        self.add_in_q(ctx.guild.id, self.Music(name[0], url[0]))
        voice_client = self.servers[ctx.guild.id].voice_client
        while voice_client and (voice_client.is_playing() or voice_client.is_paused()):
            await asyncio.sleep(1)
        else:
            if voice_client:
                if len(self.servers[ctx.guild.id].q) != 0:
                    self.next_track(ctx.guild.id)
                else:
                    await voice_client.disconnect()

    @commands.command('скип')
    async def skip(self, ctx: commands.Context):
        voice_client = self.servers[ctx.guild.id].voice_client
        if voice_client and voice_client.is_playing():
            if len(self.servers[ctx.guild.id].q) != 0:
                voice_client.stop()
                self.next_track(ctx.guild.id)
            else:
                await voice_client.disconnect()
