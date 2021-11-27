class Worker(object):
    def __init__(self, phone):
        self.phone = phone
        self.status = 'Healthy'
        
    def set_status(self,status):
        self.status = status
