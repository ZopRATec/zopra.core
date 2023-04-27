"""Filter class for sql generation"""

from copy import copy
from time import strftime
from time import strptime

from builtins import object

from PyHtmlGUI.kernel.hgTable import hgTable
from PyHtmlGUI.widgets.hgLabel import hgNEWLINE
from zopra.core import ZC
from zopra.core.elements.Buttons import DLG_CUSTOM
from zopra.core.types import ListType


# deprecated module type checking / date conversion
# date mapping for convertDate
format_list = [
    "%d-%m-%y",
    "%d-%m-%Y",
    "%d.%m.%y",
    "%d.%m.%Y",
    "%d %m %y",
    "%d %m %Y",
    "%d/%m/%y",
    "%d/%m/%Y",
    "%m.%y",
    "%m.%Y",
    "%m/%d/%y",
    "%m/%d/%Y",
    "%d\\%m\\%y",
    "%d\\%m\\%Y",
]
format_new = "%d.%m.%Y"


def convertDateDeprecated(old_date):
    """Converts different date formats in european standard.

    These function is only for converting date types before inserting in a
    database!

    :param old_date: a date that should be changed into a new format.
    :return: new date if conversion did work, otherwise an empty string.
    """
    if not old_date:
        return "NULL"

    old_date = str(old_date).strip()

    # set this to '' to differentiate between not old_date
    # and no conversion found
    new_date = ""
    for format_old in format_list:
        try:
            new_date = strftime(format_new, strptime(old_date, format_old))
            return new_date
        except ValueError:
            pass

    return new_date


def checkTypeDeprecated(
    value, column_type, operator=False, label=None, do_replace=True
):
    """makes all standard conversions and checking for supported Types
    and returns altered value-string.
    Returns an operator as well, if param operator is True
    """
    # BUG: user can cause misbehaviour by mixing keywords... redesign to brake
    #     non-fitting parts into conjunctions (need col-name for that)

    # first some checks

    # value = None leads to problems with str(value)
    if not (value is None or isinstance(value, ListType)):
        value = str(value).strip()
        pos_to = value.find("_to_")
        pos_sep = value.find("__")
        pos_lt = value.find("_<_")
        pos_lte = value.find("_<=_")
        pos_gt = value.find("_>_")
        pos_gte = value.find("_>=_")

    # NULL (0 can be ignored cause it was converted to '0' which is True
    if not value or value == "NULL" or value == "_0_" or value == ["NULL"]:
        value = "NULL"
        oper = "IS"

    # lists for freetext-search-results
    elif isinstance(value, ListType):
        if "_not_ NULL" in value or "_not_NULL" in value:
            value = "NOT NULL"
            oper = "IS"
        else:
            entry_list = map(
                lambda onevalue: checkTypeDeprecated(
                    onevalue, column_type, False, label
                ),
                value,
            )
            value = "(%s)" % ", ".join(entry_list)
            oper = "IN"

    # check for _not_NULL
    elif value.replace(" ", "") == "_not_NULL" or value.replace(" ", "") == "_not__0_":
        value = "NOT NULL"
        oper = "IS"

    # we allow range searches with keyword _to_
    elif pos_to != -1:
        value = "%s and %s" % (
            checkTypeDeprecated(value[:pos_to].rstrip(), column_type, False, label),
            checkTypeDeprecated(
                value[pos_to + 4 :].lstrip(), column_type, False, label
            ),
        )
        oper = "BETWEEN"

    elif pos_sep != -1:
        valuelist = value.split("__")
        oper = "IN"
        entry_list = map(
            lambda onevalue: checkTypeDeprecated(
                onevalue.strip(), column_type, False, label
            ),
            valuelist,
        )
        value = "(%s)" % ", ".join(entry_list)
    elif pos_lt != -1:
        oper = "<"
        value = checkTypeDeprecated(
            value[pos_lt + 3 :].strip(), column_type, False, label
        )
    elif pos_lte != -1:
        oper = "<="
        value = checkTypeDeprecated(
            value[pos_lte + 4 :].strip(), column_type, False, label
        )
    elif pos_gt != -1:
        oper = ">"
        value = checkTypeDeprecated(
            value[pos_gt + 3 :].strip(), column_type, False, label
        )
    elif pos_gte != -1:
        oper = ">="
        value = checkTypeDeprecated(
            value[pos_gte + 4 :].strip(), column_type, False, label
        )
    else:
        oper = ""
        labelstr = ""
        if label:
            labelstr = " for field %s" % label

        if not column_type:
            raise ValueError("No Type found%s." % labelstr)

        if column_type == "string" or column_type == "memo":
            oper = ""
            value = str(value)
            if do_replace:
                # replace wildcards
                value = value.replace("*", "%")
            # escape some characters
            value = value.replace("'", "\\'")
            # remove double escape for ' in text
            value = value.replace("\\\\'", "\\'")

            # we allow not like searches with keyword _not_
            if str(value).find("_not_") == 0:
                value = value[5:].lstrip()
                oper = "not "
            oper += "LIKE"
            value = "'" + value + "'"

        elif column_type == "date":
            value = value.replace("*", "%")
            oper = ""
            if str(value).find("_not_") == 0:
                value = value[5:].lstrip()
                oper = "not "

            if value.find("%") == -1:
                value = convertDateDeprecated(value)
                if not value:
                    raise ValueError("Wrong Date Format%s." % labelstr)

            value = "'%s'" % value
            oper += "LIKE"

        elif column_type == "int" or column_type == "singlelist":
            # we allow != searches with keyword _not_
            if str(value).find("_not_") == 0:
                value = value[5:].lstrip()
                oper = "<>"
            else:
                oper = " = "
            try:
                int(value)
            except ValueError:
                label = "You inserted a wrong value%s: %s (type: %s)."
                label = label % (labelstr, value, column_type)
                raise ValueError(label)

        elif column_type == "float":
            # we allow != searches with keyword _not_
            if str(value).find("_not_") == 0:
                value = value[5:].lstrip()
                oper = "<>"
            else:
                oper = " = "
            try:
                float(value)
            except ValueError:
                label = "You inserted a wrong value%s: %s (type: %s)."
                label = label % (labelstr, value, column_type)
                raise ValueError(label)

        elif column_type == "bool":
            oper = " = "
            if value and value != "NULL" and value != "0":
                value = 1
            else:
                # for add/edit there is no difference between NULL and not there
                # it all results to a NULL value in the column
                # so for search, we can look for anything (True) or NULL (False)
                # but for add/edit it is important that the int 0 is translated to NULL
                value = "NULL"
                oper = " IS "

        elif column_type == "multilist" or column_type == "hierarchylist":

            raise ValueError("checkType called on multi- or hierarchylist")

        else:
            value = str(value)
            oper = "="

    if operator:
        return (str(value), oper)

    else:
        return str(value)


class Filter(object):
    """Provides Complex Structures for Where clause for sql generation"""

    AND = "AND"
    OR = "OR"
    OPERATOR = [AND, OR]

    def __init__(self, op=AND, temp=None):
        """Constructs a Filter object."""
        assert op in Filter.OPERATOR
        if temp:
            self.template = temp
        else:
            self.template = {}
        self.constraints = {}
        self.children = []
        self.operator = op
        self.final = False
        self.invalid = True
        self.sql = None

    def copy(self):
        """copy constraints, children, op, final"""
        cop = Filter(self.operator, self.template)
        cop.constraints = copy(self.constraints)
        for child in self.children:
            ccopy = child.copy()
            cop.addChild(ccopy)
        if self.final:
            cop.setFinal()
        return cop

    def setFinal(self):
        """Finalize. No changes done afterwards."""
        self.final = True

    def setInvalid(self):
        """Invalidate."""
        self.invalid = True

    def setTemplate(self, attrdict):
        """"""
        self.template = copy(attrdict)

    def getTemplate(self):
        """"""
        return self.template

    def setOperator(self, op):
        """"""
        if op in self.OPERATOR:
            self.operator = op
            self.setInvalid()

    def getOperator(self):
        """"""
        return self.operator

    def getConsCount(self):
        """return number of own and children constraints."""
        count = len(self.constraints)
        for child in self.children:
            if child.isConstrained():
                count += 1
        return count

    def setConstraints(self, consdict, manager, prefix=None, tableData=None):
        """Stores matching constraints (including [DLG_CUSTOM+]prefix)
        from the dictionary, propagates it to its children.
        If this filter doesn't have a template, tableData has to be given."""
        if self.final:
            return False

        if not prefix:
            prefix = ""

        # test tabledef (template or tableData dict)
        if not self.template and tableData is None:
            msg = "Internal Error: no tabledef found in filter"
            raise ValueError(msg)

        tempcons = {}
        for entry in consdict:
            # accept entry with NOT_IN flag
            if (
                len(entry) - 7 == entry.find("_NOT_IN")
                and entry[: len(entry) - 7] in consdict
                and isinstance(consdict[entry[: len(entry) - 7]], ListType)
            ):
                # check template / tableData
                if not self.template:
                    field = tableData.getField(entry[: len(entry) - 7], manager)
                else:
                    field = self.template.get(entry[: len(entry) - 7])
                if field.get(ZC.COL_TYPE) in ["int"]:
                    tempcons[entry] = consdict[entry]

            # if not consdict[entry] has to be used to not end with
            # a lots of WHERE field = '',
            # so wherefield is NULL should be used for NULL-testing
            if not consdict[entry] and not consdict[entry] == 0:
                continue

            # get the matching entries out of the dict
            # ([[DLG_CUSTOM+]prefix+]field]
            if entry[:2] == DLG_CUSTOM:
                entry = entry[2:]
                pre = DLG_CUSTOM
            else:
                pre = ""

            # prefix handling
            if prefix:
                plen = len(prefix)
            else:
                plen = 0

            # check prefix (no prefix -> '' == '' -> go on:
            if entry[:plen] == prefix:

                # check template / tableData
                if not self.template:
                    field = tableData.getField(entry[plen:], manager)
                else:
                    field = self.template.get(entry[plen:])

                # found description
                if field:

                    # build where clause for string lists
                    if field.get(ZC.COL_TYPE) in ["string", "memo"] and isinstance(
                        consdict[pre + entry], ListType
                    ):
                        if pre + entry + "_AND" in consdict:
                            parent = Filter("AND")
                        else:
                            parent = Filter("OR")
                        for listentry in consdict[pre + entry]:
                            child = Filter("AND")
                            child.setConstraints(
                                {entry[plen:]: listentry}, manager, tableData=tableData
                            )
                            child.setFinal()
                            parent.addChild(child)
                        parent.setFinal()
                        self.addChild(parent)
                        continue

                    # test AND-concatenated multi/hierarchy-lists ... done extra, continue here
                    if (
                        field.get(ZC.COL_TYPE) == "multilist"
                        or field.get(ZC.COL_TYPE) == "hierarchylist"
                    ):
                        # and-concat is handled in the TableNode for len > 1 -> continue
                        if consdict.get(pre + entry + "_AND"):
                            values = consdict.get(pre + entry)
                            if isinstance(values, ListType) and len(values) > 1:
                                continue
                    # put in dict
                    tempcons[entry[plen:]] = consdict[pre + entry]
                    # better not remove to allow normal search for special attrs
                    # e.g. creator for ebase
                    # remove from source
                    # consdict.pop(pre + entry)

        # store

        if self.constraints != tempcons:
            self.constraints = tempcons
            change = True
        else:
            change = False

        for child in self.children:
            change |= child.setConstraints(consdict, manager, prefix, tableData)

        if change:
            self.setInvalid()
        return change

    def setUncheckedConstraints(self, consdict):
        """Set constraints without any field check."""
        for cons in consdict:
            self.constraints[cons] = consdict[cons]
        self.setInvalid()

    def setMultiConstraint(self, name, valuelist):
        """Create children for each value of valuelist"""
        for value in valuelist:
            fil = Filter(self.operator)
            fil.setUncheckedConstraints({name: value})
            self.addChild(fil)

    def getConstraints(self):
        """return the set constraints from this filter obj and its children"""
        cons = copy(self.constraints)
        for child in self.children:
            cons2 = child.getConstraints()
            for con in cons2:
                cons[con] = cons2[con]
        return cons

    def isConstrained(self):
        """return True for constrained object or children"""
        if self.constraints:
            return True
        for child in self.children:
            if child.isConstrained():
                return True
        return False

    def addChild(self, filterobj):
        """Add a child to this filter object.
        Children are joined with the other constraints via the operator,
        they can be complex filter trees."""
        if self.final:
            return
        # only accept Filter
        assert isinstance(filterobj, Filter)
        # with template set (neccessary for propagation) or final
        if not filterobj.getTemplate() and not filterobj.final:
            err = "Child Filter must have template set or be final."
            raise ValueError(err)
        self.children.append(filterobj)
        self.setInvalid()

    def getStructureHtml(self):
        """Generates an html-overview of the tree structure"""
        tab = hgTable(border=1)
        tab[0, 0] = self.operator
        if self.constraints:
            for entry in self.constraints:
                tab[0, 0] += hgNEWLINE + entry + ": " + str(self.constraints[entry])
        if self.children:
            tab[0, 1] = "Children:"
            row = 1
            for entry in self.children:
                tab[row, 1] = entry.getStructureHtml()
                row += 1
            tab.setCellSpanning(0, 0, row, 1)
        return tab

    def getSQL(self, tablename, manager, tableData=None, checker=None):
        """Build where-string from constraints and children."""
        # first check for validity and return cached sql
        if not self.invalid:
            return self.sql
        # TODO: check usage and remove the checkTypeDeprecated version
        # test checker or else import
        if checker and hasattr(checker, "forwardCheckType"):
            checkType = checker.forwardCheckType
        else:
            checkType = checkTypeDeprecated

        # for multi, listname.listname can be used (first 'listname' is an alias)

        # if we don't have a template (for coltypes) we need tableData (TablePrivate)
        if not self.template and not tableData:
            err = "Column info missing. Use tableData or template."
            raise ValueError(err)

        wherestring = ""
        wherepart = []

        # need mgrId for constraint db names
        mgrId = manager.id

        for cons in self.constraints:
            if self.template:
                ctype = self.template.get(cons)
            else:
                field = tableData.getField(cons, manager)
                ctype = field.get(ZC.COL_TYPE)

            # ignore entry with NOT_IN flag
            if (
                len(cons) - 7 == cons.find("_NOT_IN")
                and cons[: len(cons) - 7] in self.constraints
            ):
                continue
            # not for multi/hierarchy lists
            if ctype not in ZC.ZCOL_MLISTS:
                constraint = self.constraints[cons]
                value, operator = checkType(constraint, ctype, True, cons)

                if cons + "_NOT_IN" in self.constraints:
                    operator = "NOT " + operator

                conname = "%s%s.%s" % (mgrId, tablename, cons)

                # special handling for mysql <> x - handling of NULL-Values (for all fields)
                if operator == "<>":
                    wherepart.append(
                        "(%s %s %s OR %s IS NULL)" % (conname, operator, value, conname)
                    )
                else:
                    # special case: in with NULL -> use COALESQUE
                    if operator == 'IN' and isinstance(constraint, list) and 'NULL' in constraint:
                        # recalculate the value with -1 instead of NULL
                        constraint[constraint.index('NULL')] = -1
                        value = checkType(constraint, ctype, False, cons)
                        # use coalesce on the column with -1
                        conname = "COALESCE(%s, -1)" % conname

                    # the default statement
                    wherepart.append("%s %s %s" % (conname, operator, value))
            else:
                # multilist-constraints

                value, operator = checkType(self.constraints[cons], "int", True)
                if tableData:
                    _list = tableData.listHandler.getList(tablename, cons)
                    conname = "%s.%s" % (_list.dbname, cons)
                else:
                    conname = "%smulti%s.%s" % (mgrId, cons, cons)
                wherepart.append("%s %s %s" % (conname, operator, value))
        if self.children:
            for child in self.children:
                count = child.getConsCount()
                if count > 1:
                    ccons = child.getSQL(tablename, manager, tableData, checker)
                    wherepart.append("(%s)" % ccons)
                elif count == 1:
                    ccons = child.getSQL(tablename, manager, tableData, checker)
                    wherepart.append(ccons)
        if wherepart:
            oper = " %s " % self.operator
            wherestring = oper.join(wherepart)
        # validation
        self.invalid = False
        self.sql = wherestring

        return wherestring
