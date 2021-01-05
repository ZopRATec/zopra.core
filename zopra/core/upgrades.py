import logging


PROFILE_ID = 'profile-zopra.core:default'


def upgrade_skins(context, logger=None):
    """Method to convert float Price fields to string.

    When called from the import_various method, 'context' is
    the plone site and 'logger' is the portal_setup logger.

    But this method will be used as upgrade step, in which case 'context'
    will be portal_setup and 'logger' will be None."""

    if logger is None:
        # Called as upgrade step: define our own logger.
        logger = logging.getLogger('zopra.core')

    # Run the skins.xml step
    from plone import api
    setup = api.portal.get_tool('portal_setup')
    setup.runImportStepFromProfile(PROFILE_ID, 'skins')

    logger.info('Skins reimported.')
