# Description
![Resulting example](https://cdn.discordapp.com/attachments/962649486226767953/965948194657812540/e4a37b83-7619-4c25-b317-ca622d78f2e4.jpeg)

This bot allows you to receive messages in Telegram from user-defined Discord channels with the ability to configure selected / ignored users.

You won't miss any important messages even if Discord notifications are turned off!

### This is not a replacement for Discord, so don't overload the Discord API with requests, or you might get banned! Use a small number of tracked channels or increase the checking delay.

## Installation

First you need to make sure that you are using **Python 3.6** or higher.

After that install **requirements** from file:
``` bash
pip install -r requirements.txt
```
The next step is to edit the **settings.ini** file to add the database name and Telegram bot token.

*By default, the check is performed once per minute, but this time can be changed depending on the number of users and the channels they follow.*

```ini
# delay of tracking loop in seconds (less than 60 is not recommended)
checking_delay = 60

# name of your database with .db at the end
db_name = database.db

# token of your telegram bot
tg_bot_token = 123456:abc-def
```
The last step is to add commands for interacting with the bot. For this you need to:
- enter chat with BotFather
- choose your bot
- click Edit bot
- click Edit commands

Then send the following:
```
tracked - Shows the channels being tracked
add - Adds a new channel
edit_users - Manages tracked / ignored users
settings - Changes Discord token or time zone
pause - Pauses / resumes tracking
channel_info - Shows information from the DB
rename - Changes server / channel name
delete - Deletes the channel
delete_all - Deletes all tracked channels
cancel - Cancels adding / editing / deleting
```
You can change the description or order of commands, but the left side must remain unchanged and all commands must be present in the list.

## Usage
To start the bot use:

``` bash
python3 bot.py
```

Open a dialogue with your bot.
If the dialog is not empty, clear history to make the **start** button available.
Then you just need to press the **start** button, and it will tell you what to do next.


## Contribute
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.