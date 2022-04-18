import sqlite3


class BotDB:
    
    def __init__(self, db_file) -> None:
        self.conn = sqlite3.connect(db_file,  check_same_thread=False)
        self.cursor = self.conn.cursor()


    def user_exists(self, tg_user_id):
        result = self.cursor.execute("SELECT `id` FROM `bot_users` WHERE `tg_user_id` = ?", (tg_user_id,))
        return bool(len(result.fetchall()))


    def is_paused(self, tg_user_id):
        result = self.cursor.execute("SELECT `is_paused` FROM `bot_users` WHERE `tg_user_id` = ?", (tg_user_id,))
        return result.fetchall()


    def add_user(self, tg_user_id, ds_token, tz_delta):
        self.cursor.execute("INSERT INTO `bot_users` (`tg_user_id`, `ds_token`, `tz_delta`) VALUES (?, ?, ?)", (tg_user_id, ds_token, tz_delta,))
        return self.conn.commit()


    def add_channel(self, tg_user_id, server_id, channel_id, tracked_users, ignored_users, last_message_id):
        self.cursor.execute("INSERT INTO `tracked_channels` (`tg_user_id`, `server_id`, `channel_id`, `tracked_users`, `ignored_users`, `last_message_id`) VALUES (?, ?, ?, ?, ?, ?)", (tg_user_id, server_id, channel_id, tracked_users, ignored_users, last_message_id))
        return self.conn.commit()


    def delete_channel(self, tg_user_id, id):
        self.cursor.execute("DELETE FROM `tracked_channels` WHERE `tg_user_id` = ? AND `id` = ? ", (tg_user_id, id,))
        return self.conn.commit()


    def delete_all_channels(self, tg_user_id):
        self.cursor.execute("DELETE FROM `tracked_channels` WHERE `tg_user_id` = ?", (tg_user_id,))
        return self.conn.commit()


    def get_tracked_channels(self, tg_user_id):
        result = self.cursor.execute("SELECT `id`, `server_id`, `channel_id`, `tracked_users`, `ignored_users`, `last_message_id` FROM `tracked_channels` WHERE `tg_user_id` = ?", (tg_user_id,))
        return result.fetchall()


    def get_channel_info(self, db_id, tg_user_id):
        result = self.cursor.execute("SELECT `server_id`, `channel_id`, `tracked_users`, `ignored_users`, `last_message_id` FROM `tracked_channels` WHERE `id` = ? AND `tg_user_id` = ?", (db_id, tg_user_id,))
        return result.fetchall()


    def get_discord_token(self, tg_user_id):
        result = self.cursor.execute("SELECT `ds_token` FROM `bot_users` WHERE `tg_user_id` = ?", (tg_user_id,))
        return result.fetchall()


    def get_tracked_users(self, db_id, tg_user_id):
        result = self.cursor.execute("SELECT `tracked_users` FROM `tracked_channels` WHERE `id` = ? AND `tg_user_id` = ?", (db_id, tg_user_id,))
        return result.fetchall()

    def get_ignored_users(self, db_id, tg_user_id):
        result = self.cursor.execute("SELECT `ignored_users` FROM `tracked_channels` WHERE `id` = ? AND `tg_user_id` = ?", (db_id, tg_user_id,))
        return result.fetchall()


    def get_users(self):
        result = self.cursor.execute("SELECT * FROM `bot_users`")
        return result.fetchall()


    def update_is_paused(self, tg_user_id, state):
        self.cursor.execute("UPDATE `bot_users` SET `is_paused` = ? WHERE `tg_user_id` = ?", (state, tg_user_id,))
        return self.conn.commit()


    def update_tracked_user(self, db_id, tg_user_id, cell_content):
        self.cursor.execute("UPDATE `tracked_channels` SET `tracked_users` = ? WHERE `id` = ? AND `tg_user_id` = ?", (cell_content, db_id, tg_user_id,))
        return self.conn.commit()


    def update_ignored_user(self, db_id, tg_user_id, cell_content):
        self.cursor.execute("UPDATE `tracked_channels` SET `ignored_users` = ? WHERE `id` = ? AND `tg_user_id` = ?", (cell_content, db_id, tg_user_id,))
        return self.conn.commit()


    def update_message_id(self, tg_user_id, channel_id, new_message_id):
        self.cursor.execute("UPDATE `tracked_channels` SET `last_message_id` = ? WHERE `tg_user_id` = ? AND `channel_id` = ?", (new_message_id, tg_user_id, channel_id,))
        return self.conn.commit()


    def update_ds_token(self, tg_user_id, ds_token):
        self.cursor.execute("UPDATE `bot_users` SET `ds_token` = ? WHERE `tg_user_id` = ?", (ds_token, tg_user_id,))
        return self.conn.commit()


    def update_tz_delta(self, tg_user_id, tz_delta):
        self.cursor.execute("UPDATE `bot_users` SET `tz_delta` = ? WHERE `tg_user_id` = ?", (tz_delta, tg_user_id,))
        return self.conn.commit()
    
    
    def close(self):
        self.conn.close()



def create_db(db_name:str) -> None:
    table1 = '''
    CREATE TABLE IF NOT EXISTS "bot_users" (
        "id"	INTEGER NOT NULL UNIQUE,
        "tg_user_id"	INTEGER NOT NULL UNIQUE,
        "ds_token"	TEXT NOT NULL,
        "tz_delta"	INTEGER NOT NULL,
        "is_paused"	INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY("id" AUTOINCREMENT)
    )
    '''

    table2 = '''
    CREATE TABLE IF NOT EXISTS "tracked_channels" (
        "id"	INTEGER NOT NULL UNIQUE,
        "tg_user_id"	INTEGER NOT NULL,
        "server_id"	INTEGER,
        "channel_id"	INTEGER,
        "tracked_users"	TEXT,
        "ignored_users"	TEXT,
        "last_message_id"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT)
    )
    '''
    conn = sqlite3.connect(db_name) 
    c = conn.cursor()

    c.execute(table1)
    c.execute(table2)
        
    conn.commit()
 
