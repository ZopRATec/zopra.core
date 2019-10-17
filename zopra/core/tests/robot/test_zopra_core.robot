*** Settings ***

Resource  keywords.robot

Suite Setup  Setup Suite
Suite Teardown  Teardown Suite

Test Teardown  Teardown Test

*** Variables ***
${ZOPRA_BASE} =  ${PLONE_URL}/zopra/app


*** Keywords ***

Setup Suite
    Open Test Browser
    Set Window Size  1024  768
    Enable Autologin As  ZopRAAdmin
    Reload Page

Teardown Suite
    Close All Browsers

Teardown Test
    Capture Page Screenshot

*** Test Cases ***

Test ZopRA Installation Is In Place
    Pause
    Go To  ${ZOPRA_BASE}
    Page Should Contain  css=h1.documentFirstHeading  Modules

Test ZopRA Test Manager Start Page
    Go To  ${ZOPRA_BASE}
    Click Link  css=a.button  Test
    Page Should Contain  css=h1.documentFirstHeading  Manager Overview