"""The test manager for tests with templates"""

from zopra.core import ZM_TEST2
from zopra.core.tools.TemplateBaseManager import TemplateBaseManager


class mgrTest(TemplateBaseManager):
    """ Test Manager """

    _className = ZM_TEST2
    _classType = TemplateBaseManager._classType + [_className]
    meta_type = _className

    # generic addForm hints
    suggest_id = "testapp"
    suggest_name = "Test Manager"

    def startupConfig(self, REQUEST):
        """Function called after creation by manageAddZMOMGeneric"""
        # insert some list values
        lobj = self.listHandler.get("asinglelist")
        lobj.addValue("Avalue")
        lobj.addValue("Bvalue")
        lobj.addValue("Cvalue")
        lobj = self.listHandler.get("amultilist")
        lobj.addValue("1value")
        lobj.addValue("2value")
        lobj = self.listHandler.get("ahierarchylist")
        lobj.addValue("Level1-A", rank="0")
        lobj.addValue("Level1-B", rank="0")
        lobj.addValue("Level2-A", rank="1")
        lobj.addValue("Level2-B", rank="1")
        lobj.addValue("Level3-A", rank="3")
        lobj.addValue("Level3-B", rank="3")
        lobj.addValue("Level3-C", rank="3")
