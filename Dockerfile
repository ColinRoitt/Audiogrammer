# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install ffmpeg and imagemagick
RUN apt-get update && \
    apt-get install -y ffmpeg imagemagick && \
    rm -rf /var/lib/apt/lists/*

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download and set up the speech-to-text model
RUN mkdir -p /app/model && \
    wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip -O /app/model/model_files.zip && \
    unzip /app/model/model_files.zip -d /app/model && \
    mv /app/model/vosk-model-en-us-0.42-gigaspeech/* /app/model/ && \
    rm -r /app/model/vosk-model-en-us-0.42-gigaspeech && \
    rm /app/model/model_files.zip

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]
