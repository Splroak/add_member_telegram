import os
import sys
import datetime

class MemberInGroup:
    def __init__(self, member_id, group_id, id=None):
        '''
        Input:
            member_id                   String          Id of the member
            group_id                    String          Id of group
            id                          String          Id of this object in database. Default, this id is None.
                                                        It only has value when being fetched from database
        '''
        self.member_id = member_id
        self.group_id = group_id
        self.id = id


    def get_id(self):
        '''
        This function is used to return the id of this MemberInGroup object
        incase it is fetched from Database
        '''
        return self.id
        

    def __str__(self) -> str:
        object_str = self.user_id + ', ' + self.access_hash
        return object_str


    