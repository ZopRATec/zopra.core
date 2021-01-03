# Python 3 safety switch:
try:
    UnicodeType = unicode
except Exception:
    UnicodeType = str
IntType = int
LongType = int
ListType = list
StringType = str
TupleType = tuple
BooleanType = bool
FloatType = float
ClassType = type
DictType = dict
StringTypes = (str,)
# rude basestring setup (py2/3)
basestring = (type(""), type(u""))
