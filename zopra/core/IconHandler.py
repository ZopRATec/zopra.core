from copy import copy
from os import path
from zopra.core.types import StringType

from zopra.core import BadRequest
from zopra.core import Folder
from zopra.core import Image
from zopra.core.ImageProperties import ImageProperties
from zopra.core.utils import getASTFromXML
from zopra.core.utils import getZopRAPath


class IconHandler(Folder):
    """IconHandler instance will reside in the Manager object and handles the Icons."""

    # class variables
    _className = "IconHandler"
    _classType = [_className]
    meta_type = _className

    _properties = Folder._properties

    App = "hgApplication"

    def __init__(self, name, package=None):
        """Constructs a IconHandler."""
        Folder.__init__(self, name)

        self.title2properties = {}
        self.imgsources = set()
        self.id2title = {}

        self.package = package

    def filtered_meta_types(self, user=None):
        # Return a list of the types for which the user has
        # adequate permission to add that type of object.
        folder_meta_types = Folder.filtered_meta_types(self, user=None)

        meta_types = []

        for fmt in folder_meta_types:
            if fmt["name"] == "Image":
                meta_types.append(fmt)

        return meta_types

    def _setObject(
        self, id, object, roles=None, user=None, set_owner=1, suppress_events=False
    ):
        """Set an object into this container."""

        assert isinstance(object, Image)

        if not id:
            raise BadRequest("Image data missing.")

        if id in self.imgsources:
            raise BadRequest('Image with Id "%s" already exists.' % id)

        key = getattr(object, "title", "")

        if not key:
            key = str(object.id())
            title = ""
        else:
            title = key

        if not key:
            raise BadRequest("Image Title missing.")

        if self.has(key):
            raise BadRequest('Image with Title "%s" already exists.' % title)

        # register id
        self.imgsources.add(id)

        # create properties if necessary img inserted by user via ZMI
        if key not in self.title2properties:
            w = getattr(object, "width", "")
            h = getattr(object, "height", "")
            alt = getattr(object, "alt", "")

            # no package for externally loaded images
            img_properties = ImageProperties(id, title, "", alt, "", None, w, h)

            self.title2properties[key] = copy(img_properties)

        self.id2title[id] = key

        return Folder._setObject(
            self, id, object, roles, user, set_owner, suppress_events
        )

    def xmlInit(self, xml):
        """Initializes all tables specified in the xml-string"""
        tmp_obj = getASTFromXML(xml)

        # iterate over tables
        for icon_idx in tmp_obj.image:
            img_descr = tmp_obj.image[icon_idx]

            # TODO: add descriptions to
            self.attach(img_descr)

    def manage_delObjects(self, ids=None, REQUEST=None):
        """replaces ObjectManager's manage_delObjects.
        Be careful to only use this method to remove images.
        Using _delObject will lead to orphan image_properties lying around"""

        for _id in ids:
            self.delete(self.id2title[_id])

        return Folder.manage_delObjects(self, ids, REQUEST)

    def has(self, title):
        """"""

        assert isinstance(title, StringType) or isinstance(title, type(unicode("")))
        return title in self.title2properties

    def add(self, img_properties):
        """Adds an image to the iconHandler and set """

        assert isinstance(img_properties, ImageProperties)
        assert img_properties.title

        if self.has(img_properties.title):
            return False

        if img_properties.src in self.imgsources:
            return False

        filename = getZopRAPath()

        if img_properties.pkg:
            filename += "/" + img_properties.pkg

        elif self.package:
            filename += "/" + self.package

        filename += "/images/" + img_properties.src

        if not path.exists(filename):
            return False

        fHandle = open(filename, "r")
        image = Image(img_properties.src, img_properties.title, fHandle.read())

        self._setObject(img_properties.src, image)

        # replace generic properties
        self.title2properties[img_properties.title] = copy(img_properties)

        return True

    def attach(self, img_properties, remove_empty=False):
        """Updates properties for image referenced in img_properties.src with new settings
        Setting remove_empty to true will remove unset properties in img_properties.
        Note: title cannot be unset
        """

        assert isinstance(img_properties, ImageProperties)
        assert img_properties.title

        if img_properties.src not in self.imgsources:
            return False

        title = self.id2title.get(img_properties.src)

        if not title:
            return False

        current_properties = self.get(title)

        # update settings
        if img_properties.title:
            current_properties.title = img_properties.title

        if img_properties.alt:
            current_properties.alt = img_properties.alt
        elif remove_empty:
            current_properties.alt = None

        if img_properties.border is not None:
            current_properties.border = img_properties.border
        elif remove_empty:
            current_properties.border = None

        if img_properties.width:
            current_properties.width = img_properties.width
        elif remove_empty:
            current_properties.width = None

        if img_properties.height:
            current_properties.height = img_properties.height
        elif remove_empty:
            current_properties.height = None

        # remove old title if necessary
        if title != img_properties.title:
            img = self.getImageObject(title)
            img.title = img_properties.title

            del self.title2properties[title]
            title = img_properties.title

        # set updated properties
        self.title2properties[title] = current_properties

        return True

    # extract filename from img sources
    # only unique filenames are allowed

    def delete(self, title, manage=False):
        """Delete"""

        assert isinstance(title, StringType)

        img_properties = self.get(title)

        if img_properties:
            if img_properties.title in self.title2properties:
                del self.title2properties[img_properties.title]
            self.imgsources.remove(img_properties.src)

            if img_properties.src in self.id2title:
                del self.id2title[img_properties.src]

            if manage:
                Folder.manage_delObjects(self, [img_properties.src])

        return img_properties

    def get(self, title, path=False):
        """Get"""

        assert isinstance(title, StringType)

        img_properties = None

        if self.has(title):
            img_properties = copy(self.title2properties[title])

        # maybe its unicode?
        if img_properties is None and self.has(unicode(title)):
            img_properties = copy(self.title2properties[unicode(title)])

        # adjust path
        if img_properties and path:
            img_properties.src = self.absolute_url() + "/" + img_properties.src

        return img_properties

    def getImageObject(self, title):
        """get Image Object"""

        img_object = None
        img_properties = self.get(title)

        if img_properties:
            assert hasattr(self, img_properties.src)

            img_object = getattr(self, img_properties.src)

        return img_object

    def getTitleList(self):
        """Return list of titles."""
        return self.title2properties.keys()

    def count(self):
        """Return number of managed objects."""
        return len(self.title2properties)
