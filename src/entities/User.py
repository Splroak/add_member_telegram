import os
import sys
import datetime

class User:
    def __init__(self, user_id, access_hash):
        '''
        Input:
            user_id         String      ID of each user got from Telegram API
            access_hash     String      Access hash for each user
        '''
        self.user_id = user_id
        self.access_hash = access_hash


    def __str__(self) -> str:
        object_str = self.user_id + ', ' + self.access_hash
        return object_str