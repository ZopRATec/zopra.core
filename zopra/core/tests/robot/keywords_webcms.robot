*** Settings ***

Documentation  Keywords for WebCMS integration

Library	 Collections
Library	 String

Resource  plone/app/robotframework/keywords.robot
Resource  plone/app/robotframework/selenium.robot

Library  Remote  ${PLONE_URL}/RobotRemote

# Content-specific Keywords
Resource  keywords_folder.robot
Resource  keywords_resourcefolders.robot

*** Variables ***


*** Keywords ***

Activate Language
    [Arguments]  ${language}
    Click Link  css=#portal-languageselector li.language-${language} a

Go To And Wait
    [Arguments]  ${url}
    Go To  ${url}
    Wait Until Location Is  ${url}

Log Out Autologin
    [Documentation]  Logging out after using Enable autologin as
    Disable Autologin
    Log Out

Information Should Contain Text
    [Documentation]  Check for a substring within info portal messages.
    [Arguments]  ${text}
    Page Should Contain Element  xpath=//dl[contains(@class, 'portalMessage') and contains(@class, 'info')]/dd[contains(text(), '${text}')]

Information Should Be Visible
    Page Should Contain Element  xpath=//dl[contains(@class, 'portalMessage') and contains(@class, 'info')]

Warning Should Contain Text
    [Documentation]  Check for a substring within info portal messages.
    [Arguments]  ${text}
    Page Should Contain Element  xpath=//dl[contains(@class, 'portalMessage') and contains(@class, 'warning')]/dd[contains(text(), '${text}')]

Warning Should Be Visible
    Page Should Contain Element  xpath=//dl[contains(@class, 'portalMessage') and contains(@class, 'warning')]

Error Should Contain Text
    [Documentation]  Check for a substring within info portal messages.
    [Arguments]  ${text}
    Page Should Contain Element  xpath=//dl[contains(@class, 'portalMessage') and contains(@class, 'error')]/dd[contains(text(), '${text}')]

Error Should Be Visible
    Page Should Contain Element  xpath=//dl[contains(@class, 'portalMessage') and contains(@class, 'error')]

Field Error For "${field}" Should Be Visible
    Element Should Be Visible  css=#archetypes-fieldname-${field} .fieldErrorBox

Field Error Message Should Be
    [Arguments]  ${field}  ${message}
    Wait Until Element Contains  css=#archetypes-fieldname-${field} .fieldErrorBox  ${message}

Activate Ajax Validation
    [Arguments]  ${language}  ${field}
    # press tab-key on the field to activate validation
    Press Key  css=#archetypes-fieldname-${field} #${field}___${language}___  \\09

Activate Ajax Validation And Check Error Message
    [Documentation]  Ajax Validation Is Activated When the Focus shifts from the element to another, sometimes fails to activate
    [Arguments]  ${language}  ${field}  ${message}
    # press tab-key on the field and change Focus to activate validation via AJAX
    Log  Activate ajax validation. This sometimes fails to activate, so retry.
    Capture Page Screenshot
    ${fieldname} =  Run Keyword If  '${language}' != ''  Catenate  ${field}___${language}___
    ...                                    ELSE  Catenate  ${field}
    FOR  ${try}  IN RANGE  1  5
        Wait Until Page Contains Element  css=#archetypes-fieldname-${field} #${fieldname}
        Click Element  css=#archetypes-fieldname-${field} #${fieldname}
        Set Focus To Element  css=#archetypes-fieldname-${field} #${fieldname}
        Press Key  css=#archetypes-fieldname-${field} #${fieldname}  \\09
        Set Focus To Element  form.button.save
        ${success} =  Run Keyword And Return Status  Wait Until Element Contains  css=#archetypes-fieldname-${field} .fieldErrorBox  ${message}  5s
        Run Keyword If  ${success}  Exit For Loop
    END
    Run Keyword If  not ${success}  Capture Page Screenshot
    Should Be True  ${success}  Ajax validation for ${fieldname} failed. Message should have contained: ${message}

Wait For Ajax Validation
    Wait Until Keyword Succeeds  2 min  1 sec  Element Should Not Be Visible  ajax-spinner
