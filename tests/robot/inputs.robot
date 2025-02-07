*** Settings ***
Resource    resource.robot

*** Test Cases ***

User can input text to text-input field 
    Open And Configure Browser
    Go To    ${HOME_URL}
    Page Should Contain  Project Portfolio Visualization Tool
    Input Text    id=description    AirBNB for humans and cats
    Click Button   css:button[type="submit"]
    Sleep    10
    Page Should Contain    Project Name: AirBNB for humans and cats