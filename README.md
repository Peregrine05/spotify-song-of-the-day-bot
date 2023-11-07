# Setup

- Install Python. Version 3.8+ is recommended.
- If you are using Windows, then double-click on the file: `setup.bat`. Wait for the process to complete. When complete, the console window will close.
- Open the file `.env` with Notepad or another plain-text editor.
- Go to https://developer.spotify.com/dashboard and create a new Spotify application.
  - The `Redirect URI` will not be used, so set it to `http://localhost:3000` (or any unused port).
  - Select `Web API` to be used.
  - Read and agree to the developer agreement, and then save the application.
- In the page to which you are redirected, in the top-right corner of the page, click `Settings`.
  - Copy the `Client ID`, and paste it into the `.env` file, after `SPOTIPY_CLIENT_ID`, such that the line reads, for example: `SPOTIFY_APP_ID = 90d68b285173108bbe3349574480efd7`.
  - Copy the `Client secret`, and paste it into the `.env` file, after `SPOTIPY_CLIENT_SECRET`, such that the line reads, for example: `SPOTIFY_APP_SECRET = f8799153c6314f068e3d750bd166a47d`.
- Go to https://discord.com/developers/applications and create a new Discord application.
- Go to the `Bot` tab.
  - Name the bot however you want and upload an avatar, if desired.
  - Click `Reset Token`.
  - Copy the token, and paste it into the `.env` file, after `DISCORD_BOT_TOKEN`, such that the line reads, for example: `DISCORD_BOT_TOKEN = MTEyNjUzNTA5MDcyNjUwMjQwMA.GG_emt.cw3gIyIyMoHddWgcYRYle2Zq0bvLbh-n2bsi9w`.
- Save the `.env` file (Ctrl+S / `File > Save`).
- Go to the `OAuth2 > URL Generator` tab.
  - Select the scopes: `bot` and `applications.commands`.
  - Select the bot permissions: `Read Messages/View Channels`, `Send Messages`, and `Mention Everyone`.
  - At the bottom of the page, `Copy` the generated url. Then paste it into the address bar of your browser and press Enter.
  - Add the bot to the server of your choice.
- If you are using Windows, then double-click on the file: `start.bat`. The bot should shortly come online in the Discord server.

# Bot Commands

## Required commands

These commands must be used at least once in a server before the bot can function as intended.

- `/add_playlist`: Adds a playlist specified by its URL to the playlist pool of the server. The playlist must be publicly accessible.
- `/set_time`: Sets the time at which a random song is posted in the server. The time input is assumed to be in UTC (GMT time zone).
- `/set_channel`: Sets the channel in which the random song will be posted.

## Further configuration commands

These commands are used for further configuration or to view the current configuration.

- `/set_role`: Sets a role to be mentioned when a random song is posted.
- `/clear_role`: Clears the selected role from being mentioned when a random song is posted.
- `/remove_playlist`: Removes a playlist specified by its URL from the playlist pool of the server.
- `/current_configuration`: Retrieves the current configuration of the bot.
- `/exit_bot`: Exits the bot. The `start.bat` file must be run to start the bot again.
- `/next_time`: Retrieves the next time the bot will post a random song.
- `/random_track`: Manually retrieve a random song from the playlist pool.

---

The bot configuration is stored in `config.json`. Modifying this file directly is not supported.
