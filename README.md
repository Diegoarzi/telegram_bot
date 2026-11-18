# Telegram Daily Helper Bot

A lightweight personal assistant bot for Telegram built with Python and `pyTelegramBotAPI`.

## Features
- **Real-time Weather:** Fetches current temperature and wind speed for any city using the Open-Meteo Geocoding and Forecast REST APIs.
- **Interactive To-Do List:** Add, view, toggle completion status, remove individual tasks, or clear the entire list using inline buttons and JSON persistence.

## Setup & Usage
1. Install dependencies:
   ```bash
   pip install -r requirements.txt

2. Set your Telegram Bot Token as an environment variable:

    Linux/macOS: export BOT_TOKEN="your_token_here"

    Windows (PowerShell): $env:BOT_TOKEN="your_token_here"

3. Run the bot:
   ```bash
   python bot.py
