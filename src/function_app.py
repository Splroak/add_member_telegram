import asyncio
from UI.telegram_ui import *
import sys
import os
from telethon.sync import TelegramClient
from telethon.errors.rpcerrorlist import PhoneNumberBannedError, PeerFloodError, UserCreatorError
from telethon.tl.functions.channels import JoinChannelRequest, EditAdminRequest
from telethon.tl.types import ChatAdminRights, PeerUser, Channel

from models.Worker import Worker
import random
from config import API_DICT
from types import MethodType

# FOR LOG
import logging
from logging.handlers import RotatingFileHandler
import datetime

# FOR DB
from dotenv import load_dotenv, dotenv_values

from entities.Account import Account
from entities.User import User
from entities.Group import Group
from entities.AddMemberHistory import AddMemberHistory
from entities.CrawlGroupHistory import CrawlGroupHistory
from entities.SendMessageHistory import SendMessageHistory
from entities.MemberInGroup import MemberInGroup
from BatchProcessor import BatchProcessor
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QRegExpValidator
from PyQt5.QtCore import QThread, pyqtSignal

# import phonenumbers
from DBWorker import DBWorker

# FOR CALCULATION
import math

# FOR MULTITHREAD
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
class CustomMessageBox(QMessageBox):

    def __init__(self, *__args):
        QMessageBox.__init__(self)
        self.timeout = 0
        self.autoclose = False
        self.currentTime = 0

    def showEvent(self, QShowEvent):
        self.currentTime = 0
        if self.autoclose:
            self.startTimer(1000)

    def timerEvent(self, *args, **kwargs):
        self.currentTime += 1
        if self.currentTime >= self.timeout:
            self.done(0)

    @staticmethod
    def showWithTimeout(timeoutSeconds, message, title, icon=QMessageBox.Information, buttons=QMessageBox.Ok):
        w = CustomMessageBox()
        w.autoclose = True
        w.timeout = timeoutSeconds
        w.setText(message)
        w.setWindowTitle(title)
        w.setIcon(icon)
        # w.setStandardButtons()
        w.exec_()
# ----------------------------------------------------------------------------------------------------------------------
class Popup:
    def __init__(self):
        pass

    # def valiate_phone_number(self, phone_number_str):
    #     my_number = phonenumbers.parse(phone_number_str)
    #     return phonenumbers.is_valid_number(my_number)

    def show_popup(self, title=None, msg_text=None, info=True):
        msg = QMessageBox()
        # msg.setStyleSheet("QLabel{min-width:100 px; font-size: 12px;} QPushButton{ width:50px; font-size: 18px; }")
        msg.setWindowTitle(title)
        msg.setText(msg_text)
        if info == True:
            msg.setIcon(QMessageBox.Information)
        else:
            msg.setIcon(QMessageBox.Warning)
        x = msg.exec_()

# ----------------------------------------------------------------------------------------------------------------------
class ProgressUpdater(QThread):
    """
    This class is used to create QThread updating progress bar of each screen
    It receive one Multiprocess.Value variable as the sharing counter among threads
    """
    params = pyqtSignal(list)

    def __init__(self, count_incre, filtered_max_num_members) -> None:
        super().__init__()
        self.count_incre = count_incre
        self.filtered_max_num_members = filtered_max_num_members

    def run(self):
        while True:
            time.sleep(1)
            percentage = int((self.count_incre.value / self.filtered_max_num_members) * 100)
            logging.info(f'------------------- Progress update: {percentage}, {self.count_incre.value}, {self.filtered_max_num_members}')
            signal_list = [percentage, self.count_incre.value]
            self.params.emit(signal_list)

            if self.count_incre.value >= self.filtered_max_num_members:
                break


class Mainprogram(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(Mainprogram, self).__init__(parent)
        self.setFixedSize(700,1600)
        self.setupUi(self)
        self.btn_add_phone.clicked.connect(self.btnclick_add_phone)
        self.btn_save.clicked.connect(self.btn_save_phone)
        self.btn_Crawl_member.clicked.connect(self.btn_crawl_member)
        self.btn_add_member.clicked.connect(self.btn_add_member_func)
        self.btn_send_messger.clicked.connect(self.btn_send_mes)
        self.pushButton_add_channel.clicked.connect(self.btn_add_to_channel)
        self.tableWidget.setColumnWidth(0, 250)
        self.tableWidget.setColumnWidth(0, 250)
        self.tableWidget_group.setColumnWidth(0, 250)
        self.popup = Popup()
        self.dbWorker = DBWorker()
        self.get_all_group_with_db()
        self.get_all_phone()
        self.phone_row = 0
        self.group_row = 0
        self.current_credentials = {}
        self.current_phone = None
        self.current_client = None
        self.custommessagebox = CustomMessageBox()
        self.progressBar_crawl.setValue(0)
        self.progressBar_add_menber.setValue(0)
        self.progressBar_send_sms.setValue(0)
        self.progressBar_add_menber_sc.setValue(0)
        self.load_data_phone_list()
        self.load_data_group()
        self.btn_cancel_add_member.clicked.connect(self.terminate_add_member_gr_thread)
        self.btn_cancel_send_sms.clicked.connect(self.terminate_sending_message_thread)
        self.list_adding_member_gr_threads = []
        self.list_adding_member_sc_threads = []
        self.list_sending_message_threads = []
        self.add_member_gr_progress_updater = None
        self.add_member_sc_progress_updater = None
        self.send_message_progress_updater = None
        self.admin_rights = ChatAdminRights(post_messages=True,
                                            add_admins=True,
                                            invite_users=True,
                                            change_info=True,
                                            ban_users=True,
                                            delete_messages=True,
                                            pin_messages=True,
                                            edit_messages=True)

    def get_all_group_with_db(self):
        """

        """
        all_group_name = []

        list_group = self.dbWorker.select_all_groups()
        for gr in list_group:
            all_group_name.append(gr.group_name)
        completer = QtWidgets.QCompleter(all_group_name)
        self.input_source_group_sms.setCompleter(completer)
        self.source_group_add.setCompleter(completer)
        self.lineEdit_channel_source_group.setCompleter(completer)

    def get_all_phone(self):
        all_acc = []

        list_acc = self.dbWorker.select_all_accounts()
        for acc in list_acc:
            all_acc.append(acc.phone_no)
        completer = QtWidgets.QCompleter(all_acc)
        self.lineEdit_channel_main_phone.setCompleter(completer)


    def btnclick_add_phone(self):
        """
        lấy số điện thoại về khi click button add
        :return:
        """
        try:
            if self.input_phone_no.toPlainText() == "":
                self.popup.show_popup(title='ERROS', msg_text='Please enter a phone number', info=False)
            else:
                phone = self.input_phone_no.toPlainText()

                i = random.randint(1, len(API_DICT))
                api_id = API_DICT[i]['api_id']
                api_hash = API_DICT[i]['api_hash']

                self.current_credentials = {'phone': phone, 'api_id': api_id, 'api_hash': api_hash}
                self.current_client = TelegramClient(f'sessions/{phone}', api_id, api_hash)
                self.current_client.connect()

                if not self.current_client.is_user_authorized():
                    print('not authorized')
                    self.current_client.send_code_request(phone)
        except Exception as e:
            logging.exception(e)

    def btn_save_phone(self):
        """
        lấy về authen code khi nhập và click button save
        :return:
        """
        try:

            authen_code = self.input_code.toPlainText()
            print(authen_code)
            phone = self.current_credentials['phone']
            api_id = self.current_credentials['api_id']
            api_hash = self.current_credentials['api_hash']
            self.current_client.sign_in(phone, authen_code)
            print("signed in")

            acc = Account(phone, api_id, api_hash, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            self.dbWorker.insert_account(acc)
            self.current_client.disconnect()

            self.load_data_phone_list()
            self.input_phone_no.clear()
            self.input_code.clear()
        except Exception as e:
            logging.exception(e)

    def btn_crawl_member(self):
        """
        get source group and group type khi click btn crawl
        :return:
        """
        try:
            #   get_entity cái group source (@params: link t.me/ của group)
            #   get_participant cái group đấy (@param: group entity)
            #   catch các exception
            #   TODO: pick bừa 1 thằng từ db để log in (id, hash, phone)
            if self.input_source_group.toPlainText() == "":
                self.popup.show_popup(title='ERROR', msg_text='Source Group No Null', info=False)
                return
            if self.input_source_group.toPlainText()[0] == '@':
                self.popup.show_popup(title='ERROR', msg_text='Source Group  Not:  @ ', info=False)
                return
            else:
                source_group_name = 't.me/' + self.input_source_group.toPlainText()
                print('passed 1')

            worker = self.dbWorker.select_top_account()
            phone = worker.phone_no
            api_id = worker.api_id
            api_hash = worker.api_hash
            client = TelegramClient(f'sessions/{phone}.session', api_id, api_hash)
            client.connect()
            source_group = client.get_entity(source_group_name)
            members = client.get_participants(source_group)

            grp = Group(source_group.id, self.input_source_group.toPlainText(), 0)
            self.dbWorker.insert_group(grp)
            count = 1
            for member in members:
                percent_progerss = int((count * 100) / len(members))
                self.progressBar_crawl.setValue(percent_progerss)
                user = User(user_id=member.id, access_hash=member.access_hash)
                member_in_group = MemberInGroup(group_id=source_group.id, member_id=user.user_id)
                self.dbWorker.insert_user(user)
                self.dbWorker.insert_member_in_group(member_in_group)

                count = count + 1

            # Disconnect client after being used
            client.disconnect()

            # Show pop-up to inform
            self.popup.show_popup(title='Success', msg_text="Crawl done \n Total Member : {}".format(len(members)))
            self.input_source_group.clear()
            self.progressBar_crawl.setValue(0)
            self.load_data_group()

        except Exception as e:
            if client is not None:
                client.disconnect()

            logging.exception(e)


    def update_add_mem_to_gr_pb(self, signal_list):
        percentage = signal_list[0]
        num_added_members = signal_list[1]

        self.progressBar_add_menber.setValue(percentage)
        if percentage == 100:
            target_group_name = self.target_group_add.toPlainText()
            # Step 4: Show pop-up
            self.popup.show_popup(title='Sucsses', msg_text='Added {} members to group {}'.format(num_added_members, target_group_name))
            logging.info(f'Done: Adding members to the group: {target_group_name}')
            logging.info(f'------------------------- FINISH ADDING MEMBERS TO GROUP !!! -------------------------')


    def update_add_mem_to_sc_pb(self, signal_list):
        percentage = signal_list[0]
        num_added_members = signal_list[1]

        self.progressBar_add_menber_sc.setValue(percentage)
        if percentage == 100:
            target_chan_name = self.textEdit_channel_target.toPlainText()
            # Step 4: Show pop-up
            self.popup.show_popup(title='Sucsses', msg_text='Added {} members to subchannel {}'.format(num_added_members, target_chan_name))
            logging.info(f'Done: Adding members to the subchannel: {target_chan_name}')
            logging.info(f'------------------------- FINISH ADDING MEMBERS TO SUBCHANNEL !!! -------------------------')


    def update_send_mess_pb(self, signal_list):
        percentage = signal_list[0]
        num_sent_members = signal_list[1]

        self.progressBar_send_sms.setValue(percentage)
        if percentage == 100:
            sms_text = self.input_sms.toPlainText()
            target_group_name = target_group_name = self.input_source_group_sms.text()
            # Step 4: Show pop-up
            logging.info(f'Done: send sms to  members : : {sms_text}')
            logging.info(f'target_group_name: {target_group_name}')

            # Step 4: Show pop-up
            self.popup.show_popup(title='Sucsses', msg_text='Send sms to {} users'.format(num_sent_members))
            logging.info(f'-------------------- FINISH SEND SMS !!! --------------------')


    def btn_add_member_func(self):
        """
         get source_group and target_group khi click btn add member
        :return:
        """
        try:
            logging.info(f'------------------------- START ADDING MEMBERS TO GROUP ### -------------------------')
            NUM_MEM_ADDED_PER_ACC = config.get('NUM_MEM_ADDED_PER_ACC')
            SCREEN = "ADDING MEMBERS TO GROUP"

            # Get text from UI
            source_group_name = self.source_group_add.text()
            target_group_name = self.target_group_add.toPlainText()

            # Reset threads + progress bar
            self.reset_add_member_gr_thread()
            logging.info(f'{SCREEN}: User input source = {source_group_name} -> target = {target_group_name}')

            # Step 1: Load list of member of source group from DB
            dbWorker = DBWorker()
            list_members = dbWorker.select_all_members_in_one_group(group_id=None, group_name=source_group_name)
            logging.info(f'Done: Load list of member from group: {source_group_name}')
            logging.info(f'len list members: {len(list_members)}')

            # Step 2: Get list of needed accounts + divide into batch
            list_accounts = dbWorker.select_available_add_accounts()
            logging.info(f'len list accounts: {len(list_accounts)}')

            bpro = BatchProcessor()
            list_use_accounts, dict_batch, is_lack_acc, max_mem_process = bpro.divide_into_batch(list_accounts, \
                                                                                                 list_members, \
                                                                                                 NUM_MEM_ADDED_PER_ACC)

            logging.info(f'Done: Divide batch. Max members are proceeded = {max_mem_process}')
            logging.info(f'Done: Divide batch. Max use accounts = {len(list_use_accounts)}')
            logging.info(f'Done: Divide batch. Max batch = {len(dict_batch)}')
            
            # Step 3a: Joining all of these accounts to target_group
            banned = []
            joined_error = []
            for acc in list_use_accounts:
                api_id = int(acc.api_id)
                api_hash = str(acc.api_hash)
                phone_no = str(acc.phone_no)
                clnt = TelegramClient(f'sessions\\{phone_no}', api_id, api_hash)
                clnt.connect()

                # If account is not authorized -> Remove from list
                if not clnt.is_user_authorized():
                    logging.info(f'{phone_no} is banned')
                    banned.append(acc.phone_no)
                    list_use_accounts.remove(acc)
                # If account is authorized -> Join this account to the target group
                else:
                    username = clnt.get_entity(target_group_name)
                    try:
                        clnt(JoinChannelRequest(username))
                        logging.info(f'+ Successfully joined from {phone_no}')
                    except:
                        logging.info(f'- Error in joined from {phone_no}')
                        joined_error.append(acc)
                        list_use_accounts.remove(acc)

                time.sleep(0.5)
                clnt.disconnect()

            logging.info(f'Done: Joining all accounts to the group: {target_group_name}')

            # Step 3b: Filtered batch based on list of successfully joined accounts
            banned_phone_no = set(banned)
            filtered_max_mem_process = 0
            for key, value in dict_batch.items():
                acc = value[0]
                list_mems = value[1]

                if acc.phone_no in banned_phone_no:
                    del dict_batch[key]
                else:
                    filtered_max_mem_process += len(list_mems)

            # Step 4: Start to add users to target_group
            count_lock = multiprocessing.Lock()
            count_incre = multiprocessing.Value('i', 0)
            self.list_adding_member_gr_threads = self.parallel_process_batches(source_group_name, \
                                                                                    target_group_name, \
                                                                                    list_use_accounts, \
                                                                                    dict_batch, \
                                                                                    action='ADD_MEMBERS_TO_GROUP',\
                                                                                    bpro=bpro,\
                                                                                    count_lock=count_lock,\
                                                                                    count_incre=count_incre)

            # Step 5: Adding thread to update progress_bar
            self.add_member_gr_progress_updater = ProgressUpdater(count_incre, filtered_max_mem_process)
            self.add_member_gr_progress_updater.params.connect(self.update_add_mem_to_gr_pb)
            self.add_member_gr_progress_updater.start()

            # Step 6: Binding each thread to the main thread
            for _th_ in self.list_adding_member_gr_threads:
                _th_.start()

        except Exception as e:
            logging.exception(e)


    def btn_add_to_channel(self):
        try:
            logging.info(f'------------------------- START ADDING MEMBERS TO SUBCHANNEL ### -------------------------')
            NUM_MEM_ADDED_PER_ACC = config.get('NUM_MEM_ADDED_PER_ACC')

            # Step 1: Get input value from UI
            source_group = self.lineEdit_channel_source_group.text()
            target_channel = self.textEdit_channel_target.toPlainText()
            main_phone = self.lineEdit_channel_main_phone.text()

            # Validate input value
            if source_group == '':
                self.popup.show_popup(title='ERROR', msg_text='Please enter the source group', info=False)
                return
            if target_channel == '':
                self.popup.show_popup(title='ERROR', msg_text='Please enter the target channel', info=False)
                return
            if main_phone == '':
                self.popup.show_popup(title='ERROR', msg_text='Please enter the main phone number', info=False)
                return

            # Step 2: Get list of members of source group
            list_members = self.dbWorker.select_all_members_in_one_group(group_id=None, group_name=source_group)
            logging.info(f'Done: Load list of member from group: {source_group}')
            logging.info(f'len list members: {len(list_members)}')

            # Step 3: Get list of needed accounts + divide into batch
            list_accounts = self.dbWorker.select_available_add_accounts()
            logging.info(f'len list accounts: {len(list_accounts)}')

            bpro = BatchProcessor()
            list_use_accounts, dict_batch, is_lack_acc, max_mem_process = bpro.divide_into_batch(list_accounts, \
                                                                                                 list_members, \
                                                                                                 NUM_MEM_ADDED_PER_ACC)

            logging.info(f'Done: Divide batch. Max members are proceeded = {max_mem_process}')
            logging.info(f'Done: Divide batch. Max use accounts = {len(list_use_accounts)}')
            logging.info(f'Done: Divide batch. Max batch = {len(dict_batch)}')

            # Step 4: Joining all of these accounts to target_group
            account_id_list = []
            for acc in list_use_accounts:
                api_id = int(acc.api_id)
                api_hash = str(acc.api_hash)
                phone_no = str(acc.phone_no)
                client = TelegramClient(f'sessions\\{phone_no}', int(api_id), api_hash)
                client.connect()
                banned = []
                joined_error = []
                # If account is not authorized -> Remove from list
                if not client.is_user_authorized():
                    logging.info(f'{phone_no} is banned')
                    banned.append(acc)
                    list_use_accounts.remove(acc)
                # If account is authorized -> Join this account to the target group
                else:
                    username = client.get_entity(target_channel)
                    activate_group = client.get_entity('t.me/activategroupah')
                    try:
                        client(JoinChannelRequest(username))
                        client(JoinChannelRequest(activate_group))
                        logging.info(f'+ Successfully joined from {phone_no}')
                    except:
                        logging.info(f'- Error in joined from {phone_no}')
                        joined_error.append(acc)
                        list_use_accounts.remove(acc)

                time.sleep(0.5)
                client.disconnect()
            logging.info(f'################### {len(account_id_list)} ######################')
            logging.info(f'Done: Joining all accounts to the target group: {target_channel}')

            # Step 4b: Filtered batch based on list of successfully joined accounts
            banned_phone_no = set(banned)
            filtered_max_mem_process = 0
            for key, value in dict_batch.items():
                acc = value[0]
                list_mems = value[1]

                if acc.phone_no in banned_phone_no:
                    del dict_batch[key]
                else:
                    filtered_max_mem_process += len(list_mems)

            # Step 5: Leverage admin rights for all account
            admin_acc = self.dbWorker.select_account(main_phone)
            api_id = admin_acc.api_id
            api_hash = admin_acc.api_hash
            admin_client = TelegramClient(f'sessions/{main_phone}', api_id, api_hash)
            admin_client.connect()
            members = admin_client.get_participants('t.me/activategroupah')
            for acc in members:
                try:
                    # worker_acc = admin_client.get_entity(id)
                    worker_acc = admin_client.get_entity(PeerUser(acc.id))
                    # target_channel_entity = admin_client.get_entity(target_channel)
                    admin_client(EditAdminRequest(channel=target_channel, user_id=acc.id,
                                                  admin_rights=self.admin_rights, rank='admin'))
                    logging.info(f'+++ Edit Admin rights successfully')
                except TypeError as eee:
                    logging.exception(eee)
                    logging.info(admin_client.get_me().id)
                    logging.info(acc['id'])
                except ValueError as e:
                    logging.exception(e)
                    logging.info(type(acc['id']))
                    logging.info(acc['id'])
                except UserCreatorError as user_creator_error:
                    logging.info('Unknown Error')
                    logging.exception(user_creator_error)
            admin_client.disconnect()
            logging.info("============DONE LEVERAGING ADMIN RIGHTS===================")
            # Step 5: Start to add users to target_group
            count_lock = multiprocessing.Lock()
            count_incre = multiprocessing.Value('i', 0)
            self.list_adding_member_sc_threads = self.parallel_process_batches(source_group, \
                                                                                    target_channel, \
                                                                                    list_use_accounts, \
                                                                                    dict_batch, \
                                                                                    action='ADD_MEMBERS_TO_GROUP',\
                                                                                    bpro=bpro,\
                                                                                    count_lock=count_lock,\
                                                                                    count_incre=count_incre)

            # # Step 6: Adding thread to update progress_bar
            self.add_member_sc_progress_updater = ProgressUpdater(count_incre, filtered_max_mem_process)
            self.add_member_sc_progress_updater.params.connect(self.update_add_mem_to_sc_pb)
            self.add_member_sc_progress_updater.start()

            # Step 7: Binding each thread to the main thread
            for _th_ in self.list_adding_member_sc_threads:
                _th_.start()


        except Exception as e:
            logging.exception(e)

    def btn_send_mes(self):
        """
        get source group
        :return:
        """
        try:
            logging.info(f'------------------------- START SENDING MESSAGE TO MEMBERS OF GROUP ### -------------------------')
            # Get value from UI
            sms_text = self.input_sms.toPlainText()
            target_group_name = self.input_source_group_sms.text()


            # Validate input text
            if sms_text == '':
                self.popup.show_popup(title='ERROS', msg_text='SMS cannot blank', info=False)

            elif target_group_name == "":
                self.custommessagebox.showWithTimeout(20, "Auto close in 3 seconds", "QMessageBox with autoclose", icon=QMessageBox.Warning)
                # self.popup.show_popup(title='ERROS', msg_text='Source Group cannot blank', info=False)
            else:
                NUM_MEM_SEND_PER_ACC = config.get('NUM_MEM_SEND_PER_ACC')

                # Step 1: Select list of members from one group
                dbWorker = DBWorker()
                list_members = dbWorker.select_all_members_in_one_group(group_id=None, group_name=target_group_name)
                logging.info(f'list members need being proceeded {len(list_members)}')

                # Step 2: Get list of needed accounts + divide into batch
                list_accounts = dbWorker.select_available_send_accounts()

                bpro = BatchProcessor()
                list_use_accounts, dict_batch, is_lack_acc, max_mem_process = bpro.divide_into_batch(list_accounts, \
                                                                                                     list_members, \
                                                                                                     NUM_MEM_SEND_PER_ACC)

                logging.info(f'-------- len dict batch: {len(dict_batch)}')
                # Step 3: Send messages parallelly
                count_lock = multiprocessing.Lock()
                count_incre = multiprocessing.Value('i', 0)
                self.list_sending_message_threads = self.parallel_process_batches(target_group_name = target_group_name, \
                                                                                text_msg=sms_text, \
                                                                                dict_batch=dict_batch, \
                                                                                action='SEND_MESSAGE_ALL_MEMBERS',\
                                                                                bpro=bpro,\
                                                                                count_lock=count_lock,\
                                                                                count_incre=count_incre)

                # Step 4: Adding thread to update progress_bar
                self.send_message_progress_updater = ProgressUpdater(count_incre, max_mem_process)
                self.send_message_progress_updater.params.connect(self.update_send_mess_pb)
                self.send_message_progress_updater.start()

                # Step 5: Start threads
                for _th_ in self.list_sending_message_threads:
                    _th_.start()

        except Exception as e:
            logging.exception(e)


    def parallel_process_batches(self, source_group_name=None, target_group_name=None, list_filtered_accounts=None, \
                                        dict_batch=None, text_msg=None, action=None, bpro=None, count_lock=None, count_incre=None):
        '''
        This function is used to add members to groups/ or send message for multiple batches of memebers parallely
        The account which is used to add member/send message has been divided by BatchProcessor
        Input:
            - source_group_name                     String          Name of the source group
            - target_group_name                     String          Name of the target group
            - list_filtered_accounts:               List            List of filtered accounts.
                                                                    These accounts are not banned + add to target group successfully
            - dict_batch:                           Dict            Dict of batch in format
                                                                        key: index: 0,1,2,...
                                                                        value: Tuple 2 elements (Account, List<User>)
            - text_msg                              String          Message to send
            - action                                String          Action that user want to do paralelly
                                                                        - Action 1: ADD_MEMBERS_TO_GROUP
                                                                        - Action 2: SEND_MESSAGE_ALL_MEMBERS
            - bpro                                  BatchProcessor  BatchProcessor object
        '''
        list_threads = []
        try:
            for key in dict_batch:
                batch = dict_batch.get(key)

                add_thread = multiprocessing.Process(target=bpro.go, args=(source_group_name, \
                                                                    target_group_name, \
                                                                    batch, \
                                                                    f"Thread_{action}_batch_{key}",\
                                                                    text_msg, \
                                                                    action, \
                                                                    count_lock,\
                                                                    count_incre))
                list_threads.append(add_thread)


        except Exception as e:
            logging.exception(e)

        return list_threads


    def reset_add_member_gr_thread(self):
        # Terminating all adding members to group threads
        logging.info(f'------------- Start resetting thread adding member to group --------------')
        for t_idx, _th_ in enumerate(self.list_adding_member_gr_threads):
            logging.info(f'resetting thread adding member {t_idx}: {_th_}')
            _th_.terminate()
        logging.info(f'------------- Finish resetting thread adding member to group --------------')
        logging.info(f'------------- Start resetting thread updatting progress bar of adding member to group --------------')
        if self.add_member_gr_progress_updater is not None:
            self.add_member_gr_progress_updater.exit()
        self.progressBar_add_menber.setValue(0)

        logging.info(f'------------- Finish resetting thread updatting progress bar of adding member to group --------------')


    def terminate_add_member_gr_thread(self):
        # Terminating all adding members to group threads
        logging.info(f'------------- Start terminating thread adding member to group --------------')
        for t_idx, _th_ in enumerate(self.list_adding_member_gr_threads):
            logging.info(f'Terminating thread adding member {t_idx}: {_th_}')
            _th_.terminate()
        logging.info(f'------------- Finish terminating thread adding member to group --------------')
        logging.info(f'------------- Start terminating thread updatting progress bar of adding member to group --------------')
        if self.add_member_gr_progress_updater is not None:
            self.add_member_gr_progress_updater.exit()
        self.progressBar_add_menber.setValue(0)

        logging.info(f'------------- Finish terminating thread updatting progress bar of adding member to group --------------')
        target_group_name = self.target_group_add.toPlainText()
        logging.info(f'Cancelled: Adding members to the group: {target_group_name}')
        logging.info(f'------------------------- FINISH ADDING MEMBERS TO GROUP !!! -------------------------')


    def reset_add_member_sc_thread(self):
        # Terminating all adding members to subchannel threads
        logging.info(f'------------- Start resetting thread adding member to subchannel --------------')
        for t_idx, _th_ in enumerate(self.list_adding_member_sc_threads):
            logging.info(f'resetting thread adding member {t_idx}: {_th_}')
            _th_.terminate()
        logging.info(f'------------- Finish resetting thread adding member to subchannel --------------')
        logging.info(f'------------- Start resetting thread updatting progress bar of adding member to subchannel --------------')
        if self.add_member_sc_progress_updater is not None:
            self.add_member_sc_progress_updater.exit()
        self.progressBar_add_menber_sc.setValue(0)

        logging.info(f'------------- Finish resetting thread updatting progress bar of adding member to subchannel --------------')


    def terminate_add_member_sc_thread(self):
        # Terminating all adding members to group threads
        logging.info(f'------------- Start terminating thread adding member to subchannel --------------')
        for t_idx, _th_ in enumerate(self.list_adding_member_sc_threads):
            logging.info(f'Terminating thread adding member {t_idx}: {_th_}')
            _th_.terminate()
        logging.info(f'------------- Finish terminating thread adding member to subchannel --------------')
        logging.info(f'------------- Start terminating thread updatting progress bar of adding member to subchannel --------------')
        if self.add_member_sc_progress_updater is not None:
            self.add_member_sc_progress_updater.exit()
        self.progressBar_add_menber_sc.setValue(0)

        logging.info(f'------------- Finish terminating thread updatting progress bar of adding member to subchannel --------------')
        target_chan_name = self.textEdit_channel_target.toPlainText()
        logging.info(f'Cancelled: Adding members to the subchannel: {target_chan_name}')
        logging.info(f'------------------------- FINISH ADDING MEMBERS TO SUBCHANNEL !!! -------------------------')


    def reset_sending_message_thread(self):
        # Terminating all sending messsage threads
        logging.info(f'------------- Start resetting thread sending message --------------')
        for t_idx, _th_ in enumerate(self.list_sending_message_threads):
            logging.info(f'resetting thread sending message {t_idx}: {_th_}')
            _th_.terminate()
        logging.info(f'------------- Finish resetting thread sending message --------------')
        logging.info(f'------------- Start resetting thread updatting progress bar of sending message --------------')
        if self.send_message_progress_updater is not None:
            self.send_message_progress_updater.exit()
        self.progressBar_send_sms.setValue(0)

        logging.info(f'------------- Finish resetting thread updatting progress bar of sending message --------------')


    def terminate_sending_message_thread(self):
        # Terminating all sending message threads
        logging.info(f'------------- Start terminating thread sending message --------------')
        for t_idx, _th_ in enumerate(self.list_sending_message_threads):
            logging.info(f'Terminating thread sending message {t_idx}: {_th_}')
            _th_.terminate()
        logging.info(f'------------- Finish terminating thread sending message --------------')
        logging.info(f'------------- Start terminating thread updatting progress bar of sending message --------------')
        if self.send_message_progress_updater is not None:
            self.send_message_progress_updater.exit()
        self.progressBar_send_sms.setValue(0)

        logging.info(f'------------- Finish terminating thread updatting progress bar of sending message --------------')
        target_group_name = self.input_source_group_sms.text()
        logging.info(f'Cancelled: Sending message: {target_group_name}')
        logging.info(f'------------------------- FINISH SENDING MESSAGE !!! -------------------------')


    def load_data_phone_list(self):
        """
        hiển thị data lên trên view phone
        :return:
        """
        acc_list = self.dbWorker.select_all_accounts()
        row = 0
        self.tableWidget.setRowCount(len(acc_list))
        for acc in acc_list:
            self.tableWidget.setItem(row, 0, QtWidgets.QTableWidgetItem(str(acc.phone_no)))
            self.tableWidget.setItem(row, 1, QtWidgets.QTableWidgetItem(str(acc.authenticated_datetime)))
            row = row + 1


    def load_data_group(self):
        """
        hiển thị data group lên trên view
        :return:
        """
        group_list = self.dbWorker.select_all_groups()
        row = 0
        self.tableWidget_group.setRowCount(len(group_list))
        for group in group_list:
            members = self.dbWorker.select_all_members_in_one_group(group.group_id)
            self.tableWidget_group.setItem(row, 0, QtWidgets.QTableWidgetItem(str(group.group_name)))
            self.tableWidget_group.setItem(row, 1, QtWidgets.QTableWidgetItem(str(len(members))))
            row = row + 1


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    mainwindown = Mainprogram()
    mainwindown.show()
    # mainwindown.show()
    sys.exit(app.exec_())
