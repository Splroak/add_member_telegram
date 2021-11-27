import os
import sys
import datetime

class SendMessageHistory:
    def __init__(self, acc, member, group, message, sent_datetime, _id_ = None):
        '''
        Input:
            acc                         Account         Account that system use to send message
            member                      Member          Member that is receives message
            group                       Group           The group whose all members receive your message
            message                     String          The message you want to send to all members
            sent_datetime               datetime        The datetime when you send message 
                                                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        '''
        self.phone_no = acc.phone_no
        self.member_id = member.user_id
        self.group_id = group.group_id
        self.message = message
        self.sent_datetime = sent_datetime
        self._id_ = _id_


    def get_id(self):
        '''
        This function is used to return the id of this Group object
        incase it is fetched from Database
        '''
        return self._id_
        
        
    def __str__(self) -> str:
        object_str = ''
        if object_str is not None or object_str != '':
            object_str = self._id_ + ', ' + self.phone_no + ', ' + self.member_id + ', ' + self.group_id + ', ' + self.message + ', ' + str(self.sent_datetime)
        else:
            object_str = self.phone_no + ', ' + self.member_id + ', ' + self.group_id + ', ' + self.message + ', ' + str(self.sent_datetime)
        return object_str