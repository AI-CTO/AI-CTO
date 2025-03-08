# Use an official Python runtime as a parent image
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-root

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable (edited)
ENV FLASK_APP=app.py # change to src/app.py when the branch gets refactored

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]
