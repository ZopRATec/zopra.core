# Make the ZopRAAuthor role show up on the Sharing tab
class ZopRAAuthorRoleDelegation(object):
    title = (u"ZopRA Author")
    required_permission = "Manage portal"

# Make the ZopRAReviewer role show up on the Sharing tab
class ZopRAReviewerRoleDelegation(object):
    title = (u"ZopRA Reviewer")
    required_permission = "Manage portal"

# Make the ZopRAAdmin role show up on the Sharing tab
class ZopRAAdminRoleDelegation(object):
    title = (u"ZopRA Admin")
    required_permission = "Manage portal"
