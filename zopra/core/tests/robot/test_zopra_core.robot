*** Settings ***

Resource  keywords.robot

Suite Setup  Setup Suite
Suite Teardown  Teardown Suite

Test Teardown  Teardown Test

*** Variables ***



*** Keywords ***


*** Test Cases ***

Test ZopRA Installation Is In Place
    Go To  ${ZOPRA_BASE}
    Wait Until Page Contains  Modules

Test ZopRA Test Manager Start Page
    Go To  ${ZOPRA_BASE}
    Click Link  sizzle=a.button:contains('Test')
    Wait Until Page Contains  Manager Overview