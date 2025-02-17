*** Settings ***
Resource    resource.robot

*** Test Cases ***
Test Home Page
    Open And Configure Browser
    Go To    ${HOME_URL}
    Page Should Contain    AICTO: Project Portfolio Visualization Tool
    
User can see main page
    Open And Configure Browser
    Go To    ${HOME_URL}
    Page Should Contain  AICTO: Project Portfolio Visualization Tool

User can see Visualization page
    Open And Configure Browser
    Go To    ${HOME_URL}
    Click Element    //a[text()='Visualization']
    Page Should Contain    Visualization

User can see My Projects page
    Open And Configure Browser
    Go To    ${HOME_URL}
    Click Element    //a[text()='Previous Projects']
    Page Should Contain    Previous Projects

User can go back to Home page
    Open And Configure Browser
    Go To    ${HOME_URL}
    Click Element    //a[text()='Previous Projects']
    Page Should Contain    Previous Projects
    Click Element    //a[text()='Home']
    Page Should Contain    AI Project Portfolio Visualization Tool
    Close Browser