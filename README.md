# Discord bot made in Python

A simple Discord bot built with discord.py, featuring modular cogs for easy extension and maintenance.

## Features
- Custom welcome message for new members
- Modular command and event handling using cogs
- Example custom help command
- Easy to extend with new commands and cogs

## Project Structure
```
bot.py            # Main bot entry point and setup

env/              # Virtual environment files included, so there is no need to create another

cogs/             # Folder for modular bot features (cogs)
  core.py         # Core features
  moderation.py   # Moderation commands
  stream.py       # Stream-related commands
  test.py         # Test commands
config.json       # Bot configuration (token, etc.)

README.md         # Project documentation (this file)
```

## Getting Started
1. **Clone the repository**

2. **Activate a virtual environment** (created files are already included, so there is no need for creation, but commands are included just in case)
   - **Windows (PowerShell):**
     ```powershell
     python -m venv env
     .\env\Scripts\Activate.ps1
     ```
   - **Windows (Command Prompt):**
     ```cmd
     python -m venv env
     .\env\Scripts\activate.bat
     ```
   - **Linux/macOS:**
     ```bash
     python3 -m venv env
     source env/bin/activate
     ```
3. **Install dependencies** (in case discord.py is not installed or virtual environment failed to be activated):
    - **Windows (PowerShell)**
      ```powershell
      py -3 -m pip install -U discord.py
      ```
    - **Library from PyPl**
      ```
      python3 -m pip install -U discord.py
      ```
4. **Configure your bot**
   - Create a `config.json` file with your bot token:
     ```json
     {
       "token": "YOUR_BOT_TOKEN"
     }
     ```
5. **Run the bot**
   ```powershell
   python bot.py
   ```

## Aditional documentation
Code writen using this sites
- [Python documentation](https://docs.python.org/)
- [Python tutorials for more specific information](https://www.w3schools.com/python/default.asp)
- [Discord.py documentation](https://discordpy.readthedocs.io/en/stable/index.html)

## License
This project is for educational purposes.

## Disclaimer
AI was only used for repetitive tasks (writing plain text and certain function outputs that includes text) and for some ideas about what this bot must have