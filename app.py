import os
from flask import Flask, json, request, redirect, url_for, send_from_directory, render_template, session
from werkzeug.utils import secure_filename
from utils import create_waveform_video_with_subtitles, generate_subtitles, allowed_file, isPost, isFileSentAndAllowed

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3'}
DEFAULT_BG_IMG = 'assets/withImage.png'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'adn389ahdehj'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    bg_img = url_for('static', filename=DEFAULT_BG_IMG)
    return render_template('index.html', bg_img=bg_img)

@app.route('/upload', methods=['POST'])
def upload_file():
    if not isPost(request):
        return redirect(url_for('/'))
    if not isFileSentAndAllowed(request, ALLOWED_EXTENSIONS):
        return redirect(url_for('/'))

    file = request.files['file']
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
        'bg_image': url_for('static', filename=DEFAULT_BG_IMG)
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

@app.route('/edit-subtitles', methods=['GET', 'POST'])
def edit_subtitles():
    if isPost(request):
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
    # read docker env variable deployment type
    deployment_type = os.getenv('DEPLOYMENT_TYPE', 'development')
    if deployment_type == 'production':
        print('Running in production mode')
        app.run(debug=False, host='0.0.0.0', port=5000)
    else:
        print('Running in development mode')
        app.run(debug=True, port=5000)
