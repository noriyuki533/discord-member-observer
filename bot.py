import discord
from discord.ext import commands
import traceback
import datetime
import configparser
import os
import sys


def get_jst_dtnow_str():
    JST = datetime.timezone(datetime.timedelta(hours=+9), "JST")
    dtnow_jst = datetime.datetime.now(JST)
    return dtnow_jst.strftime("%Y-%m-%d %H:%M:%S")


class MemberObserver(commands.Bot):
    def __init__(self, command_prefix, chids: dict):
        super().__init__(command_prefix)
        self.chids = chids

    async def on_ready(self):
        pass

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        member_avatar_url = str(after.avatar_url)
        temp_chid = self.chids["status"]

        # ステータスの変更
        if not before.status == after.status:
            update_str = "**{}** -> **{}**".format(before.status, after.status)
            msg = """
            **{0.name}**が**{0.status}**になりました.
            """.format(
                after
            )
            if after.is_on_mobile():
                msg += "(モバイル)"
            footer_str = "ステータスの変更"
        # Spotifyステータスの変更
        elif isinstance(after.activity, discord.Spotify):
            total_sec = after.activity.duration.total_seconds()
            minutes = int(total_sec // 60 % 60)
            seconds = int(total_sec % 60)
            update_str = "{0}".format(after.activity.album)
            msg = "__**{0}** / {1}__\n({2})を再生中".format(
                after.activity.title,
                after.activity.artist,
                "{0}分{1}秒".format(minutes, seconds),
            )
            footer_str = "Spotifyステータスの変更"
            temp_chid = self.chids["spotify"]
        # ゲームアクティビティの変更
        elif not before.activity == after.activity:
            before_act_str = (
                before.activity.name if before.activity else before.activity
            )
            after_act_str = after.activity.name if after.activity else after.activity

            # ゲームアクティビティ終了時
            if not after.activity:
                msg = """
                **{0.name}**が**{1}**を終了しました.
                """.format(
                    before, before_act_str
                )
                update_str = "**{}** -> **{}**".format(before_act_str, after_act_str)
            # ゲームアクティビティ変更時(同一ゲーム)
            elif before.activity and before.activity.name == after.activity.name:
                if not after.activity.details:
                    return
                msg = """
                __詳細__:\n{0}
                """.format(
                    after.activity.details
                )
                update_str = "**{}**".format(after_act_str)
            # ゲームアクティビティ開始時
            elif not before.activity or not (before.activity == after.activity):
                msg = """
                **{0.name}**が**{1}**を開始しました.
                """.format(
                    after, after_act_str
                )
                update_str = "**{}** -> **{}**".format(before_act_str, after_act_str)
            else:
                return

            footer_str = "ゲームアクティビティの変更"
        else:
            return

        msg_embed = discord.Embed()
        msg_embed.title = "[{}]".format(get_jst_dtnow_str())
        msg_embed.add_field(name=update_str, value=msg)
        msg_embed.set_thumbnail(url=member_avatar_url)
        msg_embed.set_footer(text=footer_str)

        not_channel = self.get_channel(int(temp_chid))
        await not_channel.send(embed=msg_embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        member_avatar_url = str(member.avatar_url)
        footer_str = "ボイスステータスの変更"

        if not before.channel == after.channel:
            update_str = "**{}** -> **{}**".format(before.channel, after.channel)
            if not before.channel:
                msg = """
                **{0}**が**{1}**に参加しました.
                """.format(
                    member, after.channel.name
                )
            elif not after.channel:
                msg = """
                **{0}**が**{1}**から退出しました.
                """.format(
                    member, before.channel.name
                )
            else:
                msg = """
                **{0}**が**{1}**から**{2}**に移動しました.
                """.format(
                    member, before.channel.name, after.channel.name
                )
        elif not before.self_deaf == after.self_deaf:
            update_str = "deaf: **{}** -> **{}**".format(
                before.self_deaf, after.self_deaf
            )
            msg = """
            **{0}**が**スピーカーミュート**{1}.
            """.format(
                member, "しました" if after.self_deaf else "を解除しました"
            )
        elif not before.self_mute == after.self_mute:
            update_str = "mute: **{}** -> **{}**".format(
                before.self_mute, after.self_mute
            )
            msg = """
            **{0}**が**ミュート**{1}.
            """.format(
                member, "しました" if after.self_mute else "を解除しました"
            )
        else:
            return

        msg_embed = discord.Embed()
        msg_embed.title = "[{}]".format(get_jst_dtnow_str())
        msg_embed.add_field(name=update_str, value=msg)
        msg_embed.set_thumbnail(url=member_avatar_url)
        msg_embed.set_footer(text=footer_str)

        not_channel = self.get_channel(int(self.chids["voice"]))
        await not_channel.send(embed=msg_embed)


def main():
    if not os.path.exists("./token.ini"):
        token = input("token: ")
        config = configparser.ConfigParser()
        token_section = "botinfo"
        config.add_section(token_section)
        config.set(token_section, "token", token)

        id_status_update_channel = input("status_update_channel_id: ")
        id_voice_status_update_channel = input("voice_update_channel_id: ")
        id_spotify_update_channel = input("spotify_update_channel_id: ")
        chid_section = "chids"
        config.add_section(chid_section)
        config.set(chid_section, "status", id_status_update_channel)
        config.set(chid_section, "voice", id_voice_status_update_channel)
        config.set(chid_section, "spotify", id_spotify_update_channel)
        with open("./token.ini", "w") as f:
            config.write(f)
    else:
        config = configparser.ConfigParser()
        config.read("./token.ini")
        token_section = "botinfo"
        token = config.get(token_section, "token")
    chid_dict = dict(config.items("chids"))

    mo = MemberObserver(command_prefix="!", chids=chid_dict)
    mo.run(token)


if __name__ == "__main__":
    main()
