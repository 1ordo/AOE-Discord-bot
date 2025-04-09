import mysql.connector
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from mysql.connector import pooling, Error
import base64
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()

class databases:
    def __init__(self):
        self.global_translation_cache = []
        self.global_linked_roles_cache = []
        self.global_linked_poll_cache = []  
        self.global_threads_translation_cache = []
        self.global_reaction_translation_cache = []
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="pooling_for_bot",
                pool_size=20,  # Adjust the pool size based on your needs
                host=os.getenv('DB_HOST', 'localhost'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                database=os.getenv('DB_NAME')
            )
        except Error as e:
            print(f"Error creating connection pool: {e}")
            logging.error(f"Error creating connection pool: {e}")
            raise
        self.key = self.load_key()
        self.cipher_suite = Fernet(self.key)
        self.create_tables()
        

    def get_connection(self):
        return self.pool.get_connection()    

        
    def load_key(self):
        try:
            key = os.getenv('ENCRYPTION_KEY').encode()
            if not key:
                raise ValueError("ENCRYPTION_KEY not found in environment variables")
            return key
        except Exception as e:
            print(f"Error loading encryption key: {e}")
            raise
    
    
    def encrypt(self, plaintext):
        return self.cipher_suite.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext):
        return self.cipher_suite.decrypt(ciphertext.encode()).decode()
    
    def create_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            #cursor.execute('''DROP TABLE IF EXISTS emojies_translate''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_channels (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guild_id BIGINT,
                channel_id BIGINT,
                channel_language TEXT,
                channel_link_id INT,
                channel_webhook TEXT
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS linked_roles (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guild_id BIGINT,
                role_id BIGINT,
                target_role BIGINT,
                role_link_id INT
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS linked_poll (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guild_id BIGINT,
                channel_id BIGINT,
                message_id BIGINT,
                poll_link_id BIGINT,
                poll_title TEXT,
                poll_description TEXT,
                poll_footer TEXT,
                poll_options TEXT,
                poll_creation_time datetime DEFAULT CURRENT_TIMESTAMP,
                poll_end_time datetime,
                is_original BOOLEAN
                
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS poll_votes (
                poll_id BIGINT,
                option_index INT,
                vote_count INT,
                PRIMARY KEY (poll_id, option_index)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS threads_translation (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guild_id BIGINT,
                parent_channel_id BIGINT,
                thread_id BIGINT,
                thread_link_id INT,
                language TEXT,
                webhook_link TEXT
            );
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS emojies_translate(
                guild_id BIGINT,
                emoji_id VARCHAR(255),
                language TEXT,
                PRIMARY KEY (guild_id, emoji_id)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS translation_roles (
                guild_id BIGINT,
                role_id BIGINT,
                language TEXT,
                PRIMARY KEY (guild_id , role_id)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS announcments_translation (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guild_id BIGINT,
                channel_id BIGINT,
                channel_link_id INT,
                language TEXT
            );     
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                Guild_id BIGINT PRIMARY KEY,
                member_ban BIGINT,
                member_timeout BIGINT,
                member_kick BIGINT,
                member_join_server BIGINT,
                member_left_server BIGINT,
                member_nickname BIGINT,
                member_unbanned BIGINT,
                member_joined_vc BIGINT,
                member_left_vc BIGINT,
                member_move_vc BIGINT,
                member_switch_vc BIGINT,
                member_disconnected_vc BIGINT,
                member_mute_deaf BIGINT,
                invites BIGINT,
                channel_created BIGINT,
                channel_deleted BIGINT,
                channel_updated BIGINT,
                thread_created BIGINT,
                thread_deleted BIGINT,
                role_created BIGINT,
                role_give BIGINT,
                role_delete BIGINT,
                role_update BIGINT,
                server_invite BIGINT,
                channel_perm_update BIGINT,
                message_delete BIGINT,
                message_edit BIGINT,
                member_role BIGINT
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_ignore (
                guild_id BIGINT,
                message_id BIGINT,
                PRIMARY KEY (guild_id, message_id)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS defaults (
                guild_id BIGINT,
                welcome_id BIGINT,
                welcome_message TEXT,
                ai_category_id BIGINT,
                Ai_channel_id BIGINT,
                PRIMARY KEY (guild_id)
            )
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_channel_history (
            channel_id BIGINT,
            history TEXT,
            PRIMARY KEY (channel_id)
            )
            ''')
            
            #cursor.execute('''DROP TABLE IF EXISTS auto_mod''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS automod_action_types (
                action_id SERIAL PRIMARY KEY,
                action_name VARCHAR(50) UNIQUE NOT NULL
            )''')

            # Insert default action types
            """
            
            cursor.execute('''
            
            INSERT IGNORE INTO automod_action_types (action_name) VALUES 
            ('WARN'), ('TIMEOUT'), ('KICK'), ('BAN'), ('QUARANTINE')
            ''')
            
            """
            
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS auto_mod (
                guild_id BIGINT PRIMARY KEY,
                channel_log_id BIGINT,
                
                -- this checks for the chosen setting in the first page for future updates
                chosen_setting BOOLEAN DEFAULT FALSE,
                
                -- Anti-spam settings 3
                is_anti_spam BOOLEAN DEFAULT FALSE,
                anti_spam_action_id INT REFERENCES automod_action_types(action_id),
                anti_spam_threshold INT, -- Duration in minutes, NULL for permanent
                
                -- Mention spam settings 6
                is_mention_spam BOOLEAN DEFAULT FALSE,
                mention_spam_action_id INT REFERENCES automod_action_types(action_id),
                mention_spam_duration INT,
                
                -- Suspicious link settings 9
                is_sus_link BOOLEAN DEFAULT FALSE,
                sus_link_action_id INT REFERENCES automod_action_types(action_id),
                sus_link_duration INT,
                
                -- Suspicious account settings 12
                is_sus_account BOOLEAN DEFAULT FALSE,
                sus_account_action_id INT REFERENCES automod_action_types(action_id),
                
                -- New account settings 14
                is_new_account BOOLEAN DEFAULT FALSE,
                new_account_action_id INT REFERENCES automod_action_types(action_id),
                
                -- Raid protection 16
                is_anti_raider BOOLEAN DEFAULT FALSE,
                anti_raider_action_id INT REFERENCES automod_action_types(action_id),
                raid_id INT, -- i will do them into groups later to make decisions
                
                -- Anti-nuke protection 19
                is_anti_nuke BOOLEAN DEFAULT FALSE,
                anti_nuke_action_id INT REFERENCES automod_action_types(action_id),
                anti_nuke_duration INT,
                
                -- anti-mass-ban and kick protection 22
                is_anti_mass BOOLEAN DEFAULT FALSE,
                anti_mass_action_id INT REFERENCES automod_action_types(action_id),
                anti_mass_duration INT,
                
                -- anti sus keywords this should detect nitro words, weird or sus one 25
                is_anti_sus_keywords BOOLEAN DEFAULT FALSE,
                anti_sus_keywords_action_id INT REFERENCES automod_action_types(action_id),
                anti_sus_keywords_duration INT
            )
            ''')
            
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    def execute_query(self, query, params=None, fetchone=False):

        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query, params or ())
            
            if query.strip().upper().startswith('SELECT'):
                if fetchone:
                    result = cursor.fetchone()
                else:
                    result = cursor.fetchall()
            else:
                result = None
                conn.commit()
            
            return result
        finally:
            cursor.close()
            conn.close()
    
    
    async def load_cache(self):
        self.global_translation_cache = self.get_all_translation_channels()
        print(f"Cache loaded with {len(self.global_translation_cache)} translation channels.")
        
        self.global_linked_roles_cache = self.get_all_linked_roles()
        print(f"Linked roles cache loaded with {len(self.global_linked_roles_cache)} entries.")
        
        
        self.global_poll_cache = self.get_all_linked_polls()
        print(f"Cache loaded with {len(self.global_poll_cache)} polls.")
        
        self.global_threads_translation_cache = self.get_all_threads_translation()
        print(f"Threads translation cache loaded with {len(self.global_threads_translation_cache)} entries.")

    def get_all_translation_channels(self):
        return self.execute_query('SELECT * FROM translation_channels')

    def search_cache_by_channel(self, guild_id, channel_id):
        return [
            row for row in self.global_translation_cache
            if row[1] == guild_id and row[2] == channel_id
        ]
    def search_link_id_cache_by_channel(self, guild_id, channel_id):
        return [
            row[4] for row in self.global_translation_cache
            if row[1] == guild_id and row[2] == channel_id
        ]
    def search_webhooks_by_link_id(self, guild_id, channel_link_id):
        return [
            row[5] for row in self.global_translation_cache
            if row[1] == guild_id and row[4] == channel_link_id
        ]
    def search_cache_by_link_id(self, guild_id, channel_link_id):
        return [
            row for row in self.global_translation_cache
            if row[1] == guild_id and row[4] == channel_link_id
        ]

    def search_cache_by_guild(self, guild_id):
        return [
            row for row in self.global_translation_cache
            if row[1] == guild_id
        ]
    
    
    def set_translation_channels(self, guild_id, channel_id, channel_language, channel_link_id, channel_webhook):
        self.execute_query('''
            INSERT INTO translation_channels (guild_id, channel_id, channel_language, channel_link_id, channel_webhook)
            VALUES (%s, %s, %s, %s, %s)
        ''', (guild_id, channel_id, channel_language, channel_link_id, channel_webhook))
        # Update the global cache
        new_entry = (None, guild_id, channel_id, channel_language, channel_link_id, channel_webhook)
        self.global_translation_cache.append(new_entry)

        

    def remove_translation_channels(self,guild_id, channel_id):
        self.execute_query('DELETE FROM translation_channels WHERE channel_id = %s AND guild_id = %s', (channel_id, guild_id))
        self.global_translation_cache = [
            row for row in self.global_translation_cache
            if not (row[1] == guild_id and row[2] == channel_id)
        ]

    def get_translation_channel_by_channel(self, guild_id, channel_id):
        """Get translation channel by guild_id and channel_id from cache or database."""
        # Check the cache first
        result = self.search_cache_by_channel(guild_id, channel_id)
        if result:
            return result[0]

        result = self.execute_query('''
            SELECT * FROM translation_channels WHERE guild_id = %s AND channel_id = %s
        ''', (guild_id, channel_id), fetchone=True)

        return result if result else None
    
    def get_corresponding_channel_by_link_id(self, mentioned_channel_id, link_id, target_language, guild_id):
        """Retrieve the corresponding channel based on link_id, target_language, and guild_id."""
        result = [
            row[2] for row in self.global_translation_cache
            if row[1] == guild_id and row[4] == link_id and row[3] == target_language and row[2] != mentioned_channel_id
        ]
        if result:
            return result[0]

        result = self.execute_query('''
            SELECT channel_id FROM translation_channels 
            WHERE guild_id = %s AND channel_link_id = %s AND channel_language = %s AND channel_id != %s
        ''', (guild_id, link_id, target_language, mentioned_channel_id), fetchone=True)
        return result[0] if result else None
    
    
    def get_translation_channel_by_link_id(self, guild_id, channel_link_id):
        result = self.search_cache_by_link_id(guild_id, channel_link_id)
        if result:
            return result

        result = self.execute_query('''
            SELECT * FROM translation_channels WHERE guild_id = %s AND channel_link_id = %s
        ''', (guild_id, channel_link_id))

        return result if result else None
    

    def get_translation_channel_by_guild(self, guild_id):
        result = self.search_cache_by_guild(guild_id)
        if result:
            return result

        result = self.execute_query('''
            SELECT * FROM translation_channels WHERE guild_id = %s
        ''', (guild_id,))

        return result if result else None

    """role linking methods"""
    
    def get_all_linked_roles(self):
        """Fetch all linked roles from the database."""
        return self.execute_query('SELECT * FROM linked_roles')

    def search_linked_roles_cache_by_role(self, guild_id, role_id):
        """Search the global linked roles cache by guild_id and role_id."""
        return [
            row for row in self.global_linked_roles_cache
            if row[1] == guild_id and row[2] == role_id
        ]

    def search_linked_roles_cache_by_link_id(self, guild_id, role_link_id):
        """Search the global linked roles cache by guild_id and role_link_id."""
        return [
            row for row in self.global_linked_roles_cache
            if row[1] == guild_id and row[4] == role_link_id
        ]

    def search_linked_roles_cache_by_guild(self, guild_id):
        """Search the global linked roles cache by guild_id."""
        return [
            row for row in self.global_linked_roles_cache
            if row[1] == guild_id
        ]

    def set_linked_role(self, guild_id, role_id, target_role, role_link_id):
        """Insert linked role into the database and update cache."""
        self.execute_query('''
            INSERT INTO linked_roles (guild_id, role_id, target_role, role_link_id)
            VALUES (%s, %s, %s, %s)
        ''', (guild_id, role_id, target_role, role_link_id))

        # Update the global cache
        new_entry = (None, guild_id, role_id, target_role, role_link_id)
        self.global_linked_roles_cache.append(new_entry)

    def remove_linked_role(self, guild_id, role_id,link_id):
        """Remove linked role from the database and update cache."""
        self.execute_query('DELETE FROM linked_roles WHERE role_id = %s AND guild_id = %s AND role_link_id = %s', (role_id, guild_id,link_id))

        # Update the global cache
        self.global_linked_roles_cache = [
            row for row in self.global_linked_roles_cache
            if not (row[1] == guild_id and row[2] == role_id and row[4] == link_id)
        ]

    def get_linked_role_by_role(self, guild_id, role_id):
        """Get linked role by guild_id and role_id from cache or database."""
        # Check the cache first
        result = self.search_linked_roles_cache_by_role(guild_id, role_id)
        if result:
            return result[0]  # Return the first matching record from the cache

        # If not in cache, fallback to the database
        result = self.execute_query('''
            SELECT * FROM linked_roles WHERE guild_id = %s AND role_id = %s
        ''', (guild_id, role_id), fetchone=True)

        return result

    def get_linked_role_by_link_id(self, guild_id, role_link_id):
        """Get linked roles by guild_id and role_link_id from cache or database."""
        # Check the cache first
        result = self.search_linked_roles_cache_by_link_id(guild_id, role_link_id)
        if result:
            return result

        # If not in cache, fallback to the database
        result = self.execute_query('''
            SELECT * FROM linked_roles WHERE guild_id = %s AND role_link_id = %s
        ''', (guild_id, role_link_id))

        return result if result else None

    def get_linked_roles_by_guild(self, guild_id):
        """Get all linked roles by guild_id from cache or database."""
        # Check the cache first
        result = self.search_linked_roles_cache_by_guild(guild_id)
        if result:
            return result

        # If not in cache, fallback to the database
        result = self.execute_query('''
            SELECT * FROM linked_roles WHERE guild_id = %s
        ''', (guild_id,))

        return result if result else None
    
    
    def get_all_linked_polls(self):
        return self.execute_query('SELECT * FROM linked_poll')

    def search_poll_cache_by_guild_and_original(self, guild_id,is_original):
        result = [row for row in self.global_linked_poll_cache if row[1] == guild_id and row[11] == is_original]
        return result if result else None

    def search_poll_cache_by_poll_link_id(self, guild_id, poll_link_id):
        result = [row for row in self.global_linked_poll_cache if row[1] == guild_id and row[4] == poll_link_id]
        return result if result else None

    def search_poll_cache_by_poll_link_id_and_channel(self, guild_id, poll_link_id, channel_id):
        result = [row for row in self.global_linked_poll_cache if row[1] == guild_id and row[4] == poll_link_id and row[2] == channel_id]
        return result if result else None

    def search_poll_cache_by_poll_link_id_and_channel_and_original(self, guild_id, poll_link_id, channel_id,is_original:bool):
        result = [row for row in self.global_linked_poll_cache if row[1] == guild_id and row[4] == poll_link_id and row[2] == channel_id and row[11] == is_original]
        return result if result else None
    
    
    def set_linked_poll(self, guild_id, channel_id, message_id, poll_link_id, poll_title, poll_description, poll_footer, poll_options, poll_end_time,is_original = False):
        
        self.execute_query('''
            INSERT INTO linked_poll (guild_id, channel_id, message_id, poll_link_id, poll_title, poll_description, poll_footer, poll_options, poll_end_time,is_original)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
        ''', (guild_id, channel_id, message_id, poll_link_id, poll_title, poll_description, poll_footer, poll_options, poll_end_time,is_original))
        
        new_entry = (None, guild_id, channel_id, message_id, poll_link_id, poll_title, poll_description, poll_footer, poll_options, datetime.now(), poll_end_time,is_original)
        self.global_linked_poll_cache.append(new_entry)

    def remove_linked_poll(self, guild_id, poll_link_id):
        self.execute_query('DELETE FROM linked_poll WHERE guild_id = %s AND poll_link_id = %s', (guild_id, poll_link_id))
        self.global_linked_poll_cache = [
            row for row in self.global_linked_poll_cache
            if not (row[1] == guild_id and row[4] == poll_link_id)
        ]

    def get_linked_poll_by_guild_and_original(self, guild_id,is_original):
        result = self.search_poll_cache_by_guild_and_original(guild_id,is_original)
        if result:
            return result
        result = self.execute_query('SELECT * FROM linked_poll WHERE guild_id = %s AND is_original = %s', (guild_id,is_original))
        
        return result if result else None

    def get_linked_poll_by_poll_link_id(self, guild_id, poll_link_id):
        result = self.search_poll_cache_by_poll_link_id(guild_id, poll_link_id)
        if result:
            
            return result
        result = self.execute_query('SELECT * FROM linked_poll WHERE guild_id = %s AND poll_link_id = %s', (guild_id, poll_link_id))
        
        return result if result else None
    
    def get_linked_poll_by_poll_link_id_and_channel(self, guild_id, poll_link_id,channel_id):
        result = self.search_poll_cache_by_poll_link_id_and_channel(guild_id, poll_link_id,channel_id)
        if result:
            print("found data in the cache!")
            return result
        result = self.execute_query('SELECT * FROM linked_poll WHERE guild_id = %s AND poll_link_id = %s AND channel_id = %s', (guild_id, poll_link_id,channel_id))
        return result
    
    def get_linked_poll_by_poll_link_id_and_channel_and_original(self, guild_id, poll_link_id,channel_id,is_original:bool):
        result = self.search_poll_cache_by_poll_link_id_and_channel_and_original(guild_id, poll_link_id,channel_id,is_original)
        if result:
            print("found data in the cache!")
            return result
        result = self.execute_query('SELECT * FROM linked_poll WHERE guild_id = %s AND poll_link_id = %s AND channel_id = %s AND is_original = %s', (guild_id, poll_link_id,channel_id,is_original))
        return result
    
    def increment_vote(self, poll_id, option_index):
        self.execute_query('''
            INSERT INTO poll_votes (poll_id, option_index, vote_count)
            VALUES (%s, %s, 1)
            ON DUPLICATE KEY UPDATE vote_count = vote_count + 1
        ''', (poll_id, option_index))


    def decrement_vote(self, poll_id, option_index):
        self.execute_query('''
            UPDATE poll_votes
            SET vote_count = GREATEST(vote_count - 1, 0)
            WHERE poll_id = %s AND option_index = %s
        ''', (poll_id, option_index))

    def get_votes_for_poll(self, poll_id):
        return self.execute_query('''
            SELECT option_index, vote_count
            FROM poll_votes
            WHERE poll_id = %s
        ''', (poll_id,))

    def get_poll_by_message_id(self, guild_id, channel_id, message_id):
        """Get poll by guild_id, channel_id, and message_id from cache or database."""
        
        # Search the cache first
        result = [row for row in self.global_linked_poll_cache if row[1] == guild_id and row[2] == channel_id and row[3] == message_id]
        
        if result:
            return result[0]  # Return the first matching record from the cache
        
        # If not found in cache, search in the database
        result = self.execute_query('''
            SELECT * FROM linked_poll WHERE guild_id = %s AND channel_id = %s AND message_id = %s
        ''', (guild_id, channel_id, message_id), fetchone=True)
        
        return result if result else None

    def get_all_threads_translation(self):
        return self.execute_query('SELECT * FROM threads_translation')

    def set_threads_translation(self, guild_id, parent_channel_id, thread_id, thread_link_id, language, webhook_link):
        self.execute_query('''
            INSERT INTO threads_translation (guild_id, parent_channel_id, thread_id, thread_link_id, language, webhook_link)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (guild_id, parent_channel_id, thread_id, thread_link_id, language, webhook_link))
        new_entry = (None, guild_id, parent_channel_id, thread_id, thread_link_id, language, webhook_link)
        self.global_threads_translation_cache.append(new_entry)

    def remove_threads_translation(self, guild_id, thread_id):
        self.execute_query('DELETE FROM threads_translation WHERE guild_id = %s AND thread_id = %s', (guild_id, thread_id))
        self.global_threads_translation_cache = [
            row for row in self.global_threads_translation_cache
            if not (row[1] == guild_id and row[3] == thread_id)
        ]


    def get_translation_thread_by_guild(self, guild_id):
        result = [row for row in self.global_threads_translation_cache if row[1] == guild_id]
        if result:
            return result
        return self.execute_query('SELECT * FROM threads_translation WHERE guild_id = %s', (guild_id,))

    def get_translation_thread_by_channel_and_link_id(self, guild_id,channel_id,thread_link_id):
        result = [row for row in self.global_threads_translation_cache if row[1] == guild_id and row[2] == channel_id and row[4] == thread_link_id]
        if result:
            return result
        return self.execute_query('SELECT * FROM threads_translation WHERE guild_id = %s AND parent_channel_id = %s AND thread_link_id == %s', (guild_id, channel_id, thread_link_id))
    
    def get_translation_thread_by_link_id(self, guild_id,thread_link_id):
        result = [row for row in self.global_threads_translation_cache if row[1] == guild_id  and row[4] == thread_link_id]
        if result:
            return result
        return self.execute_query('SELECT * FROM threads_translation WHERE guild_id = %s AND thread_link_id = %s', (guild_id, thread_link_id))
    
    
    def get_translation_thread_by_channel(self, guild_id,channel_id):
        result = [row for row in self.global_threads_translation_cache if row[1] == guild_id and row[2] == channel_id]
        if result:
            return result[0]
        return self.execute_query('SELECT * FROM threads_translation WHERE guild_id = %s AND parent_channel_id = %s', (guild_id, channel_id))[0]
    
    def get_translation_thread_by_thread_id(self, guild_id,thread_id):
        result = [row for row in self.global_threads_translation_cache if row[1] == guild_id and row[3] == thread_id]
        if result:
            return result[0]
        return self.execute_query('SELECT * FROM threads_translation WHERE guild_id = %s AND thread_id = %s', (guild_id, thread_id),fetchone=True)
    
    def get_next_available_link_id(self,guild_id):
        result = self.execute_query('SELECT MAX(thread_link_id) FROM threads_translation WHERE guild_id = %s',(guild_id,), fetchone=True)
        return result[0] + 1 if result and result[0] is not None else 1

    def get_translation_thread_by_channel_and_thread_id(self, guild_id, channel_id, thread_id):
        result = [row for row in self.global_threads_translation_cache 
                if row[1] == guild_id and row[2] == channel_id and row[3] == thread_id]
        
        if result:
            return result
        return self.execute_query(
            'SELECT * FROM threads_translation WHERE guild_id = %s AND parent_channel_id = %s AND thread_id = %s', 
            (guild_id, channel_id, thread_id)
        )

    def get_corresponding_thread_by_link_id(self,thread_link_id: int, target_language: str, guild_id: int):
        #result = [
        #   row[2] for row in self.global_threads_translation_cache
        #    if row[1] == guild_id and row[4] == thread_link_id and row[5] == target_language and row[2] != mentioned_channel_id
        #]
        #if result:
        #    return result[0]
        
        
        result = self.execute_query('''
            SELECT thread_id, parent_channel_id FROM threads_translation 
            WHERE guild_id = %s AND thread_link_id = %s AND language = %s
        ''', (guild_id, thread_link_id, target_language), fetchone=True)
        return result if result else None
    
    
    def clone_translation_to_threads(self, guild_id, parent_channel_id, new_thread_id):

        # Get parent channel settings
        parent_translation = self.get_translation_thread_by_channel_and_thread_id(guild_id, parent_channel_id, 0)
        
        if not parent_translation:
            print(f"No translation settings found for parent channel {parent_channel_id} in guild {guild_id}")
            return None  # No translation settings for the parent channel
        
        parent_thread_link_id = parent_translation[0][4]  # Assuming the link ID is at index 4 in the tuple
        language = parent_translation[0][5]  # Language at index 5
        webhook_link = parent_translation[0][6]  # Webhook link at index 6

        # Get the next available link ID for the new thread
        new_thread_link_id = self.get_next_available_link_id(guild_id)

        # Set the translation for the new thread
        self.set_threads_translation(
            guild_id=guild_id,
            parent_channel_id=parent_channel_id,
            thread_id=new_thread_id,
            thread_link_id=new_thread_link_id,
            language=language,
            webhook_link=webhook_link
        )

        # Add the new thread's translation settings to the cache
        new_thread_entry = (None, guild_id, parent_channel_id, new_thread_id, new_thread_link_id, language, webhook_link)
        self.global_threads_translation_cache.append(new_thread_entry)

        print(f"Thread {new_thread_id} in guild {guild_id} has been linked with ID {new_thread_link_id}.")

        return new_thread_entry
    
    def ping_database(self):
        try:
            start_time = time.time()
            result = self.execute_query('''
            SELECT 1
            ''',fetchone=True)
            end_time = time.time()

            

            ping_time = (end_time - start_time) * 1000 
            return f"{ping_time:.2f} ms"
        except Exception as e:
            return f"Error: {e}"
    
    
    def log_update(self, guild_id, column_name, channel_id):
        # List of valid column names for security reasons
        valid_columns = [
            "member_ban", "member_timeout", "member_kick", "member_join_server",
            "member_left_server", "member_nickname", "member_unbanned", "member_joined_vc",
            "member_left_vc", "member_move_vc", "member_switch_vc", "member_disconnected_vc",
            "member_mute_deaf", "invites", "channel_created", "channel_deleted",
            "channel_updated", "thread_created", "thread_deleted", "role_created", "role_give",
            "role_delete", "role_update", "server_invite", "channel_perm_update","message_delete"
            ,"message_edit","member_role"
        ]
        #TODO remove vc_activity culumn completely, serpreate server loogs (member join/leaves)
        # Check if the provided column name is valid
        if column_name not in valid_columns:
            print(f"Invalid column name: {column_name}")
            return
        
        try:
            # Construct the SQL query
            query = f'''
                INSERT INTO logs (Guild_id, {column_name}) VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE {column_name} = %s
            '''
            self.execute_query(query, (guild_id, channel_id, channel_id))

        except Exception as e:
            print
        
    def log_retrieve(self, guild_id, column_name):

        valid_columns = [
            "member_ban", "member_timeout", "member_kick", "member_join_server",
            "member_left_server", "member_nickname", "member_unbanned", "member_joined_vc",
            "member_left_vc", "member_move_vc", "member_switch_vc", "member_disconnected_vc",
            "member_mute_deaf", "invites", "channel_created", "channel_deleted",
            "channel_updated", "thread_created", "thread_deleted", "role_created", "role_give",
            "role_delete", "role_update", "server_invite", "channel_perm_update","message_delete"
            ,"message_edit","member_role"
        ]
        
        if column_name not in valid_columns:
            print(f"Invalid column name: {column_name}")
            return None
        
        try:
            # Construct the SQL query
            query = f'SELECT {column_name} FROM logs WHERE Guild_id = %s'
            result = self.execute_query(query, (guild_id,),fetchone=True)

            
            # Return the result if found
            if result:
                return result[0]
            else:
                return None
        
        except Exception as e:
            return e

    

    def save_ai_channel_history(self, channel_id: int, history: list):
        history_json = json.dumps(history)
        self.execute_query('INSERT INTO ai_channel_history (channel_id, history) VALUES (%s, %s) ON DUPLICATE KEY UPDATE history = %s', (channel_id, history_json, history_json))   
        
    def delete_ai_channel_history(self,channel_id):
        self.execute_query('DELETE FROM ai_channel_history WHERE channel_id = %s', (channel_id,))

    
    def retrieve_ai_channel_history(self, channel_id):
        return self.execute_query('SELECT history FROM ai_channel_history WHERE channel_id = %s', (channel_id,),fetchone=True)
        
        
        
        
        
        
        
    def check_defaults(self, guild_id: int):

        result = self.execute_query('SELECT guild_id, welcome_id, welcome_message, ai_category_id, Ai_channel_id FROM defaults WHERE guild_id = %s', (guild_id,),fetchone=True)

        if result:
            return result 
        else:
            return None  
        
        #defaults = check_defaults(guild_id)  ----->if defaults:
        # Unpack the returned tuple into individual variables
        # guild_id, welcome_id, welcome_message, ai_category_id, Ai_channel_id, Travia_channel = defaults   and now u can use them
        
    def update_defaults(self, guild_id: int, welcome_id: str = None, welcome_message: str = None, ai_category_id: int = None, Ai_channel_id: int = None):
    # Check if a record with the provided guild_id exists

        existing_record = self.execute_query('SELECT * FROM defaults WHERE guild_id = %s', (guild_id,),fetchone=True)

        # If no record exists, insert a new record
        if not existing_record:
            # Construct the SQL query for insertion
            insert_query = 'INSERT INTO defaults (guild_id'

            # Construct the values placeholder for the query
            values_placeholder = '(%s'

            # Initialize the parameters list with guild_id
            insert_params = [guild_id]

            # Add other parameters to the SQL query and parameters list if provided
            if welcome_id is not None:
                insert_query += ', welcome_id'
                values_placeholder += ', %s'
                insert_params.append(welcome_id)
            if welcome_message is not None:
                insert_query += ', welcome_message'
                values_placeholder += ', %s'
                insert_params.append(welcome_message)
            if ai_category_id is not None:
                insert_query += ', ai_category_id'
                values_placeholder += ', %s'
                insert_params.append(ai_category_id)
            if Ai_channel_id is not None:
                insert_query += ', Ai_channel_id'
                values_placeholder += ', %s'
                insert_params.append(Ai_channel_id)

            # Complete the insert query and parameters list
            insert_query += ') VALUES ' + values_placeholder + ')'
            
            # Execute the SQL insertion query
            self.execute_query(insert_query, insert_params)
        else:
            # Construct the SQL update query
            sql_query = 'UPDATE defaults SET '
            update_params = []

            # Add each parameter to the SQL query if it's provided
            if welcome_id is not None:
                sql_query += 'welcome_id = %s, '
                update_params.append(welcome_id)
            if welcome_message is not None:
                sql_query += 'welcome_message = %s, '
                update_params.append(welcome_message)
            if ai_category_id is not None:
                sql_query += 'ai_category_id = %s, '
                update_params.append(ai_category_id)
            if Ai_channel_id is not None:
                sql_query += 'Ai_channel_id = %s, '
                update_params.append(Ai_channel_id)
                
            sql_query = sql_query.rstrip(', ') + ' WHERE guild_id = %s'
            update_params.append(guild_id)

            # Execute the SQL update query
            self.execute_query(sql_query, update_params)
    
    def set_translation_roles(self,guild_id,role_id,language):
        self.execute_query('''INSERT INTO translation_roles (guild_id, role_id, language)
                        VALUES (%s, %s,%s)
                        ON DUPLICATE KEY UPDATE language = %s''', (guild_id, role_id, language,language))   
    
    def get_translation_roles(self, guild_id):
        result = self.execute_query('SELECT * FROM translation_roles WHERE guild_id = %s',(guild_id,))
        return result if result else None
    
    def check_translation_language_with_role(self,guild_id, role_id):
        result = self.execute_query('SELECT language FROM translation_roles WHERE guild_id = %s AND role_id = %s',(guild_id,role_id),fetchone=True)
        return result[0] if result else None
    
    def delete_translation_role(self,guild_id, role_id):
        self.execute_query('DELETE FROM translation_roles WHERE guild_id = %s AND role_id = %s',(guild_id,role_id))
    
    def set_translation_emoji(self,guild_id,emoji_id,language):
        self.execute_query('''INSERT INTO emojies_translate (guild_id, emoji_id, language)
                        VALUES (%s, %s,%s)
                        ON DUPLICATE KEY UPDATE language = %s''',(guild_id,emoji_id,language,language))
    
    def get_translation_roles(self, guild_id):
        result = self.execute_query('SELECT * FROM emojies_translate WHERE guild_id = %s',(guild_id,))
        return result if result else None
    
    def check_translation_emoji(self,guild_id,emoji_id):
        result = self.execute_query('SELECT language FROM emojies_translate WHERE guild_id = %s AND emoji_id = %s',(guild_id,emoji_id),fetchone=True)
        return result[0] if result else None
    
    
    def delete_translation_emojies(self,guild_id, emoji_id):
        self.execute_query('DELETE FROM emojies_translate WHERE guild_id = %s AND emoji_id = %s',(guild_id,emoji_id))

    def insert_automod_settings(self, guild_id: int, **kwargs):
        """
        Insert or update automod settings for a guild.
        Only updates specified fields in kwargs.
        """
        
        # List of valid column names that can be updated
        valid_columns = [
            'channel_log_id',
            'chosen_setting',
            'is_anti_spam',
            'anti_spam_action_id',
            'anti_spam_threshold',
            'is_mention_spam',
            'mention_spam_action_id', 
            'mention_spam_duration',
            'is_sus_link',
            'sus_link_action_id',
            'sus_link_duration',
            'is_sus_account',
            'sus_account_action_id',
            'is_new_account',
            'new_account_action_id',
            'is_anti_raider',
            'anti_raider_action_id',
            'raid_id',
            'is_anti_nuke',
            'anti_nuke_action_id',
            'anti_nuke_duration',
            'is_anti_mass',
            'anti_mass_action_id',
            'anti_mass_duration',
            'is_anti_sus_keywords',
            'anti_sus_keywords_action_id',
            'anti_sus_keywords_duration'
        ]

        # First try to insert with all defaults
        try:
            self.execute_query(
                'INSERT IGNORE INTO auto_mod (guild_id) VALUES (%s)',
                (guild_id,)
            )
        except Exception as e:
            print(f"Error inserting default automod settings: {e}")
            return False

        # If kwargs provided, update only those fields
        if kwargs:
            # Build update query for valid columns only
            update_cols = []
            update_vals = []
            
            for col, val in kwargs.items():
                if col in valid_columns:
                    update_cols.append(f"{col} = %s")
                    update_vals.append(val)
                    
            if update_cols:
                # Add guild_id to values
                update_vals.append(guild_id)
                
                # Construct and execute update query
                update_query = f"""
                    UPDATE auto_mod 
                    SET {', '.join(update_cols)}
                    WHERE guild_id = %s
                """
                
                try:
                    self.execute_query(update_query, update_vals)
                    return True
                except Exception as e:
                    print(f"Error updating automod settings: {e}")
                    return False
                    
        return True
    def insert_all_true_settings(self, guild_id: int):
        """
        Insert all automod settings as true for a guild with default action_id = 1 
        and default durations = 60 minutes
        """
        settings = {
            'chosen_setting': True,
            'is_anti_spam': True,
            'anti_spam_action_id': 1,
            'anti_spam_threshold': 60,
            'is_mention_spam': True, 
            'mention_spam_action_id': 1,
            'mention_spam_duration': 60,
            'is_sus_link': True,
            'sus_link_action_id': 1,
            'sus_link_duration': 60,
            'is_sus_account': True,
            'sus_account_action_id': 1,
            'is_new_account': True, 
            'new_account_action_id': 1,
            'is_anti_raider': True,
            'anti_raider_action_id': 1,
            'raid_id': 1,
            'is_anti_nuke': True,
            'anti_nuke_action_id': 1,
            'anti_nuke_duration': 60,
            'is_anti_mass': True,
            'anti_mass_action_id': 1,
            'anti_mass_duration': 60,
            'is_anti_sus_keywords': True,
            'anti_sus_keywords_action_id': 1,
            'anti_sus_keywords_duration': 60
        }
        
        return self.insert_automod_settings(guild_id, **settings)
    
    def delete_automod_settings(self, guild_id: int):
        """
        Delete all automod settings for a guild.
        """
        try:
            self.execute_query('DELETE FROM auto_mod WHERE guild_id = %s', (guild_id,))
            return True
        except Exception as e:
            print(f"Error deleting automod settings: {e}")
            return False

    def update_automod_log_channel(self, guild_id: int, channel_id: int):
        """
        Update only the log channel for automod settings.
        """
        try:
            self.execute_query(
                'UPDATE auto_mod SET channel_log_id = %s WHERE guild_id = %s',
                (channel_id, guild_id)
            )
            return True
        except Exception as e:
            print(f"Error updating automod log channel: {e}")
            return False
    
    def get_all_automod_settings(self, guild_id):
        result = self.execute_query('SELECT * FROM auto_mod WHERE guild_id = %s',(guild_id,),fetchone=True)
        return result if result else None
    
    def get_automod_settings(self, guild_id: int, setting_name: str = None):
        """
        Retrieve automod settings for a guild.
        If setting_name is provided, returns just that setting.
        If setting_name is None, returns all settings.
        """
        valid_columns = [
            'channel_log_id',
            'chosen_setting',
            'is_anti_spam',
            'anti_spam_action_id',
            'anti_spam_threshold',
            'is_mention_spam',
            'mention_spam_action_id',
            'mention_spam_duration', 
            'is_sus_link',
            'sus_link_action_id',
            'sus_link_duration',
            'is_sus_account', 
            'sus_account_action_id',
            'is_new_account',
            'new_account_action_id',
            'is_anti_raider',
            'anti_raider_action_id',
            'raid_id',
            'is_anti_nuke',
            'anti_nuke_action_id',
            'anti_nuke_duration',
            'is_anti_mass',
            'anti_mass_action_id',
            'anti_mass_duration',
            'is_anti_sus_keywords',
            'anti_sus_keywords_action_id',
            'anti_sus_keywords_duration'
        ]

        try:
            if setting_name:
                if setting_name not in valid_columns:
                    return None
                query = f'SELECT {setting_name} FROM auto_mod WHERE guild_id = %s'
                result = self.execute_query(query, (guild_id,), fetchone=True)
                return result[0] if result else None
            else:
                query = 'SELECT * FROM auto_mod WHERE guild_id = %s'
                result = self.execute_query(query, (guild_id,), fetchone=True)
                return result
        except Exception as e:
            print(f"Error retrieving automod settings: {e}")
            return None
    
    def add_message_ignore(self, guild_id: int, message_id: int):
        """
        Add a message ID to the ignore list for message_ignore
        """
        try:
            self.execute_query(
                'INSERT INTO message_ignore (guild_id, message_id) VALUES (%s, %s)',
                (guild_id, message_id)
            )
            return True
        except Exception as e:
            print(f"Error adding message ID to ignore list: {e}")
            return False
    
    def remove_message_ignore(self, guild_id: int, message_id: int):
        """
        Remove a message ID from the ignore list for message_ignore
        """
        try:
            self.execute_query(
                'DELETE FROM message_ignore WHERE guild_id = %s AND message_id = %s',
                (guild_id, message_id)
            )
            return True
        except Exception as e:
            print(f"Error removing message ID from ignore list: {e}")
            return False
    
    def check_message_ignore(self, guild_id: int, message_id: int):
        """
        Check if a message ID is in the ignore list for message_ignore
        """
        try:
            result = self.execute_query(
                'SELECT * FROM message_ignore WHERE guild_id = %s AND message_id = %s',
                (guild_id, message_id),
                fetchone=True
            )
            return result is not None # returns true if message_id is in the ignore list
        
        except Exception as e:
            print(f"Error checking message ID in ignore list: {e}")
            return False
    def get_all_message_ignore(self, guild_id: int):
        """
        Get all message IDs in the ignore list for message_ignore
        """
        try:
            result = self.execute_query(
                'SELECT message_id FROM message_ignore WHERE guild_id = %s',
                (guild_id,)
            )
            return [row[0] for row in result] if result else []
        
        except Exception as e:
            print(f"Error getting all message IDs in ignore list: {e}")
            return []
database = databases()
