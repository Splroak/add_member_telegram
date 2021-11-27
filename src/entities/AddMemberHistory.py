import os
import sys
import datetime

class AddMemberHistory:
    def __init__(self, acc, member, target_group, add_status, added_datetime, _id_=None):
        '''
        Input:
            acc                         Account         Account that system use to add member
            member                      Member          Member that is added to group
            target_group                Group           The group to which you want to add member                   
            added_datetime              datetime        The datetime when this member is added 
                                                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        '''
        self.phone_no = acc.phone_no
        self.member_id = member.user_id
        self.target_group_id = target_group.group_id
        self.add_status = add_status
        self.added_datetime = added_datetime
        self._id_ = _id_

    def get_id(self):
        '''
        This function is used to return the id of this AddMemberHistory object
        incase it is fetched from Database
        '''
        return self._id_
        
        
    def __str__(self) -> str:
        object_str = ''
        if self._id_ != None and self._id_ != '':
            object_str = self._id_ + ', ' + self.phone_no + ', ' + self.member_id + ', ' \
                                    + self.target_group_id + ', ' + str(self.add_status) + ', ' + str(self.authenticated_datetime)
        else:
            object_str = self.phone_no + ', ' + self.member_id + ', ' + self.target_group_id + ', ' + str(self.add_status) + ', ' + str(self.authenticated_datetime)
            
        return object_str