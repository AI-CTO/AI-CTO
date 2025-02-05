*** Settings ***
Resource    resource.robot

*** Test Cases ***
Testaa Etusivu
    Open And Configure Browser
    

User can see main page
    Open And Configure Browser
    Go To    ${HOME_URL}
    Page Should Contain  AI Project Portfolio Visualization Tool

User can see Visualization page
    Open And Configure Browser
    Go To      ${HOME_URL}
    Click Element    //li[@data-tab="visualization"]
    Page Should Contain    Visualization

User can see My Projects page
    Open And Configure Browser
    Go To   ${HOME_URL}
    Click Element    //li[@data-tab="projects"]
    Page Should Contain   My Projects

User can go back to Home page
    Open And Configure Browser
    Go To   ${HOME_URL}
    Click Element    //li[@data-tab="projects"]
    Page Should Contain   My Projects
    Click Element    //li[@data-tab="home"]
    Page Should Contain   Enter your project idea here: