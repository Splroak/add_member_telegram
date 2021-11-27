import os
import sys
import datetime

class Group:
    def __init__(self, group_id, group_name, group_type):
        '''
        Input:
            group_id        String      ID of group
            group_name      String      Group name
            group_type      int         0: Public. 1: Private
        '''
        self.group_id = group_id
        self.group_name = group_name
        self.group_type = group_type
        
        
    def __str__(self) -> str:
        object_str = self.group_id + ', ' + self.group_name + ', ' + str(self.group_type)
        return object_str


    