# Discord bot made in Python

A simple Discord bot built with discord.py, featuring modular cogs for easy extension and maintenance.

## Features
- Custom welcome message embed for new members
- Custom help command
- Level up function per user
- Stream tracker (only Twitch at this moment)

## Project Structure
```
bot.py            # Main bot entry point and setup

env/              # Virtual environment files (regenerate using requirements.txt for cross-platform compatibility)

cogs/             # Folder for modular bot features (cogs)
  core.py         # Core features (may create new files)
  moderation.py   # Moderation commands
  stream.py       # Stream-related commands
  test.py         # Test commands
config.json       # Bot configuration (token, etc.)
requirements.txt  # Project dependencies for easy virtual environment setup

README.md         # Project documentation (this file)
```

## Getting Started
1. **Clone the repository**

2. **Regenerate the virtual environment** (recommended for cross-platform compatibility)
   - **Windows (PowerShell):**
     ```powershell
     python -m venv env
     .\env\Scripts\Activate.ps1
     pip install -r requirements.txt
     ```
   - **Windows (CMD):**
     ```cmd
     python -m venv env
     .\env\Scripts\activate.bat
     pip install -r requirements.txt
     ```
   - **Linux/macOS:**
     ```bash
     python3 -m venv env
     source env/bin/activate
     pip install -r requirements.txt
     ```

3. **Activate the virtual environment** (if not already activated)
   - **Windows (PowerShell):**
     ```powershell
     .\env\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     .\env\Scripts\activate.bat
     ```
   - **Linux/macOS:**
     ```bash
     source env/bin/activate
     ```

**WARNING:** Virtual environment activation in Windows may fail because of the script execution policy the system has, so you may write this command in PowerShell if you get the "script disabled" error (only once):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
However, this is almost a security compromise, because you are allowing scripts to be executed in your system. If you write this, please be careful with what you execute from now on.\
\
**I will not be responsible for any damage done after writing that command**


4. **Create the bot app** ([This page](https://discordpy.readthedocs.io/en/stable/discord.html) offers all the information you may need about this. Will be updated if needed specific steps)

5. **Configure your bot**
   - Create a `config.json` file with your bot token (only "token" is the must have, write the others for extented functionality):
     ```json
     {
       "token": "YOUR_BOT_TOKEN",
       "welcome_channel_id": 1234567890123456789,
       "twitch_app_credentials": {
            "client_id": "TWITCH_APP_CLIENT_ID",
            "client_secret": "TWITCH_APP_CLIENT_SECRET"
       }
     }
     ```
6. **Run the bot**
   ```powershell
   python bot.py
   ```
   **On every execution you will need to activate the virtual environment first**, in Linux you can avoid that with the `./start_bot.sh` command, I'm working on a similar script for Windows.

## Aditional documentation
Code writen using this sites
- [Python documentation](https://docs.python.org/)
- [Python tutorials for more specific information](https://www.w3schools.com/python/default.asp)
- [Discord.py documentation](https://discordpy.readthedocs.io/en/stable/index.html)

## License
This project is for educational purposes.

## Disclaimer
AI was only used for repetitive tasks (writing plain text and certain function outputs that includes text) and for some ideas about what this bot must have
