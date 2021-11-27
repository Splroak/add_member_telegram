import os
import sys
import datetime

class CrawlGroupHistory:
    def __init__(self, acc, source_group, crawled_datetime, _id_=None):
        '''
        Input:
            acc                         Account         Account that system use to add member
            source_group                Group           The group to which you crawled
            crawled_datetime            datetime        The datetime when this group is crawled 
                                                        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        '''
        self.phone_no = acc.phone_no
        self.source_group_id = source_group.group_id
        self.crawled_datetime = crawled_datetime
        self._id_ = None
    
    def get_id(self):
        '''
        This function is used to return the id of this CrawlGroupHistory object
        incase it is fetched from Database
        '''
        return self._id_
        

    def __str__(self) -> str:
        object_str = ''
        if self._id_ != '' or self._id_ is not None:
            object_str = self._id_ + ', ' + self.phone_no + ', ' + self.source_group_id + ', ' + str(self.crawled_datetime)
        else:
            object_str = self.phone_no + ', ' + self.source_group_id + ', ' + str(self.crawled_datetime)
        return object_str