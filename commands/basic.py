from discord.ext import commands


class Basic(commands.Cog):

    @commands.command('out')
    async def out(self, ctx: commands.Context):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()