from Persistence    import Persistent

from persistent.list import PersistentList
from persistent.dict import PersistentDict



class PersistentCache(Persistent):


    def __init__(self, size = 10):
        self.dict = PersistentDict()
        self.list = PersistentList()
        self.size = int(size)


    def has(self, key):
        return key in self.dict


    def get(self, obj, _type = None):
        return self.dict.get(obj, _type)


    def set(self, obj, value):
        # remove last item if cache is full
        if len(self.list) == self.size:
            key = self.list.pop()
            del self.dict[key]

        self.dict[obj] = value
        self.list.insert(0, obj)


    def remove(self, obj):
        print 'del', obj
        if obj in self.dict:
            del self.dict[obj]
            self.list.remove(obj)


    def getOrderedItems(self):
        return [self.dict[key] for key in self.list]

    def getOrderedKeys(self):
        return [key for key in self.list]
