############################################################################
#    Copyright (C) 2004 by ZopRATec GbR                                    #
#    ingo.keller@zopratec.com                                              #
#                                                                          #
#    This program is free software; you can redistribute it and#or modify  #
#    it under the terms of the GNU General Public License as published by  #
#    the Free Software Foundation; either version 2 of the License, or     #
#    (at your option) any later version.                                   #
############################################################################

#
# Python Imports
#
import string
from time import strftime
from types import IntType

#
# PyHtmlGUI Imports
#
from PyHtmlGUI.widgets.hgPushButton import hgPushButton


# img button shortcuts
PB_PIXMAPSRC = hgPushButton.PB_PIXMAPSRC
PB_PIXMAPW = hgPushButton.PB_PIXMAPW
PB_PIXMAPH = hgPushButton.PB_PIXMAPH
PB_PIXMAPALT = hgPushButton.PB_PIXMAPALT


class ImageProperties(object):
    """\class ImageProperties"""

    # class variables
    _className = "ImageProperties"
    _classType = [_className]
    meta_type = _className

    # used in xml handler
    __classname__ = "Image"

    # property names
    # NOTE: what about longdesc attribute for html img tags?
    TITLE = "title"
    SRC = "src"
    PACKAGE = "package"
    ALT = "alt"
    DESC = "desc"
    BORDER = "border"
    WIDTH = "width"
    HEIGHT = "height"

    PROPERTIES = [TITLE, SRC, PACKAGE, ALT, DESC, BORDER, WIDTH, HEIGHT]

    def __init__(
        self,
        src,
        title="",
        package="",
        alt="",
        desc="",
        border=None,
        width=None,
        height=None,
    ):
        """\brief Constructs a ImageProperties."""
        self.__src = None
        self.__title = None
        self.__pkg = None
        self.__alt = None
        self.__desc = None
        self.__border = 0
        self.__width = None
        self.__height = None

        self.src = src

        if title:
            self.title = title

        if package:
            self.pkg = package

        if alt:
            self.alt = alt

        if desc:
            self.desc = desc

        if border:
            self.border = border

        if width:
            self.width = width

        if height:
            self.height = height

    # title property methods
    def setTitle(self, title):
        """\brief Set title property"""

        if title == "":
            title = None

        self.__title = title

    def getTitle(self):
        """\brief Get title property"""

        return self.__title

    title = property(getTitle, setTitle)

    # src property methods
    def setSource(self, src):
        """\brief Set src property"""

        assert src

        self.__src = str(src)

    def getSource(self):
        """\brief Get src property"""

        return self.__src

    src = property(getSource, setSource)

    # pkg property methods
    def setPackage(self, pkg):
        """\brief Set pkg property"""

        if pkg == "":
            pkg = None

        self.__pkg = pkg

    def getPackage(self):
        """\brief Get pkg property"""

        return self.__pkg

    pkg = property(getPackage, setPackage)

    # alt property methods
    def setAlt(self, alt):
        """\brief Set alt property"""

        if alt == "":
            alt = None

        self.__alt = alt

    def getAlt(self):
        """\brief Get alt property"""

        return self.__alt

    alt = property(getAlt, setAlt)

    # desc property methods
    def setDesc(self, desc):
        """\brief Set desc property"""

        if desc == "":
            desc = None

        self.__desc = desc

    def getDesc(self):
        """\brief Get desc property"""

        return self.__desc

    desc = property(getDesc, setDesc)

    # border property methods
    def setBorder(self, border):
        """\brief Set border property"""

        if border < 0:
            border = None

        self.__border = border

    def getBorder(self):
        """\brief Get border property"""

        return self.__border

    border = property(getBorder, setBorder)

    # width property methods
    def setWidth(self, width):
        """\brief Set width property"""

        assert isinstance(width, IntType)
        assert width >= 0

        if width == 0:
            width = None

        self.__width = width

    def getWidth(self):
        """\brief Get width property"""

        return self.__width

    width = property(getWidth, setWidth)

    # height property methods
    def setHeight(self, height):
        """\brief Set height property"""

        assert isinstance(height, IntType)
        assert height != ""

        if height == 0:
            height = None

        self.__height = height

    def getHeight(self):
        """\brief Get height property"""

        return self.__height

    height = property(getHeight, setHeight)

    # collective info retrieval
    def getPropertyDict(self):
        """\brief Get all properties as dict"""

        properties = {}
        properties[ImageProperties.SRC] = self.src

        if self.__title is not None:
            properties[ImageProperties.TITLE] = self.title

        if self.__pkg is not None:
            properties[ImageProperties.PACKAGE] = self.pkg

        if self.__alt is not None:
            properties[ImageProperties.ALT] = self.alt

        if self.__desc is not None:
            properties[ImageProperties.DESC] = self.desc

        if self.__border is not None:
            properties[ImageProperties.BORDER] = self.border

        if self.__width is not None:
            properties[ImageProperties.WIDTH] = self.width

        if self.__height is not None:
            properties[ImageProperties.HEIGHT] = self.height

        return properties

    def getSetPropertyNames(self):
        """\brief Get a list of all set properties"""

        propertynames = []

        propertynames.append(ImageProperties.SRC)

        if self.__title is not None:
            propertynames.append(ImageProperties.TITLE)

        if self.__pkg is not None:
            propertynames.append(ImageProperties.PACKAGE)

        if self.__alt is not None:
            propertynames.append(ImageProperties.ALT)

        if self.__desc is not None:
            propertynames.append(ImageProperties.DESC)

        if self.__border is not None:
            propertynames.append(ImageProperties.BORDER)

        if self.__width is not None:
            propertynames.append(ImageProperties.WIDTH)

        if self.__height is not None:
            propertynames.append(ImageProperties.HEIGHT)

        return propertynames

    def hasProperty(self, name):
        """\brief Returns whether a property is set or not.
        always True for ImageProperties.TITLE,
        ImageProperties.SRC and ImageProperties.PACKAGE
        """
        isset = True

        if name not in ImageProperties.PROPERTIES:
            return False

        if name == ImageProperties.TITLE:
            if self.__title is None:
                isset = False
        elif name == ImageProperties.PACKAGE:
            if self.__pkg is None:
                isset = False
        elif name == ImageProperties.ALT:
            if self.__alt is None:
                isset = False
        elif name == ImageProperties.DESC:
            if self.__desc is None:
                isset = False
        elif name == ImageProperties.BORDER:
            if self.__border is None:
                isset = False
        elif name == ImageProperties.WIDTH:
            if self.__width is None:
                isset = False
        elif name == ImageProperties.HEIGHT:
            if self.__height is None:
                isset = False

        return isset

    # get a dict that is consistent with  the ones handled by image buttons
    # NOTE: buttons should use this struct for icon description
    def getIconDict(self):
        """\brief Returns a dict that can be handled by hgPushbutton"""

        icon = {}

        icon[PB_PIXMAPSRC] = self.__src

        if self.__alt:
            icon[PB_PIXMAPALT] = self.__alt

        if self.__width:
            icon[PB_PIXMAPW] = str(self.__width)

        if self.__height:
            icon[PB_PIXMAPH] = str(self.__height)

        return icon

    def storeXML(self, ioHandle, level=0):

        # keeps track of tab level depth
        tab = ""
        tab += string.join(([" "] * level * 4), "")

        # start generating xml
        # start generating xml
        tmp_string = []
        if level == 0:
            ioHandle.write('<?xml version="1.0"?>\n')
            ioHandle.write("<!-- Creation date: %s -->\n" % strftime("%d.%m.%Y"))
        tmp_string.append(tab + "<Image")
        if self.title:
            tmp_string.append(' title="%s"' % self.title)
        if self.src:
            tmp_string.append(' src="%s"' % self.src)
        if self.pkg:
            tmp_string.append(' package="%s"' % self.pkg)
        if self.alt:
            tmp_string.append(' alt="%s"' % self.alt)
        if self.desc:
            tmp_string.append(' desc="%s"' % self.desc)
        if self.border:
            tmp_string.append(' border="%s"' % self.border)
        if self.width:
            tmp_string.append(' width="%s"' % self.width)
        if self.height:
            tmp_string.append(' height="%s"' % self.height)
        tmp_string.append("/>")
        ioHandle.write(string.join(tmp_string, "") + "\n")

    def getHtml(self, **args):
        """\brief Returns a html representation"""

        keys = args.keys()
        tag = ["<img "]

        if self.SRC not in keys and self.src:
            tag.append('src="%s"' % self.src)

        if self.ALT not in keys and self.alt:
            tag.append('alt="%s"' % self.alt)

        if self.TITLE not in keys and self.title:
            tag.append('title="%s"' % self.title)

        if self.BORDER not in keys and self.border is not None:
            tag.append('border="%s"' % self.border)

        if self.WIDTH not in keys and self.width:
            tag.append('width="%s"' % self.width)

        if self.HEIGHT not in keys and self.height:
            tag.append('height="%s"' % self.height)

        for key in args.keys():
            value = args.get(key)
            if value is not None:
                tag.append('%s="%s"' % (key, value))

        tag.append("/>")
        return " ".join(tag)
