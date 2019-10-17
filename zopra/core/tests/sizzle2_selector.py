"""A Library to introduce the sizzle2 selector.
"""

import re
from robot.libraries.BuiltIn import BuiltIn


class Sizzle2Selector:
    """A Library to introduce the sizzle2 selector.
    """
    ROBOT_LIBRARY_SCOPE = 'TEST SUITE'
    ROBOT_LIBRARY_VERSION = 1.0

    sizzle_exactly_contains = re.compile(
        r"""(?P<stuff_before>.*)\:text-equals\(["'](?P<text>.*)["']\).*(?P<stuff_after>.*)""")

    @property
    def _current_browser(self):
        """Gets the current browser
        :return:
        """
        seleniumlib = BuiltIn().get_library_instance('Selenium2Library')
        return seleniumlib._current_browser()

    def sizzle2_locator_strategy(self, browser, criteria, tag, constraints):
        """Strategy for enriched sizzle selectors. It now supports queries with the new pseudo-class :text-equals()

        e.g. Get Element  sizzle2=div span:text-equals('Hello World')

        It does not support multiple usages of the new pseudo-class.

        :param browser: 
        :param criteria: 
        :param tag:
        :param constraints: 
        :return: 
        """
        seleniumlib = BuiltIn().get_library_instance('Selenium2Library')
        match = self.sizzle_exactly_contains.match(criteria)
        if not match:  # ordinary sizzle selector...
            return seleniumlib._element_finder.find(locator="sizzle=" + criteria, first_only=False, required=False)

        d = dict((k, v.replace("'", "\\'")) for k, v in match.groupdict().items())
        # XXX: ignores 'stuff_after'...
        js = "return jQuery('{stuff_before}').filter(function() {{ return $(this).text().trim() == '{text}' }}).get();".format(
            **d)
        return seleniumlib._element_finder._filter_elements(
            browser.execute_script(js),
            tag, constraints)

