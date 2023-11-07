import datetime
import json
import os
import random
import shutil
import time

import discord
import discord.ext.tasks
import dotenv
import spotipy.oauth2


def get_playlist_id(playlist_url):
    if "spotify.com/playlist/" not in playlist_url:
        raise ValueError(
            "The provided URL is not a valid Spotify playlist URL.")
    return playlist_url.partition("playlist/")[2].partition("?")[0]


class SOTDBot(discord.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spotipy_app = spotipy.Spotify(
            auth_manager=spotipy.oauth2.SpotifyClientCredentials()
        )
        self.config = {}
        self.times = {}
        self.next_time = None
        self.load_config()
        self.load_times()

    async def on_ready(self):
        self.post_random_song.start()

    def load_config(self):
        try:
            with open("config.json", "rt", encoding="utf8") as config_file:
                config = json.load(config_file)
                self.config.clear()
                self.config.update(config)
        except FileNotFoundError:
            with open("config.json", "wt", encoding="utf8") as file:
                json.dump({}, file, indent=3)

    def save_config(self):
        shutil.copy("config.json", "config.backup")
        with open("config.json", "wt", encoding="utf8") as config_file:
            json.dump(self.config, config_file, indent=3)

    def load_times(self):
        self.times.clear()
        for guild_id, guild_config in self.config.items():
            try:
                time = guild_config["time"]
            except KeyError:
                continue

            hour = int(time.partition(":")[0])
            minute = int(time.partition(":")[2])
            time_datetime_time = datetime.time(hour=hour, minute=minute)

            try:
                guild_id_list = self.times[time_datetime_time]
            except KeyError:
                guild_id_list = []
                self.times.update({time_datetime_time: guild_id_list})

            if guild_id not in guild_id_list:
                guild_id_list.append(guild_id)

        self.set_next_time()
        if len(self.times.keys()):
            self.post_random_song.change_interval(time=list(self.times.keys()))

    def set_next_time(self):
        current_time = time.gmtime(time.time())
        hour = current_time.tm_hour
        minute = current_time.tm_min

        current_total_minutes = minute + (hour * 60)

        time_list = sorted(
            self.times.keys(),
            key=lambda x: (((x.minute + (x.hour * 60))
                            - current_total_minutes) % 1440 + 1440) % 1440)
        try:
            self.next_time = time_list[0]
        except IndexError:
            self.next_time = None

    def update_playlists(self, guild_id, playlist):
        try:
            guild_config = self.config[guild_id]
        except KeyError:
            guild_config = {}
            self.config.update({guild_id: guild_config})

        try:
            playlist_config = guild_config["playlists"]
        except KeyError:
            playlist_config = []
            guild_config.update({"playlists": playlist_config})

        playlist_id = get_playlist_id(playlist)
        if playlist_id not in playlist_config:
            if self.is_public_playlist(playlist_id):
                playlist_config.append(playlist_id)
            else:
                raise ValueError("The provided playlist is not public.")
        else:
            raise ValueError(
                "The provided playlist has already been added to the pool.")

        self.save_config()

    def remove_playlist(self, guild_id, playlist):
        playlist_id = get_playlist_id(playlist)
        try:
            if playlist_id in self.config[guild_id]["playlists"]:
                self.config[guild_id]["playlists"].remove(playlist_id)
                self.save_config()
                return None
        except KeyError:
            pass
        raise ValueError(
            "The provided playlist is already not present in the pool.")

    def set_channel(self, guild_id, channel_id):
        try:
            guild_config = self.config[guild_id]
        except KeyError:
            guild_config = {}
            self.config.update({guild_id: guild_config})

        guild_config.update({"channel": channel_id})

        self.save_config()

    def set_role(self, guild_id, role_id):
        try:
            guild_config = self.config[guild_id]
        except KeyError:
            guild_config = {}
            self.config.update({guild_id: guild_config})

        guild_config.update({"mention_role": role_id})

        self.save_config()

    def clear_notification_role(self, guild_id):
        try:
            self.config[guild_id].pop("mention_role")
        except KeyError:
            return

        self.save_config()


    def set_time(self, guild_id, time):
        try:
            guild_config = self.config[guild_id]
        except KeyError:
            guild_config = {}
            self.config.update({guild_id: guild_config})

        guild_config.update({"time": time})

        self.save_config()
        self.load_times()

    def get_time_config(self, guild_id):
        try:
            return self.config[guild_id].get("time")
        except KeyError:
            return None

    def get_channel_config(self, guild_id):
        try:
            return self.config[guild_id].get("channel")
        except KeyError:
            return None

    def get_role_config(self, guild_id):
        try:
            return self.config[guild_id].get("mention_role")
        except KeyError:
            return None

    def get_playlists(self, guild_id):
        try:
            playlists = self.config[guild_id].get("playlists")
        except KeyError:
            return None
        if not len(playlists):
            return None
        return playlists

    def is_public_playlist(self, playlist_id: str):
        try:
            self.spotipy_app.playlist(playlist_id=playlist_id)
        except spotipy.SpotifyException:
            return False
        return True

    def get_random_song(self, guild_id):
        try:
            playlists = self.config[guild_id]["playlists"]
        except KeyError:
            return None
        if not len(playlists):
            return None
        aggregate_playlist_items = []
        for playlist in playlists:
            offset = 0
            while True:
                playlist_items = self.spotipy_app.playlist_items(
                    playlist_id=playlist,
                    limit=50,
                    offset=offset
                )
                for item in playlist_items["items"]:
                    url = item["track"]["external_urls"]["spotify"]
                    aggregate_playlist_items.append(url)
                if playlist_items["next"] is None:
                    break
                offset += 50
                time.sleep(1.5)
        if not len(aggregate_playlist_items):
            return None
        track = random.choice(aggregate_playlist_items)
        return track

    @discord.ext.tasks.loop(
        hours=24
    )
    async def post_random_song(self):
        guild_ids = self.times.get(self.next_time)
        if guild_ids is None:
            return
        for guild_id in guild_ids:
            guild = self.get_guild(int(guild_id))
            if guild is None:
                continue

            guild_config = self.config[guild_id]

            channel_id = guild_config.get("channel")
            if channel_id is None:
                continue
            channel = guild.get_channel(channel_id)
            if channel is None:
                continue

            track = self.get_random_song(guild_id)
            if track is None:
                continue

            role_id = guild_config.get("mention_role")
            if role_id is not None:
                if role_id == "@everyone":
                    role_mention = role_id
                else:
                    role_mention = guild.get_role(role_id).mention
            else:
                role_mention = ""

            message = f"{role_mention} {track}"

            await channel.send(
                content=message,
                allowed_mentions=discord.AllowedMentions(
                    everyone=True,
                    roles=True
                )
            )
        self.set_next_time()


if __name__ == "__main__":
    dotenv.load_dotenv()

    discord_bot_token = os.getenv("DISCORD_BOT_TOKEN")
    bot = SOTDBot()

    @bot.slash_command(
        name="add_playlist",
        description="Add a public playlist to the playlist pool."
    )
    async def add_playlist(
            ctx: discord.ApplicationContext,
            playlist: discord.Option(
                str,
                name="playlist_url",
                description="URL of the public playlist to add",
                required=True
            )
    ):
        try:
            bot.update_playlists(str(ctx.guild_id), playlist)
            message = f"Successfully added playlist: `{playlist}` to the pool."
        except ValueError as e:
            message = str(e)
        await ctx.respond(message)


    @bot.slash_command(
        name="remove_playlist",
        description="Remove a playlist from the playlist pool."
    )
    async def remove_playlist(
            ctx: discord.ApplicationContext,
            playlist: discord.Option(
                str,
                name="playlist_url",
                description="URL of the playlist to remove",
                required=True
            )
    ):
        try:
            bot.remove_playlist(str(ctx.guild_id), playlist)
            message = (f"Successfully removed playlist: `{playlist}` from the "
                       f"pool.")
        except ValueError as e:
            message = str(e)
        await ctx.respond(message)


    @bot.slash_command(
        name="set_channel",
        description="Set the channel to which to post songs."
    )
    async def set_channel(
            ctx: discord.ApplicationContext,
            channel: discord.Option(
                discord.TextChannel,
                name="channel",
                description="Text channel to which to post songs",
                required=True
            )
    ):
        channel: discord.TextChannel

        if (channel.permissions_for(ctx.me).send_messages
                and channel.permissions_for(ctx.me).view_channel):
            bot.set_channel(str(ctx.guild_id), channel.id)
            await ctx.respond(
                f"Channel to which to post songs has been set to "
                f"{channel.mention}."
            )
        else:
            await ctx.respond(
                f"The permissions of {channel.mention} prevent the the bot "
                f"from posting songs there. Please choose a different channel "
                f"or change the permissions."
            )


    @bot.slash_command(
        name="set_role",
        description="Set a role to be notified when a song is posted."
    )
    async def set_role(
            ctx: discord.ApplicationContext,
            role: discord.Option(
                discord.Role,
                name="role",
                description="Role to be notified when a song is posted",
                required=True
            )
    ):
        role: discord.Role
        if role.name == "@everyone":
            role_id = "@everyone"
            role_mention = role_id
        else:
            role_id = role.id
            role_mention = role.mention
        bot.set_role(str(ctx.guild_id), role_id)
        await ctx.respond(f"Set the notification role to {role_mention}.")

    @bot.slash_command(
        name="clear_role",
        description="Clears any selected role from being notified when a song "
                    "is posted."
    )
    async def clear_role(ctx: discord.ApplicationContext):
        bot.clear_notification_role(str(ctx.guild_id))
        await ctx.respond("Cleared any selected role from being notified when "
                          "a song is posted.")

    @bot.slash_command(
        name="set_time",
        description="Set the daily time at which a random song will be posted"
    )
    async def set_time(
            ctx: discord.ApplicationContext,
            hour: discord.Option(
                int,
                name="hour",
                description="Hour of the day (UTC)"
            ),
            minute: discord.Option(
                int,
                name="minute",
                description="Minute of the hour"
            )
    ):
        if not 0 <= hour <= 23:
            await ctx.respond("Invalid value for `hour`. It must be a value "
                              "greater than or equal to *0* and less than or "
                              "equal to *23*")
            return

        if not 0 <= minute <= 59:
            await ctx.respond("Invalid value for `minute`. It must be a value "
                              "greater than or equal to *0* and less than or "
                              "equal to *59*")
            return
        str_time = f"{str(hour).zfill(2)}:{str(minute).zfill(2)}"
        bot.set_time(str(ctx.guild_id), str_time)
        await ctx.respond(f"Set daily time to `{str_time}` (UTC).")

    @bot.slash_command(
        name="random_track",
        description="Retrieve a random track from the playlist pool"
    )
    async def random_track(ctx: discord.ApplicationContext):
        await ctx.respond("Please wait")
        track = bot.get_random_song(str(ctx.guild_id))
        if track is None:
            message = ("No non-empty playlists have been added to the "
                       "playlist pool. Use `/add_plalist` to add playlists to "
                       "the playlist pool.")
        else:
            message = track
        await ctx.interaction.edit_original_response(content=message)

    @bot.slash_command(
        name="next_time",
        description="Retrieve the next time (UTC) when the bot will attempt "
                    "to post a song"
    )
    async def next_time(ctx: discord.ApplicationContext):
        time_next = bot.get_time_config(str(ctx.guild_id))
        if time_next is None:
            await ctx.respond("A daily time has not been set. Use `/set_time` "
                              "to set a daily time.")
            return
        channel = bot.get_channel_config(str(ctx.guild_id))
        if channel is None:
            await ctx.respond("A channel in which to post the daily song has "
                              "not been set. Use `/set_channel` to set the "
                              "channel.")
        await ctx.respond(content=f"The bot will attempt to post the next "
                                  f"song at `{time_next}` (UTC)")

    @bot.slash_command(
        name="current_configuration",
        description="Retrieve the current configuration for this server"
    )
    async def current_config(ctx: discord.ApplicationContext):
        time_config = bot.get_time_config(str(ctx.guild_id))
        channel_config = bot.get_channel_config(str(ctx.guild_id))
        role_config = bot.get_role_config(str(ctx.guild_id))
        playlist_config = bot.get_playlists(str(ctx.guild_id))

        if time_config is not None:
            time_config_message = (f"The daily time is set to: "
                                   f"`{time_config}` (UTC).")
        else:
            time_config_message = ("A daily time has not been set. Use "
                                   "`/set_time` to set a daily time.")

        if channel_config is not None:
            channel_config_message = (f"The channel in which the daily song "
                                      f"will be posted is set to "
                                      f"<#{channel_config}>.")
        else:
            channel_config_message = ("A channel in which to post the daily "
                                      "song has not been set. Use "
                                      "`/set_channel` to set the channel.")

        if role_config is not None:
            if role_config == "@everyone":
                role_mention = role_config
            else:
                role_mention = f"<@&{role_config}>"
            role_config_message = (f"The notification role is set to "
                                   f"{role_mention}.")
        else:
            role_config_message = ("A notification role has not been set. "
                                   "Use `/set_role` to set a notification "
                                   "role.")

        if playlist_config is not None:
            playlist_config_message = (
                    "The playlist pool contains the following playlists:\n"
                    + ''.join(f'  - <https://open.spotify.com/playlist/'
                              f'{playlist_id}>\n'
                              for playlist_id in playlist_config)
            )
        else:
            playlist_config_message = ("The playlist pool contains no "
                                       "playlists. Use `/add_playlist` to add "
                                       "playlists to the playlist pool.")

        message = f"**Current configuration**:\n" \
                  f"- {time_config_message}\n" \
                  f"- {channel_config_message}\n" \
                  f"- {role_config_message}\n" \
                  f"- {playlist_config_message}"

        await ctx.respond(message)

    @bot.slash_command(
        name="exit_bot",
        description="Exits the bot."
    )
    async def exit_bot(ctx):
        await ctx.respond("Exiting bot")
        await bot.close()

    bot.run(discord_bot_token)
