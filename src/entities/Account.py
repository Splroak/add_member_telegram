import os
import sys
import datetime

class Account:
    def __init__(self, phone_no, api_id, api_hash, authenticated_datetime, total_used_1D=0):
        '''
        Input:
            phone_no                    String          Phone number
            api_id                      String          API_ID used to login for this phone_no
            api_hash                    String          API_HASH used to login for this phone_no
            authenticated_datetime      datetime        Latest datetime when this phone_no is authenticated 
                                                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
        '''
        self.phone_no = phone_no
        self.api_id = api_id
        self.api_hash = api_hash
        self.authenticated_datetime = authenticated_datetime
        self.total_used_1D = total_used_1D

    def __str__(self) -> str:
        return self.phone_no + ', ' + self.api_id + ', ' + self.api_hash + ', ' + str(self.authenticated_datetime) + ', ' + str(self.total_used_1D)