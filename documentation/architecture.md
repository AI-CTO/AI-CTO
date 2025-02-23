### **Architecture description**

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
