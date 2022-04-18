import requests
import json
import asyncio
import configparser
from datetime import datetime, timedelta
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram import Bot, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from db import BotDB, create_db



config = configparser.ConfigParser()
config.read("settings.ini")

delay = int(config['GENERAL']['checking_delay'])
db_name = config['GENERAL']['db_name']
tg_bot_token = config['GENERAL']['tg_bot_token']

create_db(db_name)

BotDB = BotDB(db_name)
bot = Bot(token=tg_bot_token)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class UserAdditionForm(StatesGroup):
    ds_token = State()
    tz_delta = State()


class UserSettingsForm(StatesGroup):
    selected_option = State()
    ds_token = State()
    tz_delta = State()


class ChannelAdditionForm(StatesGroup):
    server_id = State()
    channel_id = State()


class ChannelEditionForm(StatesGroup):
    db_id = State()
    db_column = State()
    editing_option = State()
    ds_user_id = State()


class ChannelInfoGettingForm(StatesGroup):
    db_id = State()


class ChannelDeleteForm(StatesGroup):
    channel_id = State()


class AllChannelsDeleteForm(StatesGroup):
    confirmation = State()
 
 
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not BotDB.user_exists(message.from_user.id): 
        await UserAdditionForm.ds_token.set()
        await bot.send_message(message.from_user.id, "Send me Discord token.\nDon't know how to get it?\nWatch here (PC required) https://gist.github.com/9sv/3272bc9a63d64b1eb93286ffb3217130")
    else:
        await bot.send_message(message.chat.id, f"Welcome back, {message.from_user.full_name}!")


@dp.message_handler(state=UserAdditionForm.ds_token)
async def getting_discord_token(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['discord_token'] = message.text
        response = await is_token_legit(message.text)
        if response:
            await bot.send_message(message.chat.id, f"Recognized as {response}")
            await UserAdditionForm.next()
            await bot.send_message(message.chat.id, "Send me your timezone delta.\nExample:\n+3 for Moscow\n-4 for New-York")
        else:
            await bot.send_message(chat_id=message.chat.id, text="Wrong token.\nAccont was not created.\nUse /start to retry.")
            await state.finish()


@dp.message_handler(state=UserAdditionForm.tz_delta)
async def getting_discord_token(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['timezone_delta'] = int(message.text)
        if data['timezone_delta'] in range(-12, 13):
            BotDB.add_user(message.from_user.id, data['discord_token'], data['timezone_delta'])
            await bot.send_message(message.chat.id, "Success!")
            await bot.send_message(message.chat.id, "Now you can interact with the bot using the menu in the bottom left corner.")
            await bot.send_message(message.chat.id, "Don't forget to turn on developer mode in Discord\nhttps://support.discord.com/hc/article_attachments/1500008304041/Screenshot_3.png")
        else:
            await bot.send_message(message.chat.id, "Wrong input.\nAccont was not created.\nType /start to retry.")
    await state.finish()


@dp.message_handler(commands=['pause'])
async def start(message: types.Message):
    if BotDB.is_paused(message.from_user.id)[0][0]: 
        BotDB.update_is_paused(message.from_user.id, 0)
        await bot.send_message(message.from_user.id, "Tracking resumed")
    else:
        BotDB.update_is_paused(message.from_user.id, 1)
        await bot.send_message(message.from_user.id, "Tracking paused")


@dp.message_handler(commands=['settings'])
async def user_settings(message: types.Message):
    await UserSettingsForm.selected_option.set()
    button_discord_token = KeyboardButton('Discord token')
    button_tz_delta = KeyboardButton('Timezone')
    
    column_selection = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    column_selection.add(button_discord_token, button_tz_delta)
    await message.answer("What do you want to edit?", reply_markup=column_selection)


@dp.message_handler(state=UserSettingsForm.selected_option)
async def getting_option(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['selected_option'] = message.text
        if data['selected_option'] == 'Discord token':
            await UserSettingsForm.next()
            await bot.send_message(message.from_user.id, "Send me Discord token.\nDon't know how to get it?\nWatch here (PC required) https://gist.github.com/9sv/3272bc9a63d64b1eb93286ffb3217130")
        elif data['selected_option'] == 'Timezone':
            await UserSettingsForm.next()
            await UserSettingsForm.next()
            await bot.send_message(message.chat.id, "Send me your timezone delta.\nExample:\n+3 for Moscow\n-4 for New-York")
        else:
            await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Wrong option. Edition canceled.")
            await state.finish()


@dp.message_handler(state=UserSettingsForm.ds_token)
async def getting_ds_token(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['discord_token'] = message.text
        response = await is_token_legit(ds_token=data['discord_token'])
        if response:
            BotDB.update_ds_token(message.from_user.id, data['discord_token'])
            await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text=f"Recognized as {response}\nToken was updated!")
        else:
            await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Wrong token. Edition canceled.")
    await state.finish()


@dp.message_handler(state=UserSettingsForm.tz_delta)
async def getting_tz_delta(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data['timezone_delta'] = int(message.text)
            if data['timezone_delta'] in range(-12, 13):
                BotDB.update_tz_delta(message.from_user.id, data['timezone_delta'])
                await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Timezone was updated!")
            else:
                await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Wrong timezone. Editing canceled.")
        except ValueError:
            await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Timezone value is not integer. Editing canceled.")
    await state.finish()


@dp.message_handler(state='*', commands='cancel')
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Action canceled.")
    await state.finish()


@dp.message_handler(commands="add")
async def adding_channel(message: types.Message):
    await ChannelAdditionForm.server_id.set()
    await bot.send_message(message.chat.id, "Send me the Discord server ID")


@dp.message_handler(state=ChannelAdditionForm.server_id)
async def getting_channel_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if len(message.text) == 18 and (message.text).isdigit():
            data['server_id'] = message.text
            ds_token = BotDB.get_discord_token(message.from_user.id)[0][0]
            server_name = await get_server_name(ds_token=ds_token, server_id=data['server_id'])
            if server_name:
                await ChannelAdditionForm.next()
                await bot.send_message(message.chat.id, f"Recognized as {server_name}\n\nSend me the channel ID on this server")
            else:
                await bot.send_message(message.chat.id, "Wrong server ID or no access to server. Addition canceled.")
                await state.finish()
        else:
            await bot.send_message(message.chat.id, "Wrong server ID. Addition canceled.")
            await state.finish()


@dp.message_handler(state=ChannelAdditionForm.channel_id)
async def getting_channel_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if len(message.text) == 18 and (message.text).isdigit():
            data['channel_id'] = message.text
            ds_token = BotDB.get_discord_token(message.from_user.id)[0][0]
            channel_name = await get_channel_name(ds_token=ds_token, channel_id=data['channel_id'])
            if channel_name:
                await bot.send_message(message.chat.id, f"Recognized as {channel_name}")
                data['tracked_users'] = ""
                data['ignored_users'] = ""
                data['last_message_id'] = await get_last_message_id(ds_token, int(data['channel_id']))
                BotDB.add_channel(message.from_user.id, int(data['server_id']), int(data['channel_id']), data['tracked_users'], data['ignored_users'], data['last_message_id'])
                await bot.send_message(message.chat.id, "Channel added!")
            else:
                await bot.send_message(message.chat.id, "Wrong channel ID or no access to channel. Addition canceled.")
        else:
            await bot.send_message(message.chat.id, "Wrong channel ID. Addition canceled.")
    await state.finish()


@dp.message_handler(commands="edit_users")
async def adding_channel(message: types.Message):
    await ChannelEditionForm.db_id.set()
    await bot.send_message(message.chat.id, "Send me the ID of DB record")


@dp.message_handler(state=ChannelEditionForm.db_id)
async def getting_channel_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['db_id'] = message.text
        if data['db_id'].isdigit():
            await ChannelEditionForm.next()
            button_tracked_users = KeyboardButton('tracked users')
            button_ignored_users = KeyboardButton('ignored users')
            
            column_selection = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            column_selection.add(button_tracked_users, button_ignored_users)
            await message.answer("What do you want to edit?", reply_markup=column_selection)
        else:
            await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Wrong ID. Edition canceled.")
            await state.finish()


@dp.message_handler(state=ChannelEditionForm.db_column)
async def getting_channel_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['db_column'] = message.text
        if data['db_column'] == 'tracked users' or data['db_column'] == 'ignored users':
            await ChannelEditionForm.next()
            button_append_new_user = KeyboardButton('append new user')
            button_delete_existing_user = KeyboardButton('delete existing user')
            button_clear_list = KeyboardButton('clear list')
            
            editing_option = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
            editing_option.add(button_append_new_user, button_delete_existing_user, button_clear_list)
            await message.answer("Select option", reply_markup=editing_option)
        else:
            await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Wrong db column name. Edition canceled.")
            await state.finish()


@dp.message_handler(state=ChannelEditionForm.editing_option)
async def getting_user_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['editing_option'] = message.text
        if data['editing_option'] == 'append new user' or data['editing_option'] == 'delete existing user':
            await ChannelEditionForm.next()
            await bot.send_message(message.chat.id, "Send me the ID of Discord user")
        elif data['editing_option'] == 'clear list':
            if data['db_column'] == 'tracked users':
                cell_content = BotDB.get_tracked_users(data['db_id'], message.chat.id)[0][0]
                cell_content = ""
                BotDB.update_tracked_user(data['db_id'], message.chat.id, cell_content)
                await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Tracked users list was cleared!")
            if data['db_column'] == 'ignored users':
                cell_content = BotDB.get_ignored_users(data['db_id'], message.chat.id)[0][0]
                cell_content = ""
                BotDB.update_ignored_user(data['db_id'], message.chat.id, cell_content)
                await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Ignored users list was cleared!")
            await state.finish()
        else:
            await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Wrong editing option. Edition canceled.")
            await state.finish()


@dp.message_handler(state=ChannelEditionForm.ds_user_id)
async def getting_last_message_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if len(message.text) == 18 and (message.text).isdigit():
            data['ds_user_id'] = message.text
            if data['db_column'] == 'tracked users':
                if data['editing_option'] == 'append new user':
                    cell_content = BotDB.get_tracked_users(data['db_id'], message.chat.id)[0][0]
                    cell_content += data['ds_user_id'] + ','
                    BotDB.update_tracked_user(data['db_id'], message.chat.id, cell_content)
                    await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Tracked users list was updated!")
                elif data['editing_option'] == 'delete existing user':
                    cell_content = BotDB.get_tracked_users(data['db_id'], message.chat.id)[0][0]
                    cell_content = cell_content.replace(f"{data['ds_user_id']},", "")
                    BotDB.update_tracked_user(data['db_id'], message.chat.id, cell_content)
                    await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="User was removed from tracked list!")
                await state.finish()
            elif data['db_column'] == 'ignored users':
                if data['editing_option'] == 'append new user':
                    cell_content = BotDB.get_ignored_users(data['db_id'], message.chat.id)[0][0]
                    if len(cell_content) > 0:
                        cell_content += data['ds_user_id'] + ','
                    else:
                        cell_content = data['ds_user_id'] + ','
                    BotDB.update_ignored_user(data['db_id'], message.chat.id, cell_content)
                    await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Ignored users list was updated!")
                elif data['editing_option'] == 'delete existing user':
                    cell_content = BotDB.get_ignored_users(data['db_id'], message.chat.id)[0][0]
                    cell_content = cell_content.replace(f"{data['ds_user_id']},", "")
                    BotDB.update_ignored_user(data['db_id'], message.chat.id, cell_content)
                    await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="User was removed from ignored list!")
                await state.finish()
        else:
            await bot.send_message(chat_id=message.chat.id, reply_markup=ReplyKeyboardRemove(), text="Wrong ID. Edition canceled.")
            await state.finish()


@dp.message_handler(commands="tracked")
async def show_tracked_channels(message: types.Message):
    tracked_channels = BotDB.get_tracked_channels(message.from_user.id)
    tracked_all = []
    tracked_by_users = []
    for tpl in tracked_channels:
        db_id, server_id, channel_id, tracked_users, ignored_users, last_message_id = tpl
        ds_token = BotDB.get_discord_token(message.from_user.id)[0][0]
        server_name = await get_server_name(ds_token, server_id)
        if not server_name:
            server_name = "⚠️ Unaccessable server ⚠️"
        channel_name = await get_channel_name(ds_token, channel_id)
        if not channel_name:
            channel_name = "⚠️ Unaccessable channel ⚠️"
        tracked_users_count = int(len(tracked_users)/19)
        ignored_users_count = int(len(ignored_users)/19)
        if len(tracked_users) == 0:
            tracked_all.append(f'[{db_id}] {server_name} -> {channel_name} [🚫{ignored_users_count}]')
        else:
            tracked_by_users.append(f'[{db_id}] {server_name} -> {channel_name} [✅{tracked_users_count}] [🚫{ignored_users_count}]')
    header = "✅ - tracked users count\n🚫 - ignored users count\n\nUse /channel_info to get list of tracked and ignored users\n\n"
    str_all = '\n'.join(tracked_all)
    str_all = 'Messages from everyone:\n' + str_all
    splitter = '\n\n--------------------------------------------\n\n'
    str_by_users = '\n'.join(tracked_by_users)
    str_by_users = 'Messages from tracked users:\n' + str_by_users

    if tracked_all and tracked_by_users:
        result = header + str_all + splitter + str_by_users
    elif tracked_all and not tracked_by_users:
        result = header + str_all
    elif tracked_by_users and not tracked_all:
        result = header + str_by_users
    else:
        result = "There are no tracked channels."
    
    await bot.send_message(message.chat.id, result)


@dp.message_handler(commands="channel_info")
async def delete_channel(message: types.Message):
    await ChannelInfoGettingForm.db_id.set()
    await bot.send_message(message.chat.id, "Send me DB index of channel thah you want to delete\n\nExample: send 4 for [4] Servername -> Channelname")
@dp.message_handler(state=ChannelInfoGettingForm.db_id)
async def get_db_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        result = []
        data['id'] = int(message.text)
        await state.finish()
        ds_token = BotDB.get_discord_token(message.from_user.id)[0][0]
        server_id, channel_id, tracked_users, ignored_users, last_message_id = BotDB.get_channel_info(data['id'], message.from_user.id)[0]
        server_name = await get_server_name(ds_token, server_id)
        channel_name = await get_channel_name(ds_token, channel_id)
        tracked_users = tracked_users.replace(",", "\n")
        ignored_users = ignored_users.replace(",", "\n")
        result.append(f"Server ID: {server_id}\n")
        if server_name:
            result.append(f"Server name: {server_name}\n")
        else:
            result.append("Unaccessable server")
        result.append(f"Channel ID: {channel_id}\n")
        if channel_name:
            result.append(f"Channel name: {channel_name}\n")
        else:
            result.append("Unaccessable channel")
        result.append(f"Last message ID in DB: {last_message_id}\n")
        result.append("\n\n")
        result.append(f"✅ Tracked users:\n{tracked_users}\n")
        result.append(f"🚫 Ignored users:\n{ignored_users}\n")
        
        
        final_message = ''.join(result)
        await bot.send_message(message.chat.id, final_message) 


@dp.message_handler(commands="delete")
async def delete_channel(message: types.Message):
    await show_tracked_channels(message)
    await ChannelDeleteForm.channel_id.set()
    await bot.send_message(message.chat.id, "Send me DB index(db_id) of channel thah you want to delete")


@dp.message_handler(state=ChannelDeleteForm.channel_id)
async def delete_channel_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['id'] = int(message.text)
        BotDB.delete_channel(message.from_user.id, data['id'])
        await bot.send_message(message.chat.id, "Channel deleted!") 
        await state.finish()


@dp.message_handler(commands="delete_all")
async def delete_channel(message: types.Message):
    await AllChannelsDeleteForm.confirmation.set()
    await bot.send_message(message.chat.id, "Are you sure?\nY/N")


@dp.message_handler(state=AllChannelsDeleteForm.confirmation)
async def confirm_deletion(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['confirmation'] = message.text
        if data['confirmation'] == 'Y':
            BotDB.delete_all_channels(message.from_user.id)
            await bot.send_message(message.chat.id, "All tracked channels were deleted!")
            await state.finish()
        else:
            await bot.send_message(message.chat.id, "Deletion canceled.")
            await state.finish()


async def is_token_legit(ds_token:str) -> str:
    """Returns ds identificator(True) if token is legit False otherwise"""
    
    headers = {
        'authorization': ds_token,
        }
    r = requests.get(f"https://discord.com/api/v9/users/@me", headers=headers)
    data = json.loads(r.text)
    try:
        username = data['username']+"#"+data['discriminator']
        return username
    except KeyError:
        return False


async def get_server_name(ds_token, server_id):
    """Returns servername(True) server is accessable and False otherwise"""
    
    headers = {
        'authorization': ds_token,
        }
    r = requests.get(f"https://discord.com/api/v9/guilds/{server_id}/preview", headers=headers)
    data = json.loads(r.text)
    try:
        server_name = data['name']
        return server_name
    except KeyError:
        return False


async def get_channel_name(ds_token, channel_id):
    """Returns channel_name(True) if channel is accessable and False otherwise"""
    
    headers = {
        'authorization': ds_token,
        }
    r = requests.get(f"https://discord.com/api/v9/channels/{channel_id}", headers=headers)
    data = json.loads(r.text)
    try:
        channel_name = data['name']
        return channel_name
    except KeyError:
        return False


async def get_username_on_server(ds_token:str, ds_server_id, ds_user_id) -> str:
    """Returns users nickname on given server"""
    
    headers = {
        'authorization': ds_token,
        }
    
    r = requests.get(f"https://discord.com/api/v9/users/{ds_user_id}/profile?guild_id={ds_server_id}", headers=headers)
    json_data = json.loads(r.text)
    
    try:
        username_on_server = list(filter(lambda item: item['id'] == str(ds_server_id), json_data['mutual_guilds']))[0]['nick']
        ds_username = json_data['user']['username']
        if username_on_server is not None:
            servername = f"{username_on_server} ({ds_username}#{json_data['user']['discriminator']})"
        else:
            servername = f"{ds_username} ({ds_username}#{json_data['user']['discriminator']})"
        return servername
    except KeyError:
        print(KeyError, "\n", json_data)


async def get_discord_messages(ds_token:str, ds_channel_id:int, last_message_id:int) -> list:
    """Returns a list of dicts containing new messages data"""
    
    headers = {
        'authorization': ds_token,
        }
    try:
        r = requests.get(f"https://discord.com/api/v9/channels/{ds_channel_id}/messages?limit={100}&after={last_message_id}", headers=headers)
        list_of_dicts = json.loads(r.text)[::-1]
        return list_of_dicts
    except TypeError:
        print("Error! Wrong Discord token or user is not on server or no premission to read channel!")
        return []


async def get_last_message_id(ds_token:str, ds_channel_id:int) -> int:
    """Returns id of last message in channel"""
    
    headers = {
        'authorization': ds_token,
        }
    r = requests.get(f"https://discord.com/api/v9/channels/{ds_channel_id}/messages?limit={1}", headers=headers)
    try:
        message_data = json.loads(r.text)[0]
        received_message_id = int(message_data['id'])
        return received_message_id
    except KeyError:
        print("Access denied! Wrong channel id or token!")
        return 0


async def processing(tg_user_id:int, ds_token:str, tz_delta:int):
    """Getting list of tracked channel and forming message """
    
    tracked_list = BotDB.get_tracked_channels(tg_user_id)
    for row in tracked_list:
        db_id, server_id, channel_id, tracked_users, ignored_users, last_message_id = row
        server_name = await get_server_name(ds_token, server_id)
        channel_name = await get_channel_name(ds_token, channel_id)
        if server_name and channel_name:
            data = await get_discord_messages(ds_token, channel_id, last_message_id)
            usernames = {}
            if 0 < len(data):
                for raw_message in data:
                    message_parts = []
                    received_message_id = int(raw_message['id'])
                    author_id = raw_message['author']['id']
                    if len(ignored_users) == 0 or author_id not in ignored_users:
                        if author_id in usernames:
                            author_username = usernames[author_id]
                        else:
                            author_username = await get_username_on_server(ds_token, server_id, author_id)
                            if author_username is not None:
                                usernames[author_id] = author_username
                            else:
                                author_username = raw_message['author']['username']
                        message_content = raw_message['content']
                        timestamp = raw_message['timestamp']
                        timestamp = datetime.fromisoformat(timestamp.replace("T", " ").replace("+00:00", ""))
                        ts_edited = (timestamp + timedelta(hours=tz_delta)).strftime("%d.%m.%Y %H:%M:%S")
                        msg_date, msg_time = ts_edited.split(" ")

                        message_parts.append(f"🔥 {server_name}")
                        message_parts.append("\n")
                        message_parts.append(f"⚡ {channel_name}")
                        message_parts.append("\n\n")
                        message_parts.append(f"⏰ {msg_date} {msg_time}")
                        message_parts.append("\n")
                        message_parts.append(f"✉️ Message from {author_username}")
                        message_parts.append("\n")
                        if 'referenced_message' in raw_message:
                            message_parts.append("\n")
                            referenced_author_name = await get_username_on_server(ds_token, server_id, raw_message['referenced_message']['author']['id'])
                            referenced_message_content = raw_message['referenced_message']['content']
                            message_parts.append(f"↪ Replying to {referenced_author_name}: {referenced_message_content}")
                            message_parts.append("\n")
                        if len(raw_message['attachments']) != 0:
                            message_parts.append("\n")
                            for _ in range(len(raw_message['attachments'])):
                                if raw_message['attachments'][_]['content_type'] in 'video/mp4 video/webm':
                                    attachment = raw_message['attachments'][_]['proxy_url']
                                else:
                                    attachment = raw_message['attachments'][_]['url']
                                message_parts.append(f"📎 {attachment}")
                                message_parts.append("\n\n")
                        if len(message_content) > 0:
                            message_parts.append("\n")
                            message_parts.append(f"📝 {message_content}")
                        
                        BotDB.update_message_id(tg_user_id, channel_id, received_message_id)
                        
                        if len(tracked_users) == 0: # messages from all users
                            final_message = ''.join(message_parts)
                            await bot.send_message(chat_id=tg_user_id, text=final_message, disable_web_page_preview=True)
                        elif author_id in tracked_users: # messages by selected user
                            message_parts[6] += " ✅" # adding symbol for tracked user
                            final_message = ''.join(message_parts)
                            await bot.send_message(chat_id=tg_user_id, text=final_message, disable_web_page_preview=True)
                    else: # user is ignored
                        pass
            else: # no new messages
                pass
        else:
            error_message = []
            error_message.append(f"⚠️ Warning! ⚠️")
            if not server_name:
                error_message.append("\n")
                error_message.append(f"No access to server {server_name}!")
            if not channel_name:
                error_message.append("\n")
                error_message.append(f"No access to channel {channel_name}!")
            await bot.send_message(chat_id=tg_user_id, text=''.join(error_message))


async def check_channels():
    users = BotDB.get_users()
    for user in users:
        tg_user_id, ds_token, tz_delta, is_paused = int(user[1]), user[2], int(user[3]), user[4]
        if not is_paused:
            await processing(tg_user_id, ds_token, tz_delta)
        

def repeat(coro, loop):
    asyncio.ensure_future(coro(), loop=loop)
    loop.call_later(delay, repeat, coro, loop)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.call_later(delay, repeat, check_channels, loop)
    executor.start_polling(dp, loop=loop)
