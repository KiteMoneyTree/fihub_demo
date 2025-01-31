# Use an official Python runtime as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .


# Install the project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project code into the container
COPY . .

# Set environment variables, if needed
# ENV VARIABLE_NAME value

# Expose the port that the Django app will run on
EXPOSE 8000

# Define the command to run the Django app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]