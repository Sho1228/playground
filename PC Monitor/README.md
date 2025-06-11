# PC Monitor with Discord Bot

Please note that this is for educational purposes for those who are studying about how different Python packages and discord bots work.

## Installation

1. Install Python 3.10
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a Discord bot:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" section and create a bot
   - Copy the bot token
   - Go to the "OAuth2" section"
   - Select the needed permission and copy the URL shown
   -Copy and paste the URL on the server that you want to install the bot to
   - Click the link and authenticate the bot
4. Create a `.env` file in the project directory and add your bot token:
   ```
   DISCORD_TOKEN=your_discord_bot_token_here
   ```
5. Invite the bot to your server with the following permissions:
   - Send Messages
   - Attach Files
   - Read Message History

## Usage

To run the bot, use:
```bash
python3 bot.py
```

Available commands:
- `/bot ss` - Takes a screenshot of the current screen
- `/bot mic` - Records 10 seconds of audio from the microphone
- `/bot volume <0-100>` - Sets system volume (0-100%)
- `/bot sleep` - Puts the computer to sleep
- `/bot type <text>` - Types the specified text
- `/bot media <play/next/prev>` - Controls media playback
- `/bot url <url>` - Opens the specified URL in default browser
- `/bot launch <app_name>` - Launches the specified application
- `/bot kill <app_name>` - Kills the specified application
- `/bot processes` - Lists top 10 processes by CPU usage
- `/bot ip` - Shows the system's IP address
- `/bot sysinfo` - Shows detailed system information
- `/bot uptime` - Shows system uptime
- `/bot camera` - Takes a photo using the webcam
- `/bot keylogger <start/stop>` - Starts or stops keylogging

## Features

- Actions with Commands
- Start up notification
- Screenshot capture
- Audio recording
- Volume control
- System sleep
- Keyboard input simulation
- Media playback control
- URL opening
- Application management
- Process monitoring
- System information
- Camera capture
- Keylogging (for educational purposes)
- Automatic file cleanup
- Error handling

## FYI

This bot is designed exclusively for macOS systems and is currently in an experimental phase. Please note the following important points:

- This is a development project and should be used responsibly
- The bot requires appropriate permissions to function properly
- Some features may not work as expected due to the experimental nature
- Use this tool only for legitimate purposes and with proper authorization
- *The developers are not responsible for any misuse of this software*

### Warning: Unauthorized use of this bot, especially for malicious purposes, may violate laws and ToS.

## Please use this tool responsibly and ethically.
