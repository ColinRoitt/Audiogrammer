# Audiogrammer
A Python app for making custom audiograms with built-in captioning engine

## Example Output
![Example Video](https://github.com/ColinRoitt/Audiogrammer/assets/9614541/a187337d-cba5-4007-b6fd-27d5914c3e11)

### UI
<img src="https://github.com/ColinRoitt/Audiogrammer/assets/9614541/7e41eaa4-b5aa-4da1-aa69-03976ffff2fb" height="800"/>
<img src="https://github.com/ColinRoitt/Audiogrammer/assets/9614541/c38d937e-8a87-45aa-9699-11baef874264" height="800"/>


## Setup

To get running:

1. Make sure ffmpeg and imagemagic are installed

Linux:
```
sudo apt install ffmpeg imagemagick
```
Mac:
```
brew install ffmpeg imagemagick
```

2. Install pip packages
```
pip install -r requirements.txt
```

3. Install speech-to-text model
```
wget https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip -O model/model_files.zip && unzip model/model_files.zip -d model && mv model/vosk-model-en-us-0.42-gigaspeech/* model/ && rm -r model/vosk-model-en-us-0.42-gigaspeech
```

3. Run the server

```
python app.py
```
