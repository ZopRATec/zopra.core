*** Settings ***

Documentation  zopra.core general robot keywords provides keywords for navigating a ZopRA installation as admin or editor

Library	 Collections
Library	 String

Resource  plone/app/robotframework/keywords.robot
Resource  plone/app/robotframework/selenium.robot

Library  Remote  ${PLONE_URL}/RobotRemote

*** Variables ***

${DEFAULT_LANG}  en

*** Keywords ***

#
# Setup / Teardown
#

# Suite setup to get ZOPRA_BASE global for every test
Setup Suite
    Open Test Browser
    Set Window Size  1024  768
    Enable Autologin As  ZopRAAdmin
    Reload Page
    ${ZOPRA_PATH} =  Get ZopRA Base Path
    ${ZOPRA_BASE} =  ${PLONE_URL}${}${ZOPRA_PATH}
    Set Suite Variable  ${ZOPRA_BASE}

Teardown Suite
    Close All Browsers

Teardown Test
    Capture Page Screenshot

#------------------------------------------------------------------------------
# ZopRA Navigation
#------------------------------------------------------------------------------

Go To Editorial
    [Documentation] Click the Editorial Link in the Navigation
    # TODO

Go To Manager Start Page
    [Documentation] Open the given url
    [Arguments]  ${manager_url}
    Go To URL  ${manager_url}

Go To Manager
    [Documentation] get the manager url and go there
    [Arguments]  ${manager_id}
    ${url} = Find Manager  ${manager_id}
    Go To Manager Start Page  ${url}

Table Default Options Are Visible
    [Documentation] Check the default Options List, Search and New on the Manager start page
    [Arguments]  ${table}
    Table Option Is Visible  ${table}  List
    Table Option Is Visible  ${table}  Search
    Table Option Is Visible  ${table}  New

Table Option Is Visible
    [Documentation] Check the named option that is visible in the table box on the Manager start page
    [Arguments]  ${table}  ${option}
    Page Should Contain Element  <sizzle me here>

Click On Table Option
    [Documentation] Click Option Link on Manager start page for the given Table
    [Arguments]  ${table}  ${option}
    Click  <sizzle me here>

Check Search Form
    [Documentation] Check we are landed on the desired Form
    # TODO

Check List
    [Documentation] Check we are landed on the search results page
    # TODO

Check Search Results
    [Documentation] Check we are landed on the search results page
    Check List

Check Search Result Count
    [Documentation] Check the count on the page
    [Arguments]  ${count}
    # TODO

Check Show Form
    [Documentation] Check we are landed on the Show Form
    # TODO

Check Edit Form
    [Documentation] Check we are landed on the Edit Form
    # TODO

Click Show Icon
    [Documentation] Click Icon on search results page to get to the Show Form
    # TODO
Click Edit Icon
    [Documentation] Click Icon on search results page to get to the Edit Form
    # TODO

Go To List Management Form
    [Documentation] List elements for simple lists (singlelist, multilist, hierarchylist) can be edited / entered via List Management Form
    # TODO

Enter Data Into Form
    [Documentation] Find the field with the given fieldname and input the value according to fieldtype. Use additional_value for multilist notes.
    [Arguments]  ${fieldname}  ${fieldtype}  ${value}  ${additional_value}
    # TODO switch fieldtypes and handle the selection / data input

# form field data manipulation

Set Text Field
    [Documentation]  Enter content into a given text field.
    [Arguments]  ${fieldname}  ${content}
    Page Should Contain Element  css=#archetypes-fieldname-${fieldname} input
    Input Text  ${fieldname}  ${content}

Set Selection Widget By Value
    [Documentation]  Select the option with value of a selection widget with fieldname
    [Arguments]  ${fieldname}  ${value}
    Select From List By Value  ${fieldname}  ${value}

Set Textarea Field
    [Documentation]  Enter content into a given textarea
    [Arguments]  ${fieldname}  ${content}
    Page Should Contain Element  css=#archetypes-fieldname-${fieldname} textarea
    Input Text  ${fieldname}  ${content}

Select Checkbox Field
    [Documentation]  Activate a Checkbox
    [Arguments]  ${fieldname}
    Page Should Contain Element  css=#archetypes-fieldname-${fieldname} input#${fieldname}
    Select Checkbox  ${fieldname}

