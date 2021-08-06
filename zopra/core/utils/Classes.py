"""handles the xml-definition import"""

from time import strftime
from xml.sax.handler import ContentHandler

from builtins import object

from zopra.core.ImageProperties import ImageProperties


if __debug__:
    # import types for asserts
    from zopra.core.types import StringType, UnicodeType


class Columnlist(object):
    """Container for Columns"""

    __classname__ = "Columnlist"

    def __init__(self):
        self.collist = None

    def getList(self):
        return self.collist

    def setList(self, collist):
        # FIXME no type check for 'list' available.
        self.collist = collist

    def storeXML(self, ioHandle, level=0):

        # keeps track of tab level depth
        tab = ""
        tab += "".join(([" "] * level * 4))

        # start generating xml
        tmp_string = []
        if level == 0:
            ioHandle.write('<?xml version="1.0"?>\n')
            ioHandle.write("<!-- Creation date: %s -->\n" % strftime("%d.%m.%Y"))
        tmp_string.append(tab + "<Columnlist")
        if self.collist:
            tmp_string.append(' list="%s"' % self.collist)
        tmp_string.append("/>")
        ioHandle.write("".join(tmp_string) + "\n")


class Column(object):
    __classname__ = "Column"

    def __init__(self, name, coltype):
        # no type check for 'key' available.
        self.name = name
        assert isinstance(coltype, UnicodeType) or isinstance(coltype, StringType)
        self.coltype = coltype
        self.label = u" "
        self.default = None
        self.notnull = False
        self.autoinc = False
        self.manager = None
        self.function = None
        self.noedit = None
        self.invisible = None
        self.notes = None
        self.noteslabel = None
        self.noconnect = None
        self.labelsearch = None
        self.map = None

    def getName(self):
        return self.name

    def setName(self, name):
        # no type check for 'key' available.
        self.name = name

    def getType(self):
        return self.coltype

    def setType(self, coltype):
        assert isinstance(coltype, UnicodeType) or isinstance(coltype, StringType)
        self.coltype = coltype

    def getLabel(self):
        return self.label

    def setLabel(self, label=u" "):
        assert isinstance(label, UnicodeType) or isinstance(label, StringType)
        self.label = label

    def getDefault(self):
        return self.default

    def setDefault(self, default):
        assert isinstance(default, UnicodeType) or isinstance(default, StringType)
        self.default = default

    def getNotnull(self):
        return self.notnull

    def setNotnull(self, notnull=False):
        # no type check for 'boolean' available.
        self.notnull = notnull

    def getAutoinc(self):
        return self.autoinc

    def setAutoinc(self, autoinc=False):
        # no type check for 'boolean' available.
        self.autoinc = autoinc

    def getManager(self):
        return self.manager

    def setManager(self, manager):
        assert isinstance(manager, UnicodeType) or isinstance(manager, StringType)
        self.manager = manager

    def getFunction(self):
        return self.function

    def setFunction(self, function):
        assert isinstance(function, UnicodeType) or isinstance(function, StringType)
        self.function = function

    def getInvisible(self):
        return self.invisible

    def setInvisible(self, invisible):
        assert isinstance(invisible, UnicodeType) or isinstance(invisible, StringType)
        self.invisible = invisible

    def getNotes(self):
        return self.notes

    def setNotes(self, notes):
        assert isinstance(notes, UnicodeType) or isinstance(notes, StringType)
        self.notes = notes

    def getNoteslabel(self):
        return self.noteslabel

    def setNoteslabel(self, noteslabel):
        assert isinstance(noteslabel, UnicodeType) or isinstance(noteslabel, StringType)
        self.noteslabel = noteslabel

    def getNoconnect(self):
        return self.noconnect

    def setNoconnect(self, noconnect):
        assert isinstance(noconnect, UnicodeType) or isinstance(noconnect, StringType)
        self.noconnect = noconnect

    def getLabelsearch(self):
        return self.labelsearch

    def setLabelsearch(self, labelsearch):
        assert isinstance(labelsearch, UnicodeType) or isinstance(
            labelsearch, StringType
        )
        self.labelsearch = labelsearch

    def getMap(self):
        return self.map

    def setMap(self, map):
        assert isinstance(map, UnicodeType) or isinstance(map, StringType)
        self.map = map

    def storeXML(self, ioHandle, level=0):

        # keeps track of tab level depth
        tab = ""
        tab += "".join(([" "] * level * 4))

        # start generating xml
        tmp_string = []
        if level == 0:
            ioHandle.write('<?xml version="1.0"?>\n')
            ioHandle.write("<!-- Creation date: %s -->\n" % strftime("%d.%m.%Y"))
        tmp_string.append(tab + "<Column")
        if self.name:
            tmp_string.append(' name="%s"' % self.name)
        if self.coltype:
            tmp_string.append(' type="%s"' % self.coltype)
        if self.label:
            tmp_string.append(' label="%s"' % self.label)
        if self.default:
            tmp_string.append(' default="%s"' % self.default)
        if self.notnull:
            tmp_string.append(' notnull="%s"' % self.notnull)
        if self.autoinc:
            tmp_string.append(' autoinc="%s"' % self.autoinc)
        if self.manager:
            tmp_string.append(' manager="%s"' % self.manager)
        if self.function:
            tmp_string.append(' function="%s"' % self.function)
        if self.noedit:
            tmp_string.append(' noedit="%s"' % self.noedit)
        if self.invisible:
            tmp_string.append(' invisible="%s"' % self.invisible)
        if self.notes:
            tmp_string.append(' notes="%s"' % self.notes)
        if self.noteslabel:
            tmp_string.append(' noteslabel="%s"' % self.noteslabel)
        if self.noconnect:
            tmp_string.append(' noconnect="%s"' % self.noconnect)
        if self.labelsearch:
            tmp_string.append(' labelsearch="%s"' % self.labelsearch)
        if self.map:
            tmp_string.append(' map="%s"' % self.map)
        tmp_string.append("/>")
        ioHandle.write("".join(tmp_string) + "\n")


class List(object):
    __classname__ = "List"

    def __init__(self, name):
        # no type check for 'key' available.
        self.name = name

        self.label = u" "
        self.noedit = None
        self.invisible = None
        self.docache = None
        self.translations = None

    def getName(self):
        return self.name

    def setName(self, name):
        # no type check for 'key' available.
        self.name = name

    def getLabel(self):
        return self.label

    def setLabel(self, label=u" "):
        assert isinstance(label, UnicodeType) or isinstance(label, StringType)
        self.label = label

    def getNoedit(self):
        return self.noedit

    def setNoedit(self, noedit):
        assert isinstance(noedit, UnicodeType) or isinstance(noedit, StringType)
        self.noedit = noedit

    def getInvisible(self):
        return self.invisible

    def setInvisible(self, invisible):
        assert isinstance(invisible, UnicodeType) or isinstance(invisible, StringType)
        self.invisible = invisible

    def getDocache(self):
        return self.docache

    def setDocache(self, docache):
        assert isinstance(docache, UnicodeType) or isinstance(docache, StringType)
        self.docache = docache

    def getTranslations(self):
        return self.translations

    def setTranslations(self, translations):
        assert isinstance(translations, UnicodeType) or isinstance(
            translations, StringType
        )
        self.translations = translations

    def storeXML(self, ioHandle, level=0):

        # keeps track of tab level depth
        tab = ""
        tab += "".join(([" "] * level * 4))

        # start generating xml
        tmp_string = []
        if level == 0:
            ioHandle.write('<?xml version="1.0"?>\n')
            ioHandle.write("<!-- Creation date: %s -->\n" % strftime("%d.%m.%Y"))
        tmp_string.append(tab + "<List")
        if self.name:
            tmp_string.append(' name="%s"' % self.name)
        if self.label:
            tmp_string.append(' label="%s"' % self.label)
        if self.noedit:
            tmp_string.append(' noedit="%s"' % self.noedit)
        if self.invisible:
            tmp_string.append(' invisible="%s"' % self.invisible)
        if self.docache:
            tmp_string.append(' docache="%s"' % self.docache)
        if self.translations:
            tmp_string.append(' translations="%s"' % self.translations)
        tmp_string.append("/>")
        ioHandle.write("".join(tmp_string) + "\n")


# FIXME Index, Unique, Foreignkey, Checks do not exist


class Constraints(object):
    __classname__ = "Constraints"

    def __init__(self):
        self.index = {}
        self.unique = {}
        self.foreignkey = {}

    def getIndex(self, key):
        return self.index.get(key)

    def addIndex(self, key, obj):
        # assert isinstance(obj, Index)
        self.index[key] = obj

    def getUnique(self, key):
        return self.unique.get(key)

    def addUnique(self, key, obj):
        # assert isinstance(obj, Unique)
        self.unique[key] = obj

    def getForeignkey(self, key):
        return self.foreignkey.get(key)

    def addForeignkey(self, key, obj):
        # assert isinstance(obj, Foreignkey)
        self.foreignkey[key] = obj

    def storeXML(self, ioHandle, level=0):
        # keeps track of tab level depth
        tab = ""
        tab += "".join(([" "] * level * 4))

        # start generating xml
        tmp_string = []
        if level == 0:
            ioHandle.write('<?xml version="1.0"?>\n')
            ioHandle.write("<!-- Creation date: %s -->\n" % strftime("%d.%m.%Y"))
        tmp_string.append(tab + "<Constraints")
        tmp_string.append(">")
        ioHandle.write("".join(tmp_string) + "\n")

        # generates sub elements
        for key in self.index:
            entry = self.index[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        # generates sub elements
        for key in self.unique:
            entry = self.unique[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        # generates sub elements
        for key in self.foreignkey:
            entry = self.foreignkey[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        ioHandle.write(tab + "</Constraints>\n")


class Table(object):
    __classname__ = "Table"

    def __init__(self, name):
        # no type check for 'key' available.
        self.name = name
        self.primarykey = None
        self.column = {}
        self.checks = {}
        self.constraints = {}
        self.ebase = None
        self.label = None
        self.uid = None

    def getName(self):
        return self.name

    def setName(self, name):
        # no type check for 'key' available.
        self.name = name

    def getPrimarykey(self):
        return self.primarykey

    def setPrimarykey(self, primarykey):
        assert isinstance(primarykey, UnicodeType) or isinstance(primarykey, StringType)
        self.primarykey = primarykey

    def getColumn(self, key):
        return self.column.get(key)

    def addColumn(self, key, obj):
        assert isinstance(obj, Column)
        self.column[key] = obj

    def getChecks(self, key):
        return self.checks.get(key)

    # FIXME Checks does not exist
    def addChecks(self, key, obj):
        # assert isinstance(obj, Checks)
        self.checks[key] = obj

    def getConstraints(self, key):
        return self.constraints.get(key)

    def addConstraints(self, key, obj):
        assert isinstance(obj, Constraints)
        self.constraints[key] = obj

    def getEbase(self):
        return self.ebase

    def setEbase(self, ebase):
        assert isinstance(ebase, UnicodeType) or isinstance(ebase, StringType)
        self.ebase = ebase

    def getLabel(self):
        return self.label

    def setLabel(self, label):
        assert isinstance(label, UnicodeType) or isinstance(label, StringType)
        self.label = label

    def getUid(self):
        return self.uid

    def setUid(self, uid):
        assert isinstance(uid, UnicodeType) or isinstance(uid, StringType)
        self.uid = uid

    def storeXML(self, ioHandle, level=0):

        # keeps track of tab level depth
        tab = ""
        tab += "".join(([" "] * level * 4))

        # start generating xml
        tmp_string = []
        if level == 0:
            ioHandle.write('<?xml version="1.0"?>\n')
            ioHandle.write("<!-- Creation date: %s -->\n" % strftime("%d.%m.%Y"))
        tmp_string.append(tab + "<Table")
        if self.name:
            tmp_string.append(' name="%s"' % self.name)
        if self.primarykey:
            tmp_string.append(' primarykey="%s"' % self.primarykey)
        if self.label:
            tmp_string.append(' label="%s"' % self.label)
        if self.ebase:
            tmp_string.append(' ebase="%s"' % self.ebase)
        if self.uid:
            tmp_string.append(' uid="%s"' % self.uid)
        tmp_string.append(">")
        ioHandle.write("".join(tmp_string) + "\n")

        # generates sub elements
        for key in self.column:
            entry = self.column[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        # generates sub elements
        for key in self.checks:
            entry = self.checks[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        # generates sub elements
        for key in self.constraints:
            entry = self.constraints[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        ioHandle.write(tab + "</Table>\n")


class Tabledefinition(object):
    __classname__ = "Tabledefinition"

    def __init__(self):
        self.table = {}
        self.list = {}

    def getTable(self, key):
        return self.table.get(key)

    def addTable(self, key, obj):
        assert isinstance(obj, Table)
        self.table[key] = obj

    def getList(self, key):
        return self.list.get(key)

    def addList(self, key, obj):
        assert isinstance(obj, List)
        self.list[key] = obj

    def storeXML(self, ioHandle, level=0):

        # keeps track of tab level depth
        tab = ""
        tab += "".join(([" "] * level * 4))

        # start generating xml
        tmp_string = []
        if level == 0:
            ioHandle.write('<?xml version="1.0"?>\n')
            ioHandle.write("<!-- Creation date: %s -->\n" % strftime("%d.%m.%Y"))
        tmp_string.append(tab + "<Tabledefinition")
        tmp_string.append(">")
        ioHandle.write("".join(tmp_string) + "\n")

        # generates sub elements
        # tables
        for key in self.table:
            entry = self.table[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        # lists
        for key in self.list:
            entry = self.list[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        ioHandle.write(tab + "</Tabledefinition>\n")


class Icondefinitions(object):
    # This class is not used anymore by the zopra.core. But it has to remain for the legacy package to work.
    __classname__ = "Icondefinitions"

    def __init__(self):
        self.image = {}

    def getImage(self, key):
        return self.image.get(key)

    def addImage(self, key, obj):
        assert isinstance(obj, ImageProperties)
        self.image[key] = obj

    def storeXML(self, ioHandle, level=0):

        # keeps track of tab level depth
        tab = ""
        tab += "".join(([" "] * level * 4))

        # start generating xml
        tmp_string = []
        if level == 0:
            ioHandle.write('<?xml version="1.0"?>\n')
            ioHandle.write("<!-- Creation date: %s -->\n" % strftime("%d.%m.%Y"))
        tmp_string.append(tab + "<Icondefinitions")
        tmp_string.append(">")
        ioHandle.write("".join(tmp_string) + "\n")

        # generates sub elements
        for key in self.image:
            entry = self.image[key]
            if entry and hasattr(entry, "storeXML"):
                entry.storeXML(ioHandle, level + 1)

        ioHandle.write(tab + "</Icondefinitions>\n")


DEF_TYPES = (
    "Columnlist",
    "Column",
    "Table",
    "List",
    "Image",
    "Tabledefinition",
    "Constraints",
    "Icondefinitions",
)


class XMLHandler(ContentHandler):
    def __init__(self):

        ContentHandler.__init__(self)
        self.tmpObjects = {}
        self.lvlElement = {}
        self.prevList = []
        self.rootObject = None
        self.idCounter = 0

    def getObjectTree(self):
        return self.rootObject

    def incElementLevel(self, element):
        if not self.lvlElement.get(element):
            self.lvlElement[element] = 0
        else:
            self.lvlElement[element] += 1

    def decElementLevel(self, element):
        if not self.lvlElement.get(element):
            pass
            # raise ValueError('Too many closing tags \
            #                   for element %s.' % element)
        else:
            self.lvlElement[element] -= 1

    def startElement(self, name, attrs):
        if name not in DEF_TYPES:
            return

        self.incElementLevel(name)

        tmpObject = None

        if name == "Columnlist":
            tmpObject = Columnlist()

            if attrs.get("list"):
                tmpObject.setList(attrs["list"])

        elif name == "Column":
            tmpObject = Column(
                attrs.get("name"),
                attrs.get("type"),
            )

            if attrs.get("label"):
                tmpObject.setLabel(attrs["label"])

            if attrs.get("default"):
                tmpObject.setDefault(attrs["default"])

            if attrs.get("notnull"):
                tmpObject.setNotnull(attrs["notnull"])

            if attrs.get("autoinc"):
                tmpObject.setAutoinc(attrs["autoinc"])

            if attrs.get("manager"):
                tmpObject.setManager(attrs["manager"])

            if attrs.get("function"):
                tmpObject.setFunction(attrs["function"])

            if attrs.get("noconnect"):
                tmpObject.setNoconnect(attrs["noconnect"])

            if attrs.get("invisible"):
                tmpObject.setInvisible(attrs["invisible"])

            if attrs.get("notes"):
                tmpObject.setNotes(attrs["notes"])

            if attrs.get("noteslabel"):
                tmpObject.setNoteslabel(attrs["noteslabel"])

            if attrs.get("labelsearch"):
                tmpObject.setLabelsearch(attrs["labelsearch"])

            if attrs.get("map"):
                tmpObject.setMap(attrs["map"])

        elif name == "Table":
            tmpObject = Table(
                attrs.get("name"),
            )

            if attrs.get("primarykey"):
                tmpObject.setPrimarykey(attrs["primarykey"])

            if attrs.get("label"):
                tmpObject.setLabel(attrs["label"])

            if attrs.get("ebase"):
                tmpObject.setEbase(attrs["ebase"])

            if attrs.get("uid"):
                tmpObject.setUid(attrs["uid"])

        elif name == "List":
            tmpObject = List(attrs.get("name"))

            if attrs.get("label"):
                tmpObject.setLabel(attrs["label"])

            if attrs.get("noedit"):
                tmpObject.setNoedit(attrs["noedit"])

            if attrs.get("invisible"):
                tmpObject.setInvisible(attrs["invisible"])

            if attrs.get("docache"):
                tmpObject.setDocache(attrs["docache"])

            if attrs.get("translations"):
                tmpObject.setTranslations(attrs["translations"])

        elif name == "Image":
            tmpObject = ImageProperties(attrs.get("src"), attrs.get("title"))

            if attrs.get("package"):
                tmpObject.setPackage(attrs["package"])

            if attrs.get("alt"):
                tmpObject.setAlt(attrs["alt"])

            if attrs.get("desc"):
                tmpObject.setDesc(attrs["desc"])

            if attrs.get("border"):
                try:
                    b = int(attrs["border"])
                except ValueError:
                    pass
                else:
                    tmpObject.setBorder(b)

            if attrs.get("width"):
                try:
                    w = int(attrs["width"])
                except ValueError:
                    pass
                else:
                    tmpObject.setWidth(w)

            if attrs.get("height"):
                try:
                    h = int(attrs["height"])
                except ValueError:
                    pass
                else:
                    tmpObject.setHeight(h)

        elif name == "Tabledefinition":
            tmpObject = Tabledefinition()

        elif name == "Constraints":
            tmpObject = Constraints()

        elif name == "Icondefinitions":
            tmpObject = Icondefinitions()

        if tmpObject:
            self.prevList.append(tmpObject)

    def endElement(self, name):
        if name not in DEF_TYPES:
            return

        lenList = len(self.prevList)
        if lenList > 1:
            entry = self.prevList[lenList - 1]
            self.idCounter += 1
            key = self.idCounter
            # get object
            obj = self.prevList[lenList - 2]
            # get add function from object
            func = getattr(obj, "add%s" % entry.__classname__)
            # call add function
            func(key, self.prevList[lenList - 1])
        elif lenList == 1:
            self.rootObject = self.prevList[0]
        self.prevList = self.prevList[0 : lenList - 1]

        self.decElementLevel(name)
