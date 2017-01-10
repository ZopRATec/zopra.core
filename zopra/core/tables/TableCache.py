###########################################################################
#    Copyright (C) 2005 by by ZopRATec GbR                                #
#    <webmaster@ingo-keller.de>                                           #
# Copyright: See COPYING file that comes with this distribution           #
#                                                                         #
###########################################################################
# TODO: use BTree as Cache to speed up pickle and unpickle
from types          import ListType
from OFS.SimpleItem import SimpleItem


class TableCache(SimpleItem):
    """\brief Table Cache

    The TableCache provides 3 different caching mechanisms:
        -ALLIST: complete tablecache for tables used as lists (key=columnlist)
        -IDLIST: entry-listcache for entrylists (key=query)
        -ITEM:   itemcache for single entries (key=autoid) .
    """

    _className = 'ZMOMTableCache'
    _classType = [_className]

    # action
    INSERT  = 1
    UPDATE  = 2
    DELETE  = 3

    # cache type
    ITEM    = 4
    IDLIST  = 5
    ALLLIST = 6
    ALL     = 7

    item_count    = 200
    idlist_count  = 10
    alllist_count = 3

#
# Instance Methods
#

    def __init__(self):
        """\brief Constructs a TableCache."""
        self.item          = {}
        self.idlist        = {}
        self.alllist       = {}
        self.item_order    = []
        self.idlist_order  = []
        self.alllist_order = []


    def invalidate(self, autoid = None):
        """\brief Cleares the cache.
           \param autoid Only removes the item with this
                  autoid from item-cache
        """
        self.clearCache(self.IDLIST)
        self.clearCache(self.ALLLIST)
        self.delItem(autoid)


    def delItem(self, autoid):
        """\brief Remove one item from the item-cache.
           \param autoid The autoid of the item to remove
        """
        if autoid is not None and self.item.get(int(autoid)):
            del self.item[int(autoid)]
            self.item_order.remove(int(autoid))
            self.make_persistent()


    def clearCache(self, cachetype = ALL):
        """\brief removes the complete cache."""
        if cachetype == self.ALL:
            self.item          = {}
            self.idlist        = {}
            self.alllist       = {}
            self.item_order    = []
            self.idlist_order  = []
            self.alllist_order = []

        elif cachetype == self.ITEM:
            self.item    = {}
            self.item_order    = []

        elif cachetype == self.IDLIST:
            self.idlist  = {}
            self.idlist_order  = []

        elif cachetype == self.ALLLIST:
            self.alllist = {}
            self.alllist_order = []

        # me hate persistance
        self.make_persistent()


    def getItem(self, cachetype, key):
        """ Returns a cached item if available from the chosen cache.

        @param cachetype - int flag for cache type
        @param key       - key for the cached item
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
        """\brief Insert an item into cache."""
        assert cachetype in [self.ITEM, self.IDLIST, self.ALLLIST]
        assert key is not None

        if cachetype == self.ITEM:
            key   = int(key)
            cache = self.item
            order = self.item_order
            count = self.item_count

        elif cachetype == self.IDLIST:
            cache = self.idlist
            order = self.idlist_order
            count = self.idlist_count

        elif cachetype == self.ALLLIST:
            assert isinstance(key, ListType)
            key   = str(key)
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
        """\brief Zope persistence needs to be activated... ugly style."""
        self.getParentNode().cache = self
