import os
from dotenv import load_dotenv, dotenv_values

# FOR LOG
import logging
from logging.handlers import RotatingFileHandler
import datetime
import math
import json

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
from entities.Account import Account
from entities.User import User
from BatchProcessor import BatchProcessor

if __name__ == "__main__":
    bpro = BatchProcessor()

    num_mem_per_acc = 4
    list_members = []
    for i in range(3):
        member = User(f'user_id_{i}', f'access_hash_{i}')
        list_members.append(member)
    
    list_accounts = []
    for i in range(3):
        acc = Account(f'phone_no_{i}', f'api_id_{i}', f'api_hash_{i}', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        list_accounts.append(acc)
    
    logging.info(list_accounts)
    logging.info(list_members)

    list_use_accounts, dict_batch, is_lack_acc, max_mem_process = bpro.divide_into_batch(list_accounts, list_members, num_mem_per_acc)
    
    logging.info(', '.join([acc.phone_no for acc in list_use_accounts]))
    logging.info(is_lack_acc)
    logging.info(max_mem_process)

    for key in dict_batch:
        print(key)
        print('Account:' ,dict_batch[key][0])
        print('List members:')
        print(*dict_batch[key][1], sep='\n')
