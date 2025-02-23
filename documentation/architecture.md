# **Architecture description**

#### Structure

The architecture of this application follows the Model-View-Controller (MVC) pattern with additional service and utility layers. The **Model** represents the core business logic and data handling, with components such as `models.py` and `db_utils.py` to manage data interactions. The **View** layer includes the HTML templates and static assets like CSS and JavaScript to render the UI. The **Controller** manages application routes, defined in `routes.py`, that connect user input to the appropriate business logic. 

In addition to the core MVC structure, the application integrates external services, such as OpenAI and Bokeh, for AI processing and data visualization. The **Utilities** layer provides auxiliary functions like API testing. This modular architecture ensures the separation of concerns, making the application more maintainable and scalable.




```mermaid

graph TD
  subgraph Model
    A[models.py]
    B[db_utils.py]
  end

  subgraph View
    C[Templates]
    D[static/styles.css]
    E[static/tab_script.js]
  end

  subgraph Controller
    F[routes.py]
  end

  subgraph Services
    G[openai_service.py]
    H[bokeh_visualization.py]
  end

  subgraph Utilities
    I[test_api_assist.py]
  end

  %% Dependencies
  F --> A
  F --> B
  F --> C
  F --> G
  F --> H

  A --> B

  %% Highlight redundancy
  style I fill:#e0f7fa,stroke:#00bcd4,stroke-width:2px


```
#### User Interface

The application provides several user interface views, each serving a distinct purpose in the system. The UI is composed of five main templates:

1. **index.html** – The main landing page of the application. This template contains a text input field, allowing the user to type, submit, and fine-tune a business idea. 
   
2. **previous_projects.html** – A page that displays a list of previous projects. It includes an option to edit individual projects.

3. **update_project.html** – A form or interface for updating existing project information. This template allows users to modify details about a project to iteratively enhance assessment scores.

4. **visualization.html** – A page dedicated to visualizing projects on scatter plots. 

Each template is designed to allow seamless user interactions, with navigation elements provided via `layout.html` and content-specific functionality managed through the other templates. The user interface is clean and modular, ensuring an efficient and user-friendly experience across all pages.



