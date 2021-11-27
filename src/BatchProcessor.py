import os
from dotenv import load_dotenv, dotenv_values

# FOR TELEGRAM
from telethon.sync import TelegramClient
from telethon.tl.types import InputPeerChannel, InputPeerEmpty, PeerUser
from telethon.tl.types import InputPeerUser
from telethon.tl.functions.channels import InviteToChannelRequest, InviteToChannelRequest, JoinChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.errors.rpcerrorlist import PeerFloodError, UserPrivacyRestrictedError, UserBannedInChannelError, \
    UserChannelsTooMuchError, PhoneNumberBannedError

# FOR LOG
import logging
from logging.handlers import RotatingFileHandler
import datetime
import math

# FOR MULTITHREAD
import asyncio
import multiprocessing

# FOR OTHER PURPOSE
import time

# Load environmental variable
config = dotenv_values(".env")

# --------------------------------------------------- LOGGING ---------------------------------------------------------
# Create new log folder if not exist
# LOG_FOLDER_NAME = config.get('LOG_FOLDER_NAME')
# LOG_FOLDER = os.path.join(os.getcwd(), LOG_FOLDER_NAME)
# LOG_FILE = os.path.join(LOG_FOLDER, 'log_{datetime}.log'.format(datetime=datetime.datetime.now().strftime('%Y-%m-%d')))
# MAXBYTES = (config.get('MAXBYTES'))
# BACKUP_COUNT = config.get('BACKUP_COUNT')
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

class BatchProcessor:
    def __init__(self):
        '''
        This class is used to process batch of members in Telegram
        '''
        self.number_add_members = 0

    def divide_into_batch(self, list_available_accounts, list_members, num_mem_per_acc=45):
        '''
        This class is used to divide list of member for each available account
        Each account can only be used to:
        - add maximum 60 members/ day
        - send 45 message /day
        
        Input:
            - list_available_accounts:          List(Account)           List of accounts that hasn't been used in 1 day up-to-now
            - list_members:                     List(User)              List of members that needed to be added/sent emails
            - num_mem_per_acc:                  Int                     Max number of members that 1 acc can add/send message 
        Output:
            - list_use_accounts                 List(Account)           List of accounts to use
            - dict_batch:                       Dict                    Dict contains batch of members divided for each account
                                                                            key: index: (INT) 0,1,2,...
                                                                            value: Tuple 2 elements (Account, List<User>)
            - is_lack_acc:                      Boolean                 + True: Lack accounts to proceed 
                                                                        - False: Enough account to proceed
            - max_mem_process:                  Int                     Max number of accounts can be proceeded
        '''
        # Cast num_mem_per_acc to INT
        num_mem_per_acc = int(num_mem_per_acc)

        # Get list of needed accounts
        num_required_acc = math.ceil(len(list_members) / int(num_mem_per_acc))

        is_lack_acc = False
        max_mem_process = 0
        list_use_accounts = list_available_accounts

        logging.info(f'len available accounts = {len(list_available_accounts)}')
        if len(list_available_accounts) < num_required_acc:
            is_lack_acc = True
            max_mem_process = int(len(list_use_accounts) * int(num_mem_per_acc))
            logging.info(f'is lack = {is_lack_acc}, max_mem_process: {max_mem_process}')
        else:
            is_lack_acc = False
            list_use_accounts = list_available_accounts[:num_required_acc]
            max_mem_process = len(list_members)
            logging.info(f'is lack = {is_lack_acc}, max_mem_process: {max_mem_process}')

        # Divide to each batch
        dict_batch = {}
        start_idx = 0
        for idx, acc in enumerate(list_use_accounts):
            end_idx = int((idx + 1) * (num_mem_per_acc)) 
            dict_batch[str(idx)] = (acc, list_members[start_idx:end_idx]) 
            start_idx = end_idx 

        return list_use_accounts, dict_batch, is_lack_acc, max_mem_process


    async def p_add_one_batch_to_group(self, source_group_name, target_group_name, tupple_batch, thread_name, count_lock, count_incre):
        '''
        This function is used to add one batch of member.
        This help to proceed this adding function with multiple threads
        Input:
            - source_group_name                     String      Name of the source group
            - target_group_name                     String      Name of the target group
            - list_filtered_accounts:               List        List of filtered accounts.
                                                                These accounts are not banned + add to target group successfully
            - tuple_batch:                          Tuple       Tuple of 1 batch in format
                                                                    - Element 1st:  Account object -> storing phone_no, api_id, api_hash
                                                                    - Element 2nd:  1 List with multiple User object
                                                                                each User object = 1 member need to be added to the target group
            - thread_name                           String      Name assigned for the each thread.
        '''
        try:
            logging.info(f'----- THREAD: {thread_name}: START ADDING BATCH OF MEMS -----')
            GROUP_PREFIX = 't.me/'

            acc = tupple_batch[0]
            list_mems = tupple_batch[1]

            # Init TelegramClient
            client = TelegramClient(f'sessions\\{acc.phone_no}', acc.api_id, acc.api_hash)
            await client.connect()
            await asyncio.sleep(1.5)

            # Get access to the group: group link = t.me/group_name
            logging.info(f' THREAD: {thread_name}: Adding members to group_name: {target_group_name}')
            target_group = await client.get_entity(str(GROUP_PREFIX + target_group_name))
            entity = InputPeerChannel(target_group.id, target_group.access_hash)
            group_title = target_group.title

            ####
            source_group = await client.get_entity(str(GROUP_PREFIX + source_group_name))
            ####

            await client.get_participants(source_group)

            logging.info(f'THREAD: {thread_name}: Adding members to group_title: {group_title}')

            # Start adding
            for user in list_mems:
                current_adding_mem = []
                try:
                    logging.info(f'THREAD: {thread_name}: ***** Processing: {user.user_id}')
                    # Increment this variable to set progress bar
                    count_lock.acquire()
                    count_incre.value = count_incre.value + 1 
                    count_lock.release()
                    
                    # NOTES:  client.get_entity() get an input as one INT
                    user_entity = await client.get_entity(int(user.user_id))
                    await asyncio.sleep(1)
                    current_adding_mem.append(user_entity)
                    await client(InviteToChannelRequest(entity, current_adding_mem))
                    
                except UserPrivacyRestrictedError:
                    logging.exception(f'THREAD: {thread_name}: User is private')
                except UserBannedInChannelError:
                    logging.exception(f'THREAD: {thread_name}: {acc.phone_no} is banned')
                except UserChannelsTooMuchError:
                    logging.exception(f'THREAD: {thread_name}: This user is already in too many channel')
                except ValueError:
                    logging.exception(f'THREAD: {thread_name}: User not found')
                except Exception as e:
                    logging.exception(e)

                logging.info(f'THREAD: {thread_name}: Sleep 20s')
                await asyncio.sleep(20)
            
            await client.disconnect()
            logging.info(f'----- THREAD: {thread_name}. FINISH ADDING BATCH OF MEMS -----')

        except Exception as e:
            logging.exception(f'THREAD: {thread_name}: {e}')


    def sequential_add_member_to_group(self, source_group_name, target_group_name, list_filtered_accounts, dict_batch):
        '''
        This function is used to add members to groups
        The account which is used to add member has been divided by BatchProcessor
        Input:
            - source_group_name                     String      Name of the source group
            - target_group_name                     String      Name of the target group
            - list_filtered_accounts:               List        List of filtered accounts. 
                                                                These accounts are not banned + add to target group successfully
            - dict_batch:                           Dict        Dict of batch in format
                                                                    key: index: 0,1,2,...
                                                                    value: Tuple 2 elements (Account, List<User>)
        '''
        try:
            GROUP_PREFIX = 't.me/'
            for key in dict_batch:
                batch = dict_batch.get(key)
                acc = batch[0]
                list_mems = batch[1]

                logging.info(f'----- SEQUENCE: Sequence_add_mems_{key}: START ADDING BATCH OF MEMS -----')

                # Init TelegramClient
                client = TelegramClient(f'sessions\\{acc.phone_no}', acc.api_id, acc.api_hash)
                client.connect()
                time.sleep(1.5)

                # Get access to the group: group link = t.me/group_name
                logging.info(f'SEQUENCE: Sequence_add_mems_{key}: Adding members to group_name: {target_group_name}')
                target_group = client.get_entity(str(GROUP_PREFIX + target_group_name))
                entity = InputPeerChannel(target_group.id, target_group.access_hash)
                group_title = target_group.title
                
                ####
                source_group = client.get_entity(str(GROUP_PREFIX + source_group_name))
                ####

                client.get_participants(source_group)

                logging.info(f'SEQUENCE: Sequence_add_mems_{key}: Adding members to group_title: {group_title}')

                # Start adding
                for user in list_mems:
                    current_adding_mem = []
                    try:
                        logging.info(f'SEQUENCE: Sequence_add_mems_{key}: Processing: {user.user_id}')
                        # NOTES:  client.get_entity() get an input as one INT
                        user_entity = client.get_entity(int(user.user_id))
                        time.sleep(1)
                        current_adding_mem.append(user_entity)
                        client(InviteToChannelRequest(entity, current_adding_mem))
                    except UserPrivacyRestrictedError:
                        logging.exception(f'SEQUENCE: Sequence_add_mems_{key}: User is private')
                    except UserBannedInChannelError:
                        logging.exception(f'SEQUENCE: Sequence_add_mems_{key}: {acc.phone_no} is banned')
                    except UserChannelsTooMuchError:
                        logging.exception(f'SEQUENCE: Sequence_add_mems_{key}: This user is already in too many channel')
                    except ValueError:
                        logging.exception(f'SEQUENCE: Sequence_add_mems_{key}: User not found')
                    except Exception as e:
                        logging.exception(f'SEQUENCE: Sequence_add_mems_{key}: {e}')

                    logging.info(f'SEQUENCE: Sequence_add_mems_{key}: Sleep 20s')
                    time.sleep(20)
                
                client.disconnect()
                logging.info(f'----- SEQUENCE: Sequence_add_mems_{key}: FINISH ADDING BATCH OF MEMS -----')

        except Exception as e:
            logging.exception(e)

        

    def send_sms_to_menber(self, target_group_name, text_sms, dict_batch):
        """

        :param text_sms:
        :param dict_batch:
        :return:
        """
        GROUP_PREFIX = 't.me/'
        
        for key in dict_batch:
            batch = dict_batch.get(key)
            acc = batch[0]
            list_mems = batch[1]

            # client = TelegramClient(f'sessions\\{acc.phone_no}', acc.api_id, acc.api_hash)
            logging.info(f'++++++++++++++++++++++ {acc.phone_no}, {acc.api_id}, {acc.api_hash}')
            client = TelegramClient(f'sessions\\{acc.phone_no}', acc.api_id, acc.api_hash)
            client.connect()
            client.start()

            # Make sender and receiver encounter for sure
            target_group = client.get_entity(str(GROUP_PREFIX + target_group_name))
            client.get_participants(target_group)
            ####


            time.sleep(1.5)
            for user in list_mems:
                try:
                    logging.info(f'----------- Sending message for {user.user_id}, {user.access_hash} ')
                    receiver = client.get_entity(int(user.user_id))
                    client.send_message(receiver, text_sms)
                    time.sleep(5)
                except PeerFloodError as e:
                    client.disconnect()
                    logging.exception(e)
                except Exception as e:
                    logging.exception(f'Error: {e}')
                    continue

            client.disconnect()


    async def p_send_sms_to_menbers(self, target_group_name, text_sms, tuple_batch, thread_name, count_lock, count_incre):
        """

        :param text_sms:
        :param dict_batch:
        :return:
        """
        try:
            logging.info(f'----- THREAD: {thread_name}: START SENDING MESSAGE TO A BATCH OF MEMS -----')
            GROUP_PREFIX = 't.me/'
            acc = tuple_batch[0]
            list_mems = tuple_batch[1]

            client = TelegramClient(f'sessions\\{acc.phone_no}', acc.api_id, acc.api_hash)
            await client.connect()
            
            # Make sender and receiver encounter for sure
            target_group = await client.get_entity(str(GROUP_PREFIX + target_group_name))
            await client.get_participants(target_group)
            ####

            await asyncio.sleep(1.5)
            for user in list_mems:
                try:
                    # Increment this variable to set progress bar
                    count_lock.acquire()
                    count_incre.value = count_incre.value + 1 
                    count_lock.release()
                    
                    receiver = await client.get_entity(int(user.user_id))
                    await client.send_message(receiver, text_sms)
                    await asyncio.sleep(5)
                except PeerFloodError:
                    logging.exception(f'THREAD: {thread_name}: {e}')
                except Exception as e:
                    logging.exception(f'THREAD: {thread_name}: {e}')
                    continue

            await client.disconnect()
            logging.info(f'----- THREAD: {thread_name}: FINISH SENDING MESSAGE TO A BATCH OF MEMS -----')
        except Exception as e:
            logging.exception(f'{e}')
        


    def go(self, source_group_name = None, target_group_name = None, batch = None, thread_name = None, \
                    text_msg = None, action = None, count_lock = None, count_incre = None):
        '''
        This function is used as a bridge to call the core function
        which is passed as target of Thread.

        If action == 'add_members_to_group'         ---> call core: p_add_one_batch_to_group()
        If action == 'send_message_all_members'     ---> call core: p_send_sms_to_menber()
        Input:
            - source_group_name                     String                      Name of the source group
            - target_group_name                     String                      Name of the target group
            - list_filtered_accounts:               List                        List of filtered accounts.
                                                                                    - These accounts are not banned + add to target group successfully
            - batch:                                Tuple                       Tuple of 1 batch in format
                                                                                    - Element 1st:  Account object -> storing phone_no, api_id, api_hash
                                                                                    - Element 2nd:  1 List with multiple User object
                                                                                                each User object = 1 member need to be added to the target group
            - thread_name                           String                      Name assigned for the each thread.
            - text_msg                              String                      Default: None. The input will be passed when action = 'send_message_all_members'
            - action                                String                      Action that user want to do paralelly
                                                                                    - Action 1: ADD_MEMBERS_TO_GROUP
                                                                                    - Action 2: SEND_MESSAGE_ALL_MEMBERS
            - count_lock                            Multiprocessing.Lock        Log is used to avoid concurrent
            - count_incre                           Multiprocessing.Valie       Value is used to count number of added/sent members
        '''
        if action == 'ADD_MEMBERS_TO_GROUP':
            asyncio.run(self.p_add_one_batch_to_group(source_group_name, target_group_name, batch, thread_name, count_lock, count_incre))
        elif action == 'SEND_MESSAGE_ALL_MEMBERS':
            asyncio.run(self.p_send_sms_to_menbers(target_group_name, text_msg, batch, thread_name, count_lock, count_incre))
