# Use an official Python runtime as a parent image
FROM python:3.9-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg and imagemagick
RUN apt-get update && \
    apt-get install -y ffmpeg imagemagick && \
    rm -rf /var/lib/apt/lists/*

# Download and set up the speech-to-text model
RUN wget -nv https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip -O /app/model/model_files.zip
RUN unzip /app/model/model_files.zip -d /app/model
RUN mv /app/model/vosk-model-en-us-0.42-gigaspeech/* /app/model/

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches
CMD ["python", "app.py"]
