from AccessControl import getSecurityManager
from zope.interface import implements
from zopra.core import zopraMessageFactory as _


try:
    from tud.theme.webcms2.interfaces import INavigationExtender
except ImportError:
    from zope.interface import Interface as INavigationExtender


class NavigationExtender:
    implements(INavigationExtender)

    def __init__(self, nav_root_obj, context, request):
        """Initialize NavigationExtender object

        :param nav_root_obj: the current navigation root
        :type nav_root_obj: object
        :param context: the context object (IHasNavigationExtender implementer)
        :type context: object
        :param request: the current request
        :type request: ZPublisher.HTTPRequest.HTTPRequest
        """
        self.nav_root_obj = nav_root_obj
        self.context = context
        self.context_path = "/".join(context.getPhysicalPath())
        self.request = request

    def _create_breadcrumb(self, name, path, in_current_path=False, review_state=None, context=None):
        """Creates a breadcrumb dictionary entry

        :param name: title, which will be shown in the navigation
        :type name: string
        :param path: relative path based on context
        :type path: string
        :param in_current_path: True if this breadcrumb is in current path, defaults to False
        :type in_current_path: bool, optional
        :param review_state: review_state indicates which markers to use for the breadcrumb item, defaults to None
        :type review_state: string, optional
        :param context: base context for the breadcrumb will be either the given context object or (fallback) the IHasNavigationExtender in self.context, defaults to None
        :type context: object, optional
        :return: breadcrumb entry
        :rtype: dict
        """
        if not context:
            context = self.context
        id = path.split("/")[-1]
        return {
            "children": [],
            "description": "",
            "id": id,
            "in_current_path": in_current_path,
            "is_active": False,
            "name": name,
            "path": context.absolute_url_path() + "/" + path,
            "position": (),
            "review_state": review_state or "",
            "show_url": True,
            "url": context.absolute_url() + "/" + path,
        }

    def extend_main_navigation(self, nav_root):
        """Extends the navigation root

        :param nav_root: current main navigation
        :type nav_root: dict
        :return: modified navigation
        :rtype: dict
        """
        return nav_root

    @property
    def is_editor(self):
        """Determines, whether the current user is an editor.

        :return: True, if it is an editor, otherwise False
        :rtype: boolean
        """
        return getSecurityManager().getUser().has_role(["ZopRAAuthor", "ZopRAReviewer", "ZopRAAdmin"], self.context)

    @property
    def in_app_folder(self):
        """Determines, whether the user is in the app folder aka in the editorial area

        :return: True, if being in the app folder, otherwise False
        :rtype: boolean
        """
        return "app" in (getattr(parent, "__name__", "") for parent in self.request.PARENTS)

    def get_breadcrumb_item(self, breadcrumbs):
        """Get the breadcrumb item represents the current context.

        :param breadcrumbs: current breadcrumb navigation
        :type breadcrumbs: dict
        :return: breadcrumb if found, otherwise None
        :rtype: dict|nothing
        """
        for item in breadcrumbs["items"]:
            if item["path"] == self.context_path:
                return item

    def extend_breadcrumbs(self, breadcrumbs):
        """Extend the navigation with app specific entries:
            * "Editorial" is added as sub-entry of the main database application folder if the user has at least one zopra role

        This method should be overridden, to allow custom behavior.

        :param breadcrumbs: current breadcrumb navigation
        :type breadcrumbs: dict
        :return: modified navigation
        :rtype: dict
        """
        zopra_breadcrumb = self.get_breadcrumb_item(breadcrumbs)

        if not zopra_breadcrumb:
            return breadcrumbs

        zopra_children = zopra_breadcrumb["children"]

        if self.is_editor:
            message = self.context.translate(_(u"zopra_editorial", default=u"Editorial"))
            editorial_breadcrumb_item = self._create_breadcrumb(
                message,
                "app/zopra_main_form",
                False,
                "private",
            )
            zopra_children.append(editorial_breadcrumb_item)

            # Replicate editorial item, when we are somewhere beyond app
            if self.in_app_folder:
                breadcrumbs["items"].append(editorial_breadcrumb_item)

        return breadcrumbs
