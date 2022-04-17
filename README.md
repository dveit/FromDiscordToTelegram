# Description

This bot allows you to receive messages in Telegram from user defined Discord channels with the ability to configure important / ignored users.

You won't miss any important messages even if Discord notifications are off!

### It's not a Discord replacement so don't overload Discord API with requests or you can be banned! Use а small amount of tracked channels or increase checking delay.

## Installation
First of all you need to install **requirements** from file:
```bash
pip install -r requirements.txt
```

The next step is to edit the **settings.ini** file to add the name of the database and the Telegram bot token.

*By default the check is performed once a minute, but this time can be changed depending on the number of users and the channels they tracking.*

```ini
# tracking loops delay in seconds (lower than 60 not recommended)
checking_delay = 60

# name of your database with .db in the end
db_name = database.db

# token of your telegram bot
tg_bot_token = 123456:abcdef
```

The last step is to add commands directly to the telegram bot.
How to do this:
- enter the chat with BotFather
- select your bot
- click Edit Bot
- click Edit Commands

Then send following:
```
tracked - Shows tracked channels
add - Adds new channel
edit_users - Manages tracked / ignored users
settings - Changes Discord token or Timezone
pause - Pauses / resumes tracking
channel_info - Shows info from DB
delete - Deletes channel
delete_all - Deletes all tracked channels
cancel - Cancels addition / edition / deletion
```

These will be commands for interacting with your bot, you can arrange them in the order you want.

## Usage

To run bot use:

```bash
python3 bot.py
```

After that go to chat with your bot and press **start** button and it will tell you what to do next.

You will need PC during first launch to setup Discord token.

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.
