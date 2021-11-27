import os
import sys
import logging
from logging.handlers import RotatingFileHandler
import datetime
import mysql.connector
from dotenv import load_dotenv, dotenv_values


# Load environmental variable
config  = dotenv_values(".env")
        
# --------------------------------------------------- LOGGING ---------------------------------------------------------
# Create new log folder if not exist
LOG_FOLDER_NAME = config.get('LOG_FOLDER_NAME')
LOG_FOLDER      = os.path.join(os.getcwd(), LOG_FOLDER_NAME)
LOG_FILE        = os.path.join(LOG_FOLDER, 'log_{datetime}.log'.format(datetime=datetime.datetime.now().strftime('%Y-%m-%d')))
MAXBYTES        = (config.get('MAXBYTES'))
BACKUP_COUNT    = config.get('BACKUP_COUNT')

# Set up logging basic config
try:
    handler_rfh = RotatingFileHandler(LOG_FILE, maxBytes=int(MAXBYTES), backupCount=int(BACKUP_COUNT))
    handler_rfh.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s', \
                        datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.getLogger('CRAWL_TELEGRAM').addHandler(handler_rfh)

except Exception as e:
    logging.exception(e)
# ----------------------------------------------------------------------------------------------------------------------

DB_NAME = config.get('DB_NAME')
DB_USER = config.get('DB_USER')
DB_PASSWORD = config.get('DB_PASSWORD')
DB_HOST = config.get('DB_HOST')
DB_PORT = config.get('DB_PORT')


def create_database():
    mydb = mysql.connector.connect(
        port=DB_PORT,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        auth_plugin='mysql_native_password'
    )

    mycursor = mydb.cursor()

    mycursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(DB_NAME))
    mycursor.close()


def get_db_connection():
    connection = mysql.connector.connect(
        port=DB_PORT,
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        auth_plugin='mysql_native_password'
    )
    connection.autocommit = True
    return connection


def create_account_table_query():
    query = 'CREATE TABLE IF NOT EXISTS tbl_account' \
            '(phone_no VARCHAR(20) NOT NULL,' \
            'api_id VARCHAR(20) NOT NULL,' \
            'api_hash VARCHAR(60) NOT NULL,' \
            'authenticated_datetime DATETIME NOT NULL,'\
            'PRIMARY KEY(phone_no)'\
            ');'
    return query


def create_user_table_query():
    query = 'CREATE TABLE IF NOT EXISTS tbl_user' \
            '(user_id VARCHAR(60) NOT NULL,' \
            'access_hash VARCHAR(60) NOT NULL,'\
            'PRIMARY KEY(user_id)'\
            ');'
    return query


def create_group_table_query():
    query = 'CREATE TABLE IF NOT EXISTS tbl_group' \
            '(group_id VARCHAR(60) NOT NULL,' \
            'group_name VARCHAR(255) NOT NULL,'\
            'group_type INT NOT NULL,'\
            'PRIMARY KEY(group_id)'\
            ');'
    return query


def create_member_in_group_table_query():
    query = 'CREATE TABLE IF NOT EXISTS member_in_group' \
            '(group_id VARCHAR(60) NOT NULL,' \
            'member_id VARCHAR(60) NOT NULL,'\
            \
            'PRIMARY KEY(group_id, member_id),'\
            'INDEX (group_id),'\
            'INDEX (member_id),'\
            \
            'FOREIGN KEY (group_id) '\
            'REFERENCES tbl_group(group_id),'\
            \
            'FOREIGN KEY (member_id) '\
            'REFERENCES tbl_user(user_id)'\
            ');'
    return query

def create_add_member_history_table_query():
    '''
    Table add_member_history
    - status:       Boolean     True: add member successfully. False: add member fail
    '''

    query = 'CREATE TABLE IF NOT EXISTS add_member_history' \
            '(id INT NOT NULL AUTO_INCREMENT,'\
            'phone_no VARCHAR(20) NOT NULL,' \
            'member_id VARCHAR(60) NOT NULL,'\
            'target_group_id VARCHAR(60) NOT NULL,'\
            'add_status BOOLEAN NOT NULL,'\
            'added_datetime DATETIME NOT NULL,'\
            \
            'PRIMARY KEY(id),'\
            'INDEX (phone_no),'\
            'INDEX (member_id),'\
            'INDEX (target_group_id),'\
            \
            'FOREIGN KEY (phone_no) '\
            'REFERENCES tbl_account(phone_no),'\
            \
            'FOREIGN KEY (target_group_id) '\
            'REFERENCES tbl_group(group_id),'\
            \
            'FOREIGN KEY (member_id) '\
            'REFERENCES tbl_user(user_id)'\
            ');'
    return query


def create_crawl_group_history_table_query():
    query = 'CREATE TABLE IF NOT EXISTS crawl_group_history' \
            '(id INT NOT NULL AUTO_INCREMENT,'\
            'phone_no VARCHAR(20) NOT NULL,' \
            'source_group_id VARCHAR(60) NOT NULL,'\
            'crawled_datetime DATETIME NOT NULL,'\
            \
            'PRIMARY KEY(id),'\
            'INDEX (phone_no),'\
            'INDEX (source_group_id),'\
            \
            'FOREIGN KEY (phone_no) '\
            'REFERENCES tbl_account(phone_no),'\
            \
            'FOREIGN KEY (source_group_id) '\
            'REFERENCES tbl_group(group_id)'\
            ');'
    return query


def create_send_message_history_table_query():
    query = 'CREATE TABLE IF NOT EXISTS send_message_history' \
            '(id INT NOT NULL AUTO_INCREMENT,'\
            'phone_no VARCHAR(20) NOT NULL,' \
            'member_id VARCHAR(60) NOT NULL,'\
            'group_id VARCHAR(60) NOT NULL,'\
            'message TEXT NOT NULL,'\
            'sent_datetime DATE NOT NULL,'\
            \
            'PRIMARY KEY(id),'\
            'INDEX (phone_no),'\
            'INDEX (member_id),'\
            'INDEX (group_id),'\
            \
            'FOREIGN KEY (phone_no) '\
            'REFERENCES tbl_account(phone_no),'\
            \
            'FOREIGN KEY (group_id) '\
            'REFERENCES tbl_group(group_id),'\
            \
            'FOREIGN KEY (member_id) '\
            'REFERENCES tbl_user(user_id)'\
            ');'
    return query


def create_sp_get_available_add_account():
    drop_query = """
                DROP PROCEDURE IF EXISTS sp_get_available_add_account; 
                """
    query = """ 
            CREATE PROCEDURE sp_get_available_add_account() 
            BEGIN 
                DROP TEMPORARY TABLE IF EXISTS amh_1_day; 
                
                CREATE TEMPORARY TABLE amh_1_day AS ( 
                    SELECT amh.phone_no 
                    FROM add_member_history as amh 
                    WHERE amh.added_datetime >= NOW() - INTERVAL 1 DAY 
                    GROUP BY amh.phone_no 
                ); 
                IF EXISTS(SELECT * FROM amh_1_day) THEN 
                -- If has data of any account used to add member within 1-day interval 
                    SELECT DISTINCT ta.phone_no, ta.api_id, ta.api_hash, ta.authenticated_datetime 
                    FROM tbl_account AS ta, amh_1_day 
                    WHERE ta.phone_no != amh_1_day.phone_no; 
                ELSE 
                -- If there is no data of account used to add member within 1-day interval 
                    SELECT ta.phone_no, ta.api_id, ta.api_hash, ta.authenticated_datetime 
                    FROM tbl_account as ta; 
                END IF; 
                
            END 
            """
    return drop_query, query


def create_sp_get_available_send_account():
    drop_query = """
                DROP PROCEDURE IF EXISTS sp_get_available_send_account;
                """

    query = """ 
            CREATE PROCEDURE sp_get_available_send_account()
            BEGIN
                DROP TEMPORARY TABLE IF EXISTS smh_1_day;

                CREATE TEMPORARY TABLE smh_1_day AS (
                    SELECT smh.phone_no
                    FROM send_message_history as smh
                    WHERE smh.sent_datetime >= NOW() - INTERVAL 1 DAY
                    GROUP BY smh.phone_no
                );
                IF EXISTS(SELECT * FROM smh_1_day) THEN
                -- If has data of any account used to add member within 1-day interval
                    SELECT DISTINCT ta.phone_no, ta.api_id, ta.api_hash, ta.authenticated_datetime
                    FROM tbl_account AS ta, smh_1_day
                    WHERE ta.phone_no != smh_1_day.phone_no;
                ELSE
                -- If there is no data of account used to add member within 1-day interval
                    SELECT ta.phone_no, ta.api_id, ta.api_hash, ta.authenticated_datetime
                    FROM tbl_account as ta;
                END IF;

            END 
            """
    return drop_query, query
    

def create_tables():
    connection = get_db_connection()
    mycursor = connection.cursor()

    # ---------------------- CREATE TABLES -------------------------
    logging.info('Start create table: account if not exists')
    mycursor.execute(create_account_table_query())
    logging.info('Create table: account successfully')

    logging.info('Start create table: user if not exists')
    mycursor.execute(create_user_table_query())
    logging.info('Create table: user successfully')
    
    logging.info('Start create table: group if not exists')
    mycursor.execute(create_group_table_query())
    logging.info('Create table: group successfully')
    
    logging.info('Start create table: member_in_group if not exists')
    mycursor.execute(create_member_in_group_table_query())
    logging.info('Create table: member_in_group successfully')
    
    logging.info('Start create table: add_member_history if not exists')
    mycursor.execute(create_add_member_history_table_query())
    logging.info('Create table: add_member_history successfully')
    
    logging.info('Start create table: crawl_group_history if not exists')
    mycursor.execute(create_crawl_group_history_table_query())
    logging.info('Create table: crawl_group_history successfully')
    
    logging.info('Start create table: send_message_history if not exists')
    mycursor.execute(create_send_message_history_table_query())
    logging.info('Create table: send_message_history successfully')
    
    mycursor.close()
    connection.close()


def create_stored_procedure():
    connection = get_db_connection()
    mycursor = connection.cursor()

    # ---------------------- CREATE STORED PROCEDURE -------------------------
    logging.info('Start create stored procedure: sp_get_available_add_account if not exists')
    drop_query, query = create_sp_get_available_add_account()
    mycursor.execute(drop_query)
    mycursor.execute(query)
    logging.info('Create SP: sp_get_available_add_account successfully')
    
    logging.info('Start create stored procedure: sp_get_available_send_account if not exists')
    drop_query, query = create_sp_get_available_send_account()
    mycursor.execute(drop_query)
    mycursor.execute(query)
    logging.info('Create SP: sp_get_available_send_account successfully')
    
    mycursor.close()
    connection.close()

if __name__ == '__main__':
    try:
        # Create database: crawl_telegram
        create_database()
        # Create tables: account, member, group, member_in_group, crawl_user_history, add_user_history
        create_tables()
        # Create stored procedure: sp_get_available_add_account + sp_get_available_send_account
        create_stored_procedure()
        logging.info('--- FINISH CREATING DATABASE AND TABLES')
    except Exception as e:
        logging.exception(e)