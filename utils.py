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

def isPost(request):
    return request.method == 'POST'

def isGet(request):
    return request.method == 'GET'

def isFileSentAndAllowed(request, allowed_extensions):
    if 'file' not in request.files:
        print('No file part')
        return False
    file = request.files['file']
    if file.filename == '':
        print('No selected file')
        return False
    if not allowed_file(file.filename, allowed_extensions):
        print('Invalid file type')
        return False
    return True

def convert_to_wav(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    audio.export(output_path, format='wav')
    return output_path

def generate_subtitles(audio_path):

    audio = whisper.load_audio(audio_path)
    model = whisper.load_model("base")
    result = whisper.transcribe(model, audio, language="en", verbose=True)

    # convert to subtitles
    subtitles = []
    for i, segment in enumerate(result['segments']):
        start, end = segment['start'], segment['end']
        subtitles.append((round(start, 1), round(end, 1), segment['text'].strip()))

    # subtitles = [(0.0, 8.62, "I tell you what I really want, it's one of e but the spice girls."), (13.66, 17.3, "It's LaRou with Bulletproof still to come as well."), (22.0, 24.98, 'And an epic take that with all the worlds.'), (25.62, 26.2, 'On air.'), (26.38, 26.88, 'Online.'), (27.3, 27.82, 'On tap.'), (28.8, 30.6, 'It looks official studio radio station.')]

    print(subtitles)
    return subtitles

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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

    final_video.write_videofile(output_path, fps=fps, logger=None)