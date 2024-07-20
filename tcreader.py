import streamlit as st
import ffmpeg
import re
import tempfile

def seconds_to_timecode(seconds, frame_rate=23.976):
    """Converts a duration in seconds to a timecode `HH:MM:SS:FF`."""
    total_frames = round(seconds * frame_rate)
    frames = total_frames % round(frame_rate)
    total_seconds = total_frames // round(frame_rate)
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    return f"{hours:02}:{minutes:02}:{secs:02}:{frames:02}"

def get_sample_rate(metadata):
    """Gets the sample rate of the file."""
    for stream in metadata.get('streams', []):
        if 'sample_rate' in stream:
            return int(stream['sample_rate'])
    return 48000  # Default value if not found

def get_time_reference(metadata):
    """Gets the time reference of the file."""
    if 'format' in metadata and 'tags' in metadata['format'] and 'time_reference' in metadata['format']['tags']:
        return int(metadata['format']['tags']['time_reference'])
    for stream in metadata.get('streams', []):
        if 'tags' in stream and 'time_reference' in stream['tags']:
            return int(stream['tags']['time_reference'])
    return 0

def get_frame_rate(metadata):
    """Gets the frame rate from the file metadata."""
    for stream in metadata.get('streams', []):
        if 'r_frame_rate' in stream:
            r_frame_rate_str = stream['r_frame_rate']
            numerator, denominator = map(int, r_frame_rate_str.split('/'))
            return numerator / denominator
    return 23.976  # Default value if not found

def get_timecode(metadata):
    """Gets the initial timecode from the file metadata."""
    if 'format' in metadata and 'tags' in metadata['format'] and 'timecode' in metadata['format']['tags']:
        return metadata['format']['tags']['timecode']
    for stream in metadata.get('streams', []):
        if 'tags' in stream and 'timecode' in stream['tags']:
            return stream['tags']['timecode']
    return "00:00:00:00"

def timecode_to_seconds(timecode, frame_rate):
    """Converts a timecode in format `HH:MM:SS:FF` to seconds."""
    match = re.match(r'(\d{2}):(\d{2}):(\d{2}):(\d{2})', timecode)
    if not match:
        return 0
    hours, minutes, seconds, frames = map(int, match.groups())
    total_seconds = hours * 3600 + minutes * 60 + seconds + frames / frame_rate
    return total_seconds

def add_timecodes(tc1, tc2):
    """Adds two timecodes with a frame rate of 24 fps."""
    frame_rate = 24
    seconds1 = timecode_to_seconds(tc1, frame_rate)
    seconds2 = timecode_to_seconds(tc2, frame_rate)
    total_seconds = seconds1 + seconds2
    return seconds_to_timecode(total_seconds, frame_rate)

def process_metadata(file_paths, file_type):
    result_message = ""
    for file_path in file_paths:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_path.read())
            temp_file_path = temp_file.name
        
        metadata = ffmpeg.probe(temp_file_path)
        if file_type == 'audio':
            sample_rate = get_sample_rate(metadata)
            time_reference = get_time_reference(metadata)
            start_seconds = time_reference / sample_rate
            start_timecode = seconds_to_timecode(start_seconds, 23.976)
            result_message += (f"Audio Results ({file_path.name}):\n"
                               f"Time Reference: {time_reference}\n"
                               f"Sample Rate: {sample_rate}\n"
                               f"Start Timecode: {start_timecode}\n\n")
        elif file_type == 'video':
            frame_rate = get_frame_rate(metadata)
            start_timecode = get_timecode(metadata)
            duration = float(metadata['format']['duration'])
            duration_timecode = seconds_to_timecode(duration, frame_rate)
            end_timecode = add_timecodes(start_timecode, duration_timecode)
            result_message += (f"Video Results ({file_path.name}):\n"
                               f"Start Timecode: {start_timecode}\n"
                               f"End Timecode: {end_timecode}\n"
                               f"Duration in Timecode Format: {duration_timecode}\n\n")
    return result_message

def display_footer():
    footer = """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: white;
        color: black;
        text-align: center;
        padding: 10px;
        border-top: 1px solid #eaeaea;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .footer .logo {
        height: 60px; /* Increased size */
        margin-right: 20px;
    }
    .footer .separator {
        border-left: 2px solid #eaeaea;
        height: 120px;
        margin-right: 20px;
    }
    </style>
    <div class="footer">
        <img class="logo" src="http://vicherrera.net/wp-content/uploads/2023/05/VicHerrera_Logo.svg" alt="Vic Herrera Logo">
        <div class="separator"></div>
        <div>
            <p>Developed by Vic Herrera | <a href="https://vicherrera.net" target="_blank">Vic Herrera</a> | <a href="https://datawava.com" target="_blank">datawava</a></p>
            <p>© Version 1.2  - July, 2024</p>
        </div>
    </div>
    """
    st.markdown(footer, unsafe_allow_html=True)

def main():
    st.title("Timecode Reader")

    # File uploader for audio files
    audio_files = st.file_uploader("Select Audio Files", type=["wav"], accept_multiple_files=True)
    # File uploader for video files
    video_files = st.file_uploader("Select Video Files", type=["mp4", "mov", "avi", "mxf"], accept_multiple_files=True)

    # Button to process metadata
    if st.button("Process Metadata"):
        if audio_files:
            audio_results = process_metadata(audio_files, 'audio')
            st.text_area("Audio Results", value=audio_results, height=200)
        
        if video_files:
            video_results = process_metadata(video_files, 'video')
            st.text_area("Video Results", value=video_results, height=200)

    # Display footer
    display_footer()

if __name__ == "__main__":
    main()