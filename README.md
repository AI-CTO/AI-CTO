# AI-CTO

# AI Project Portfolio Visualization Tool
![GHA workflow badge](https://github.com/modaralgayal/AI-CTO/workflows/CI/badge.svg)

## Description
This project focuses on developing a web-based tool that provides a comprehensive and visually appealing view of the company's AI features, projects, and project ideas. The tool enables decision-makers to strategically evaluate and prioritize projects using visual analytics. 

### Key Features:
- **Visual Analytics:** Projects are visualized on a two-dimensional axis:
  - **Y-axis:** Customer-perceived novelty value.
  - **X-axis:** Business model and service delivery novelty value.
- **Modular Design:** Ensures flexibility for future extensions and integration of additional backend components.
- **AI-Enhanced Backend:** Optionally leverages the latest AI technologies, such as large language models, to enhance project evaluation capabilities.  


# Links:

- [Product Backlog](https://docs.google.com/spreadsheets/d/1TU4pviN2y0U6E9rLPYMDoz6TYgi0V0dnNJn4ZTuhK0A/edit?gid=0#gid=0)

- [Sprint Backlog](https://github.com/users/ErikHuuskonen/projects/1)

- [Documentation](https://github.com/AI-CTO/AI-CTO/tree/release/documentation)


# Definition of Done:

## User Story Implementation
- The **user story** and its **acceptance criteria** have been fully implemented and meet the agreed requirements.

## Testing and Quality Assurance
- **Unit tests** are complete, with at least 90% code coverage, and all tests pass successfully.
- **End-to-End (E2E tests)**, including **robot tests**, are complete and pass successfully.
- **Integration tests** validate the interactions between components and pass successfully.
- The code passes the **CI/CD pipeline** in **GitHub Actions**, including:
  - Unit testing
  - End-to-End testing
  - Linting (e.g., `pylint`, `flake8`)
  - Dependency checks
- **Test Traceability**:
  - Each **user story** has corresponding, well-documented **tests** (e.g., unit, integration, E2E).
  - A **link to the relevant tests** for each user story is added to the **product backlog** or task description to ensure traceability and easy reference.

## Code Review
- A thorough **code review** has been completed, and all identified issues have been resolved.

## Dependency Management
- All project dependencies are managed using **Poetry**.
- The `pyproject.toml` file is up-to-date and reflects the current project configuration.

## Documentation
- All relevant documentation is updated, including:
  - API documentation (e.g., using **Swagger** or **OpenAPI**).
  - Developer setup guides.
  - Explanation of test cases and how to run them.
  - Details of the CI/CD pipeline and deployment process.

## Task and Process Management
- Tasks related to the story are updated and marked as complete in **GitHub Projects** or another task management tool.
- The **user story** is reviewed and accepted by the **Product Owner** during the sprint review.

## Client Approval
- The **final draft** of the deliverable is reviewed and approved by the client.
- Any feedback provided by the client has been addressed.

## Optional Enhancements
- **Performance Testing**: Ensure the system meets performance benchmarks, especially for AI and API endpoints.
- **Security Testing**: Validate the system for vulnerabilities (e.g., penetration testing or dependency vulnerability scans).
- **Reproducibility**: Verify that the environment can be reliably set up using the provided documentation and tools.
