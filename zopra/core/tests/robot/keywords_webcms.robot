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
