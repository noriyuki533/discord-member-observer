import discord
from discord.ext import commands
import traceback

TOKEN = 'XFWR0TBWp9f3xJ8TvW-gMaMY1ugrKMDl'

class MemberObserver(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix)

    async def on_ready(self):
        print(self.user.name)
        print(self.user.id)
    
    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        print(before.name)
        print(before.is_on_mobile())
        print()
        print(after.name)
        print(after.is_on_mobile())
        print("---------------------")
        if after.is_on_mobile():
            await after.edit()

def main():
    mo = MemberObserver(command_prefix='!')
    mo.run(TOKEN)

if __name__ == '__main__':
    main()