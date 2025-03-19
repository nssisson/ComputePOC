# Use an official Python runtime as a parent image
FROM python:3.13.2-slim-bookworm

# Set the working directory in the container
WORKDIR /src

# Copy the requirements file into the container
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files into the container
COPY . .

# Define the command to run your application
# Replace "your_script.py" with the actual name of your main Python script
CMD ["python", "Transform_Load_FREDBIGTABLE.py"]