# TODO: use RAMCache to loose the write operations
from zopra.core import SimpleItem
from zopra.core.types import ListType


# soft plone dependency, use plone.protect if it is available
try:
    from plone.protect.utils import safeWrite
except ImportError:
    def safeWrite(obj, request=None):
        pass


class TableCache(SimpleItem):
    """Table Cache

    The TableCache provides 3 different caching mechanisms:
        -ALLIST: complete tablecache for tables used as lists (key=columnlist)
        -IDLIST: entry-listcache for entrylists (key=query)
        -ITEM:   itemcache for single entries (key=autoid) .
    """

    _className = "ZMOMTableCache"
    _classType = [_className]

    # action
    INSERT = 1
    UPDATE = 2
    DELETE = 3

    # cache type
    ITEM = 4
    IDLIST = 5
    ALLLIST = 6
    ALL = 7

    item_count = 200
    idlist_count = 10
    alllist_count = 3

    #
    # Instance Methods
    #

    def __init__(self):
        """Constructs a TableCache."""
        self.item = {}
        self.idlist = {}
        self.alllist = {}
        self.item_order = []
        self.idlist_order = []
        self.alllist_order = []

    def invalidate(self, autoid=None):
        """Cleares the cache.
        :param autoid: Additionally remove the item with this autoid from item-cache.
        """
        self.clearCache(self.IDLIST)
        self.clearCache(self.ALLLIST)
        self.delItem(autoid)

    def delItem(self, autoid):
        """Remove one item from the item-cache.
        :param autoid: The autoid of the item to remove
        """
        if autoid is not None and self.item.get(int(autoid)):
            safeWrite(self)
            safeWrite(self.item)
            safeWrite(self.item_order)
            del self.item[int(autoid)]
            self.item_order.remove(int(autoid))
            self.make_persistent()

    def clearCache(self, cachetype=ALL):
        """removes the complete cache."""
        if cachetype == self.ALL:
            self.item = {}
            self.idlist = {}
            self.alllist = {}
            self.item_order = []
            self.idlist_order = []
            self.alllist_order = []

        elif cachetype == self.ITEM:
            self.item = {}
            self.item_order = []

        elif cachetype == self.IDLIST:
            self.idlist = {}
            self.idlist_order = []

        elif cachetype == self.ALLLIST:
            self.alllist = {}
            self.alllist_order = []

        # me hate persistance
        self.make_persistent()

    def getItem(self, cachetype, key):
        """Returns a cached item if available from the chosen cache.

        :param cachetype: int flag for cache type
        :param key: key for the cached item
        """
        assert cachetype in [self.ITEM, self.IDLIST, self.ALLLIST]
        assert key is not None

        if cachetype == self.ITEM:
            return self.item.get(int(key))

        elif cachetype == self.IDLIST:
            return self.idlist.get(key)

        elif cachetype == self.ALLLIST:
            assert isinstance(key, ListType)
            return self.alllist.get(str(key))

    def insertItem(self, cachetype, key, value):
        """Insert an item into cache."""
        assert cachetype in [self.ITEM, self.IDLIST, self.ALLLIST]
        assert key is not None

        if cachetype == self.ITEM:
            key = int(key)
            cache = self.item
            order = self.item_order
            count = self.item_count

        elif cachetype == self.IDLIST:
            cache = self.idlist
            order = self.idlist_order
            count = self.idlist_count

        elif cachetype == self.ALLLIST:
            assert isinstance(key, ListType)
            key = str(key)
            cache = self.alllist
            order = self.alllist_order
            count = self.alllist_count

        if key not in cache:
            cache[key] = value
            order.append(key)
            if len(order) > count:
                tmpkey = order.pop(0)
                del cache[tmpkey]

            # persistence
            self.make_persistent()

    def make_persistent(self):
        """Zope persistence needs to be activated."""

        parent = self.getParentNode()
        parent.cache = self
        # all writing methods call make_persistent, so we use it to tell plone.protect that write operations are okay
        safeWrite(parent)
        safeWrite(parent.cache)
        safeWrite(self)
        safeWrite(self.item)
        safeWrite(self.idlist)
        safeWrite(self.alllist)
        safeWrite(self.item_order)
        safeWrite(self.idlist_order)
        safeWrite(self.alllist_order)
