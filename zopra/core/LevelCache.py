###########################################################################
#    Copyright (C) 2005 by by ZopRATec GbR                                #
#    <webmaster@ingo-keller.de>                                           #
# Copyright: See COPYING file that comes with this distribution           #
#                                                                         #
###########################################################################
from zopra.core import SimpleItem


ORDER = '$_order'


class LevelCache(SimpleItem):
    """\brief Level Cache

    The Level Cache is a generic hierarchical cache using lists of keys.
    """

    _className = 'LevelCache'
    _classType = [_className]

    # action
    INSERT  = 1
    UPDATE  = 2
    DELETE  = 3

#
# Instance Methods
#

    def __init__(self, levels = 1, counts = [200], name = 'cache', nonpersistent = False):
        """\brief Constructs a LevelCache with <levels> number of
                  levels.
           \param levels The number of levels in this cache.
           \param name The variable name of this cache in the
                  containing object (for persistence)
           \param counts The maximum number of entries per cache level as a
                  list, for levels > 1, the size is counted extra
                  for each cache dict."""
        self.levels = levels
        self.counts = counts
        self.name   = name
        self.items  = {ORDER: []}
        self.forcepersistence = not nonpersistent


    def invalidateLevel(self, level, key):
        """\brief Cleares the cache.
           \param level Only removes the items with the given key
                  in this level, counting from 0.
        """
        # go through tree, find all items in level, remove key
        caches = []
        self.findCache(self.items, 0, level, caches)
        for cache in caches:
            # remove key
            if key in cache:
                del cache[key]

        if self.forcepersistence:
            # me hate persistence
            self.makePersistent()


    def findCache(self, cache, level, targetlevel, result):
        if level != targetlevel:
            for sub in cache.values():
                self.findCache(sub, level + 1, targetlevel, result)
        else:
            result.append(cache)


    def invalidateItem(self, keys):
        """\brief Cleares the cache.
           \param level Only removes the items with the given key
                  in this level, counting from 0.
        """
        assert len(keys) == self.levels
        # go through tree, find keys
        cache = self.items
        for key in keys[:-1]:
            if key in cache:
                cache = cache[key]
            else:
                return False
        if keys[-1] in cache:
            del cache[keys[-1]]

        if self.forcepersistence:
            # me hate persistence
            self.makePersistent()


    def invalidate(self):
        """\brief Cleares the cache."""
        # clear cache completely
        self.items  = {ORDER: []}

        if self.forcepersistence:
            # me hate persistence
            self.makePersistent()


    def get(self, keys):
        """\brief Return a cached item if available."""

        assert len(keys) == self.levels

        cache  = self.items
        for key in keys:
            if key in cache:
                cache = cache[key]
            else:
                return
        return cache


    def insert(self, keys, value):
        """\brief Insert an item into cache."""
        assert len(keys) == self.levels

        cache = self.items

        for level, key in enumerate(keys[:-1]):
            if key not in cache:
                new_cache = {ORDER: []}
                cache[key] = new_cache
                order = cache[ORDER]
                order.append(key)
                # check count
                if len(order) > self.counts[level]:
                    tmpkey = order.pop(0)
                    # remove
                    del cache[tmpkey]
                cache = new_cache
            else:
                cache = cache[key]

        # done, set value
        key = keys[-1]
        if key not in cache:
            # set value
            cache[key] = value
            order = cache[ORDER]
            order.append(key)
            # check count
            if len(order) > self.counts[self.levels - 1]:
                tmpkey = order.pop(0)
                # remove
                del cache[tmpkey]
        else:
            # set new value, do not change order
            cache[key] = value

        if self.forcepersistence:
            # me hate persistence
            self.makePersistent()


    def makePersistent(self):
        """\brief Zope persistence needs to be activated... ugly style."""
        if self.name:
            # this is the only reason to have simpleitem as superclass
            setattr(self.getParentNode(), self.name, self)
