import logging
from logging.handlers import RotatingFileHandler

import os
import datetime

import mysql.connector
from dotenv import load_dotenv, dotenv_values

from entities.Account import Account
from entities.User import User
from entities.Group import Group
from entities.AddMemberHistory import AddMemberHistory
from entities.CrawlGroupHistory import CrawlGroupHistory
from entities.SendMessageHistory import SendMessageHistory
from entities.MemberInGroup import MemberInGroup

# Load environmental variable
config = dotenv_values("../.env")

# --------------------------------------------------- LOGGING ---------------------------------------------------------
# Create new log folder if not exist
# LOG_FOLDER_NAME = config.get('LOG_FOLDER_NAME')
# LOG_FOLDER      = os.path.join(os.getcwd(), LOG_FOLDER_NAME)
# LOG_FILE        = os.path.join(LOG_FOLDER, 'log_{datetime}.log'.format(datetime=datetime.datetime.now().strftime('%Y-%m-%d')))
# MAXBYTES        = (config.get('MAXBYTES'))
# BACKUP_COUNT    = config.get('BACKUP_COUNT')
#
# # Set up logging basic config
# try:
#     handler_rfh = RotatingFileHandler(LOG_FILE, maxBytes=int(MAXBYTES), backupCount=int(BACKUP_COUNT))
#     handler_rfh.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', \
#                         datefmt='%m/%d/%Y %I:%M:%S %p')
#     logging.getLogger('CRAWL_TELEGRAM').addHandler(handler_rfh)
#
# except Exception as e:
#     logging.exception(e)
# ----------------------------------------------------------------------------------------------------------------------


class DBWorker:
    def __init__(self):
        '''
        This class is used to provide methods help you to work with Database
        '''
        self.DB_USER = config.get('DB_USER')
        self.DB_PASSWORD = config.get('DB_PASSWORD')
        self.DB_HOST = config.get('DB_HOST')
        self.DB_PORT = config.get('DB_PORT')
        self.DB_NAME = config.get('DB_NAME')
    

    def get_mysql_engine_connection(self):
        my_engine = mysql.connector.connect(
            port=self.DB_PORT,
            host=self.DB_HOST,
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            auth_plugin='mysql_native_password'
        )
        return my_engine
        

    def get_db_connection(self):
        my_db = mysql.connector.connect(
            port=self.DB_PORT,
            host=self.DB_HOST,
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            database=self.DB_NAME,
            auth_plugin='mysql_native_password'
        )
        my_db.autocommit = True
        return my_db

    # ========================================== SELECT =======================================================
    def select_all_accounts(self):
        '''
        This function is used to select all accounts that is available to proceed
        '''
        authenticated_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = """SELECT phone_no, api_id, api_hash, authenticated_datetime FROM tbl_account"""

        my_db = self.get_db_connection()
        mycursor = my_db.cursor()
        mycursor.execute(query)
        results = mycursor.fetchall()

        list_accounts = []
        for x in results:
            acc = Account(phone_no = x[0], api_id = x[1], api_hash = x[2], authenticated_datetime=x[3])
            list_accounts.append(acc)

        return list_accounts

    def select_account(self, phone):
        '''
        select a specific account
        '''
        query = f"""SELECT phone_no, api_id, api_hash, authenticated_datetime FROM tbl_account WHERE phone_no = {phone}"""

        my_db = self.get_db_connection()
        mycursor = my_db.cursor()
        mycursor.execute(query)
        results = mycursor.fetchall()
        result = results[0]
        acc = Account(phone_no=result[0], api_id=result[1], api_hash=result[2],
                      authenticated_datetime=result[3])
        return acc
    def select_available_add_accounts(self):
        '''
        This function is used to select all accounts that is not used to add member in 1-day interval.
        '''
        my_db = self.get_db_connection()
        mycursor = my_db.cursor()
        mycursor.callproc('sp_get_available_add_account')
        results = mycursor.stored_results()
        
        list_accounts = []
        for result in results:
            for x in result:
                acc = Account(phone_no = x[0], api_id = x[1], api_hash = x[2], authenticated_datetime = x[3])
                list_accounts.append(acc)

        return list_accounts

    
    def select_available_send_accounts(self):
        '''
        This function is used to select all accounts that is not used to send member in 1-day interval.
        '''
        my_db = self.get_db_connection()
        mycursor = my_db.cursor()
        mycursor.callproc('sp_get_available_send_account')
        results = mycursor.stored_results()
        
        list_accounts = []
        for result in results:
            for x in result:
                acc = Account(phone_no = x[0], api_id = x[1], api_hash = x[2], authenticated_datetime = x[3])
                list_accounts.append(acc)

        return list_accounts

    
    def select_top_account(self):
        '''
        This function is used to select the last account
        '''
        authenticated_datetime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        query = 'SELECT * FROM ' \
                'tbl_account ORDER BY authenticated_datetime DESC LIMIT 1'

        my_db = self.get_db_connection()
        mycursor = my_db.cursor()
        mycursor.execute(query)
        results = mycursor.fetchall()
        result = results[0]
        acc = Account(phone_no=result[0], api_id=result[1], api_hash=result[2],
                      authenticated_datetime=result[3])

        return acc

    def select_all_groups(self):
        '''
        This function is used to select all groups 
        '''
        query = 'SELECT group_id, group_name, group_type FROM tbl_group'
        
        my_db = self.get_db_connection()
        mycursor = my_db.cursor()
        mycursor.execute(query)
        results = mycursor.fetchall()
        
        list_groups = []
        for x in results:
            gr = Group(group_id = x[0], group_name = x[1], group_type = x[2])
            list_groups.append(gr)

        return list_groups


    def select_all_members_in_one_group(self, group_id, group_name=None):
        '''
        This function is used to select all members from one group
        '''
        my_db       = self.get_db_connection()
        mycursor    = my_db.cursor()
        results     = []

        if group_id is not None and group_id.strip() != '' and (group_name is None or group_name.strip() == ''):
            query = """SELECT tu.user_id, tu.access_hash \
                    FROM member_in_group AS mig \
                    INNER JOIN tbl_user AS tu ON mig.member_id = tu.user_id \
                    INNER JOIN tbl_group AS tg ON mig.group_id = tg.group_id \
                    WHERE tg.group_id = %s"""
            
            mycursor.execute(query, (group_id,))
            results = mycursor.fetchall()

        elif group_name is not None and group_name.strip() != '' and (group_id is None or group_id.strip() == ''):
            query = """SELECT tu.user_id, tu.access_hash \
                    FROM member_in_group AS mig \
                    INNER JOIN tbl_user AS tu ON mig.member_id = tu.user_id \
                    INNER JOIN tbl_group AS tg ON mig.group_id = tg.group_id \
                    WHERE tg.group_name = %s"""
            
            mycursor.execute(query, (group_name,))
            results = mycursor.fetchall()

        elif (group_name is not None and group_name.strip() != '') and (group_id is not None and group_id.strip() != ''):
            query = """SELECT tu.user_id, tu.access_hash \
                    FROM member_in_group AS mig \
                    INNER JOIN tbl_user AS tu ON mig.member_id = tu.user_id \
                    INNER JOIN tbl_group AS tg ON mig.group_id = tg.group_id \
                    WHERE mig.group_id = %s or tg.group_name = %s"""

            mycursor.execute(query, (group_id, group_name))
            results = mycursor.fetchall()
        
        list_members = []
        for x in results:
            user = User(user_id= x[0], access_hash = x[1])
            list_members.append(user)

        return list_members

    # ========================================== INSERT =======================================================
    def insert_account(self, acc):
        '''
        This function is used to insert new record of account session to database
        Input:
            acc                     Account     The account you want to insert
        '''
        phone_no = acc.phone_no
        authenticated_datetime = acc.authenticated_datetime        
        api_id = acc.api_id
        api_hash = acc.api_hash

        query = """INSERT INTO tbl_account (phone_no, api_id, api_hash, authenticated_datetime) VALUES (%s, %s, %s, %s) \
                ON DUPLICATE KEY UPDATE \
                phone_no = phone_no, api_id = api_id, \
                api_hash = api_hash, authenticated_datetime = authenticated_datetime"""
        my_db = self.get_db_connection()
        my_db.cursor().execute(query, (phone_no, api_id, api_hash, authenticated_datetime))
        my_db.cursor().close()
    
    
    def insert_user(self, user):
        '''
        This function is used to insert new record of user to database
        Input:
            user     User       The user object you want to insert to DB
        '''
        user_id     = user.user_id
        access_hash = user.access_hash
        query = """INSERT INTO tbl_user (user_id, access_hash) VALUES (%s, %s) \
                ON DUPLICATE KEY UPDATE \
                user_id=user_id, access_hash=access_hash"""
        
        my_db = self.get_db_connection()
        my_db.cursor().execute(query, (user_id, access_hash))
        my_db.cursor().close()


    def insert_group(self, group):
        '''
        This function is used to insert new record of group to database
        Input:
            group           Group       Group object to add to DB
        '''
        group_id = group.group_id
        group_name = group.group_name
        group_type = group.group_type

        query = """INSERT INTO tbl_group (group_id, group_name, group_type) VALUES (%s, %s, %s) \
                ON DUPLICATE KEY UPDATE\
                group_id=group_id, group_name=group_name, group_type=group_type"""
        
        my_db = self.get_db_connection()
        my_db.cursor().execute(query, (group_id, group_name, group_type))
        my_db.cursor().close()


    def insert_send_message_history(self, smh_object):
        '''
        This function is used to insert new record of history log each time system sends message to all members of one group
        Input:
            smh_object      SendMessageHistory      SendMessageHistory object
        '''
        phone_no        = smh_object.phone_no
        group_id        = smh_object.group_id
        member_id       = smh_object.member_id
        message         = smh_object.message
        sent_datetime   = smh_object.sent_datetime

        query = """INSERT INTO send_message_history (phone_no, group_id, member_id, message, sent_datetime) VALUES \
                            (%s, %s, %s, %s, %s)"""
        
        my_db = self.get_db_connection()
        my_db.cursor().execute(query, (phone_no, group_id, member_id, message, sent_datetime))
        my_db.cursor().close()


    def insert_crawl_group_history(self, cgh_object):
        '''
        This function is used to insert new record of history log each time system crawls list of group
        Input:
            cgh_object          CrawlGroupHistory      CrawlGroupHistory object - get each time call Telegram API to crawl list of groups
        '''
        phone_no = cgh_object.phone_no
        source_group_id = cgh_object.source_group_id
        crawled_datetime = cgh_object.crawled_datetime
        query = """INSERT INTO crawl_group_history (phone_no, source_group_id, crawled_datetime) VALUES (%s, %s, %s)"""
                        
        
        my_db = self.get_db_connection()
        my_db.cursor().execute(query, (phone_no, source_group_id, crawled_datetime))
        my_db.cursor().close()


    def insert_add_member_history(self, amh_object):
        '''
        This function is used to insert new record of history log each time user send message
        Input:
            amh_object          AddMemberHistory        AddMemberHistory object
        '''
        phone_no = amh_object.phone_no
        target_group_id = amh_object.target_group_id
        member_id = amh_object.member_id
        add_status = amh_object.add_status
        added_datetime = amh_object.added_datetime

        query = """INSERT INTO add_member_history (phone_no, target_group_id, member_id, add_status, added_datetime) VALUES \
                            (%s, %s, %s, %s, %s)"""
        
        my_db = self.get_db_connection()
        my_db.cursor().execute(query, (phone_no, target_group_id, member_id, add_status, added_datetime))
        my_db.cursor().close()

    
    def insert_member_in_group(self, member_in_group):
        '''
        This function is used to insert new record of the table member_in_group
        Input:
            member_in_group          MemberInGroup        One MemberInGroup object
        '''
        group_id = member_in_group.group_id
        member_id = member_in_group.member_id

        query = """INSERT INTO member_in_group (member_id, group_id) VALUES \
                            (%s, %s) ON DUPLICATE KEY UPDATE member_id=member_id, group_id=group_id"""
        
        my_db = self.get_db_connection()
        my_db.cursor().execute(query, (member_id, group_id))
        my_db.cursor().close()


