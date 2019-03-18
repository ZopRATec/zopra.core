'''
Created on 6 May 2018

@author: Peter Seifert
'''
# is this necessary?
#from builtins import int, str

IntType     = int
LongType    = int
ListType    = list
StringType  = str
UnicodeType = str
TupleType   = tuple
BooleanType = bool
FloatType   = float
ClassType   = type
DictType    = dict
StringTypes = (str, )
# rude basestring setup (py2/3)
basestring  = (type(''), type(u''))
