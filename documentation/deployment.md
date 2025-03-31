# Deploying the AI-CTO Application as a Container in OpenShift

This document explains how the AI-CTO application is deployed as a container in OpenShift using GitHub Actions and Github Container Registry.

## Prerequisites
1. **OpenShift Cluster**: You need an access to an OpenShift cluster.
2. **Secrets Configuration**: Add the following secrets to your GitHub repository:
   - `OPENSHIFT_SERVER`: The OpenShift server URL.
   - `OPENSHIFT_TOKEN`: The token for authenticating with OpenShift.
   - `OPENAI_API_KEY`: The API key for OpenAI integration.
   - `SQLALCHEMY_DATABASE_URI`: The database connection string.

## Required Files
1. **`Dockerfile`**: Defines how the application is containerized. It includes:
   - Setting up the Python environment.
   - Installing dependencies using Poetry.
   - Exposing port `5000` for the Flask application.
   - Running the app using `flask run`.

   File: [`Dockerfile`](./Dockerfile)

2. **GitHub Actions Workflow**: Automates the build and deployment process. The workflow:
   - Builds the container image using the `Dockerfile`.
   - Pushes the image to the GitHub Container Registry.
   - Logs into the OpenShift cluster.
   - Deploys the application and exposes it to the internet.

   File: [`.github/workflows/openshift.yml`](./.github/workflows/openshift.yml)

## Deployment Steps
1. **Set Up the Workflow**:
   - The workflow is defined in [`.github/workflows/openshift.yml`](./.github/workflows/openshift.yml).
   - It uses actions like `buildah-build`, `push-to-registry`, and `oc-new-app` to build, push, and deploy the container.

2. **Trigger the Workflow**:
   - The workflow runs on a push to the `release` branch or can be triggered manually via `workflow_dispatch`.

3. **Build and Push the Image**:
   - The `Dockerfile` is used to build the container image.
   - The image is pushed to the GitHub Container Registry (GHCR).

4. **Log in to OpenShift**:
   - The workflow logs into the OpenShift cluster using the `OPENSHIFT_SERVER` and `OPENSHIFT_TOKEN` secrets.

5. **Deploy the Application**:
   - The `oc-new-app` action creates a deployment, service, and route for the application.
   - The application is exposed to the internet, and an HTTPS route is configured.

6. **Access the Application**:
   - The workflow prints the application URL after deployment. You can access the app using this URL.

