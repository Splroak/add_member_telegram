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

from DBWorker import DBWorker

# Load environmental variable
config = dotenv_values(".env")

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

def test_all():
    dbWorker = DBWorker()

    # test insert_account
    logging.info('test insert account')
    acc = Account('+84915268381', '6272920', 'c75b1de1a5e8e68b1f6d0947019823f2', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    acc2 = Account('+84915268384', '6778743', 'ca355f904857e7d3f5155cd396a3dce7', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    dbWorker.insert_account(acc)
    dbWorker.insert_account(acc2)
    
    # test insert_user
    logging.info('test insert user')
    user1 = User('user_1', 'access_hash_1')
    user2 = User('user_2', 'access_hash_2')
    user3 = User('user_3', 'access_hash_3')
    user4 = User('user_4', 'access_hash_4')
    dbWorker.insert_user(user1)    
    dbWorker.insert_user(user2)    
    dbWorker.insert_user(user3)    
    dbWorker.insert_user(user4)    

    # test insert_group
    logging.info('test insert group')
    group1 = Group('group_1', 'group_name_1', 0)
    group2 = Group('group_2', 'group_name_2', 1)
    group3 = Group('group_3', 'group_name_1', 1)
    dbWorker.insert_group(group1)    
    dbWorker.insert_group(group2)    
    dbWorker.insert_group(group3)    

    # test insert_member_in_group
    logging.info('test insert men_in_group')
    mem_in_group1 = MemberInGroup(group_id='group_1', member_id='user_1')
    mem_in_group2 = MemberInGroup(group_id='group_1', member_id='user_2')
    mem_in_group3 = MemberInGroup(group_id='group_1', member_id='user_3')
    mem_in_group4 = MemberInGroup(group_id='group_3', member_id='user_4')
    dbWorker.insert_member_in_group(mem_in_group1)
    dbWorker.insert_member_in_group(mem_in_group2)
    dbWorker.insert_member_in_group(mem_in_group3)
    dbWorker.insert_member_in_group(mem_in_group4)

    # test crawl_group_history
    logging.info('test crawl_group_history')
    cgh_object = CrawlGroupHistory(acc=acc, source_group=group1, crawled_datetime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    dbWorker.insert_crawl_group_history(cgh_object)    

    # test add_member_history
    logging.info('test add_member_history')
    amh_object = AddMemberHistory(acc=acc, member=user1, target_group=group1, add_status=True, added_datetime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    dbWorker.insert_add_member_history(amh_object)

    # test send_message_history
    logging.info('test send_message_history')
    smh_object = SendMessageHistory(acc=acc, member=user1, group=group1, message='Test send message', sent_datetime=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    dbWorker.insert_send_message_history(smh_object)
    
    
    
    # -----------------------------------------------------------------------------------------------------
    # -----------------------------------------------------------------------------------------------------
    
    
    # test select_all_accounts
    logging.info('test select_all_accounts')
    list_account = dbWorker.select_all_accounts()
    for acc in list_account:
        print(acc)

    # test select_all_groups
    logging.info('test select_all_groups')
    list_group = dbWorker.select_all_groups()
    for gr in list_group:
        print(gr)

    # test select_all_members_in_one_group
    logging.info('test select_all_members_in_one_group')
    list_members = dbWorker.select_all_members_in_one_group(group_id = 'group_1', group_name=None)
    list_members = dbWorker.select_all_members_in_one_group(group_id = None, group_name='group_name_1')
    for member in list_members:
        print(member)

    # test select_available_add_accounts
    logging.info('test select_available_add_accounts')
    list_account = dbWorker.select_available_add_accounts()
    for acc in list_account:
        print(acc)

    # test select_available_send_accounts
    logging.info('test select_available_send_accounts')
    list_account = dbWorker.select_available_send_accounts()
    for acc in list_account:
        print(acc)

    return

if __name__ == '__main__':
    try:
        # Create database: crawl_telegram
        test_all()
    except Exception as e:
        logging.exception(e)