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
