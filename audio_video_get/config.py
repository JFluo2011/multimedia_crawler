# mongodb
MONGODB_SERVER = 'localhost'
MONGODB_PORT = 27017
MONGODB_DB = 'TestDB'
MONGODB_COLLECTION = 'TestCollection'

try:
    from local_config import *
except:
    pass
