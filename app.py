# Things you must do before running this code:
# 1. Install the required packages: flask, pydub, moviepy, matplotlib, numpy, SpeechRecognition
# also install whisper timestamped: pip install -U git+https://github.com/linto-ai/whisper-timestamped
# 2. Install ffmpeg: sudo apt-get install ffmpeg
# 3. Install imagemagick: sudo apt-get install imagemagick
# or on mac: brew install ffmpeg imagemagick

import os
from flask import Flask, json, request, redirect, url_for, send_from_directory, render_template, session
from werkzeug.utils import secure_filename
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
from pydub import AudioSegment
from moviepy.editor import VideoClip, AudioFileClip, CompositeVideoClip, ImageClip, vfx
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.io.bindings import mplfig_to_npimage
import whisper_timestamped as whisper

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'adn389ahdehj'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def convert_to_wav(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format='wav')
    return output_path

def generate_subtitles(audio_path):

    audio = whisper.load_audio(audio_path)
    model = whisper.load_model("base")
    result = whisper.transcribe(model, audio, language="en")

    # convert to subtitles
    subtitles = []
    for i, segment in enumerate(result['segments']):
        start, end = segment['start'], segment['end']
        subtitles.append((round(start, 1), round(end, 1), segment['text'].strip()))

    # subtitles = [(0.0, 8.62, "I tell you what I really want, it's one of e but the spice girls."), (13.66, 17.3, "It's LaRou with Bulletproof still to come as well."), (22.0, 24.98, 'And an epic take that with all the worlds.'), (25.62, 26.2, 'On air.'), (26.38, 26.88, 'Online.'), (27.3, 27.82, 'On tap.'), (28.8, 30.6, 'It looks official studio radio station.')]

    print(subtitles)
    return subtitles

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def complimentary_color(foreground_color):
    # calculate best contrassting colour to key from foreground color
    foreground_color = foreground_color.lstrip('#')
    rgb = tuple(int(foreground_color[i:i+2], 16) for i in (0, 2, 4))
    r, g, b = rgb
    yiq = ((r*299)+(g*587)+(b*114))/1000
    return '#000000' if yiq >= 128 else '#ffffff'

def make_frame(t, frame_rate, fps, samples, foreground_color, background_color):
    samples_per_frame = int(frame_rate / fps)
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor(background_color)
    start_sample = int(t * frame_rate)
    end_sample = start_sample + samples_per_frame
    if end_sample > len(samples):
        end_sample = len(samples)
    if start_sample >= len(samples):
        start_sample = len(samples) - samples_per_frame

    slc = range(start_sample, end_sample, 10)

    typ = 'fill'

    if typ == 'line':
        # plot as line
        ax.plot(samples[slc], color=foreground_color, linewidth=2)
    
    if typ == 'bar':
        # plot as bars
        ax.bar(range(len(samples[slc])), samples[slc], color=foreground_color)
        inverted = samples[slc] * -1
        ax.bar(range(len(inverted)), inverted, color=foreground_color)

    if typ == 'fill':
        # plot as filled area of just values below the 0 line
        ax.fill_between(range(len(samples[slc])), samples[slc], color=foreground_color)
        inverted_samples = samples[slc] * -1
        ax.fill_between(range(len(inverted_samples)), inverted_samples, color=foreground_color)


    ax.set_ylim(-5, 5)
    ax.set_xlim(0, len(samples[slc]))
    ax.axis('off')
    # remove padding around the figure
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.close(fig)
    out_frame = mplfig_to_npimage(fig)
    return out_frame

def create_waveform_video_with_subtitles(input_path, output_path, subtitles, video_settings):
    audio = AudioSegment.from_file(input_path)
    samples = np.array(audio.get_array_of_samples())
    frame_rate = audio.frame_rate
    channels = audio.channels 
    output_size = (1000, 1000)

    print(video_settings)

    wave_position = video_settings['wave_position']
    wave_color = video_settings['wave_color']
    background_wave_color = complimentary_color(wave_color)
    print("🚀 ~ background_wave_color:", background_wave_color)
    # TOOD: Make video settings render in the video etc and TESTTT
    caption_position = video_settings['caption_position']
    caption_color = video_settings['caption_color']
    bg_image = video_settings['bg_image']
    # remove leading /
    bg_image = bg_image[1:]

    if channels == 2:
        samples = samples.reshape((-1, 2))
        samples = samples.mean(axis=1)

    samples = samples / np.max(np.abs(samples))
    duration = len(samples) / frame_rate
    fps = 30

    audio_clip = AudioFileClip(input_path)

    # greate background video clip from image
    clip = ImageClip(bg_image, duration=duration)

    waveform_clip = VideoClip(lambda t: make_frame(t, frame_rate, fps, samples, wave_color, background_wave_color), duration=duration)
    wave_position_mapped_to_middle = int(wave_position) - output_size[0]//2
    waveform_clip = waveform_clip.set_position((0, wave_position_mapped_to_middle))
    # mask colour white from the waveform
    # color to array 
    background_wave_color_arr = [int(background_wave_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)]
    waveform_clip = vfx.mask_color(waveform_clip, color=background_wave_color_arr, thr=100, s=2)

    wavform_background_clip = CompositeVideoClip([clip, waveform_clip], size=output_size)

    # Create subtitles
    generator = lambda txt: TextClip(txt, font='Arial', fontsize=38, color=caption_color, method='caption', size=output_size)
    subs = [((start, end), txt) for (start, end, txt) in subtitles]
    subtitles_clip = SubtitlesClip(subs, generator)
    # origin in middle of the screen???
    subtitle_position_mapped_to_middle = int(caption_position) - output_size[0]//2
    print(subtitle_position_mapped_to_middle)
    subtitles_clip = subtitles_clip.set_position((0, subtitle_position_mapped_to_middle))

    final_video = CompositeVideoClip([wavform_background_clip, subtitles_clip], size=output_size)
    final_video = final_video.set_audio(audio_clip)

    final_video.write_videofile(output_path, fps=fps)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    bg_img = url_for('static', filename='assets/withImage.png')

    if request.method == 'POST':
        if 'file' not in request.files:
            print('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            print('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            print('file uploaded')
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print(file_path)
            try:
                file.save(file_path)
            except FileNotFoundError:
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(file_path)
                
            video_filename = filename + '.mp4'
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], video_filename)

            video_settings = {
                'wave_position': request.form.get('wave_position'),
                'wave_color': request.form.get('wave_color'),
                'caption_position': request.form.get('caption_position'),
                'caption_color': request.form.get('caption_color'),
                'bg_image': bg_img
            }

            # save bg_image
            # custom_bg = request.form.get('custom_bg')
            if 'custom_bg' in request.files:
                custom_bg = request.files["custom_bg"]
                bg_filename = secure_filename(custom_bg.filename)
                bg_image_path = os.path.join(app.config['UPLOAD_FOLDER'], bg_filename)
                custom_bg.save(bg_image_path)
                video_settings['bg_image'] = bg_image_path
                print('bg_image saved')

            print(video_settings)

            subtitles = generate_subtitles(file_path)
            # redirect to edit subtitles
            session['video_settings'] = video_settings
            session['file_path'] = file_path
            session['output_path'] = output_path
            session['filename'] = filename
            session['video_filename'] = video_filename
            session['subtitles'] = subtitles
            return redirect(url_for('edit_subtitles'))
        
    return render_template('index.html', bg_img=bg_img)

@app.route('/edit-subtitles', methods=['GET', 'POST'])
def edit_subtitles():
    if request.method == 'POST':
        subtitles = request.json
        subtitles = [(segment['start'], segment['end'], segment['text']) for segment in subtitles]
        session['subtitles'] = subtitles
        print(subtitles)

        file_path = session['file_path']
        output_path = session['output_path']
        video_filename = session['video_filename']
        video_settings = session['video_settings']
        create_waveform_video_with_subtitles(file_path, output_path, subtitles, video_settings)
        print("redirecting to: ", url_for('uploaded_file', filename=video_filename))
        return redirect(url_for('uploaded_file', filename=video_filename))
    
    subtitles = session['subtitles']
    subtitles = [{'start': start, 'end': end, 'text': text} for start, end, text in subtitles]
    audio_url = url_for('uploaded_file', filename=session['filename']+ '.wav')
    # return render_template('subtitle-editor-dragdrop.html', subtitles=subtitles, audio_url=audio_url)
    return render_template('subtitle-editor.html', subtitles=subtitles, audio_url=audio_url)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # video = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    # video = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    # return render_template('view.html', video=filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    


if __name__ == "__main__":
    app.run(debug=True, port=5001)
