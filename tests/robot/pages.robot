*** Settings ***
Resource    resource.robot

*** Test Cases ***
Test Home Page
    Open And Configure Browser
    Go To    ${HOME_URL}
    Page Should Contain    Welcome to the AI Project Portfolio Visualization Tool. Describe your project idea or upload a PDF to get started.
    
User can see main page
    Open And Configure Browser
    Go To    ${HOME_URL}
    Page Should Contain   Welcome to the AI Project Portfolio Visualization Tool. Describe your project idea or upload a PDF to get started.

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
    resource.Close Browser