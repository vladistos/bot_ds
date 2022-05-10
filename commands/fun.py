import discord.ext.commands
from discord.ext import commands


class FunCog(commands.Cog):

    @commands.command('трусы')
    def bebra(self, ctx:discord.ext.commands.Context, limit=10):
        channel: discord.TextChannel = ctx.channel
        messages = await channel.history(limit=limit)
        for message in messages:
            await message.add_reaction('🩲')
