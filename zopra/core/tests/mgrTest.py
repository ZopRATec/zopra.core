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
