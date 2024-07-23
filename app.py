import streamlit as st
import requests
import os

# Streamlit app title
st.title("Audio Transcription and Diarization App")

# Colab URL input
colab_url = st.text_input("Enter the Colab backend URL:")

# Display the entered URL
if colab_url:
    st.write(f"Entered URL: {colab_url}")

# File uploader
uploaded_file = st.file_uploader("Choose an audio file", type=['mp3', 'm4a'])

def process_audio(uploaded_file, colab_url):
    files = {'audio': (uploaded_file.name, uploaded_file, uploaded_file.type)}
    try:
        with requests.post(colab_url, files=files, stream=True, timeout=3600) as response:  # 1-hour timeout
            response.raise_for_status()
            transcript = ""
            progress_placeholder = st.empty()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("FINAL_TRANSCRIPT:"):
                        transcript = decoded_line[len("FINAL_TRANSCRIPT:"):]
                        progress_placeholder.text("Processing complete!")
                    else:
                        progress_placeholder.text(decoded_line)
            return transcript
    except requests.exceptions.RequestException as e:
        st.error(f"An error occurred while connecting to the backend: {str(e)}")
        return None

if uploaded_file is not None and colab_url:
    # Display file details
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
    st.write(file_details)

    # Transcription and diarization
    if st.button("Transcribe and Diarize"):
        st.info("Processing audio... This may take a few minutes.")
        
        try:
            # Test connection to backend
            st.write("Testing connection to backend...")
            test_response = requests.get(colab_url, timeout=10)  # 10-second timeout for the test
            st.write(f"Backend connection test status code: {test_response.status_code}")
            st.write(f"Backend connection test response: {test_response.text}")
            
            # Process audio file
            st.write("Sending file to backend for processing...")
            transcript = process_audio(uploaded_file, colab_url)
            
            if transcript:
                if transcript.strip() == "":
                    st.error("Received an empty transcript from the backend.")
                else:
                    st.subheader("Transcription with Speaker Diarization:")
                    st.text_area("", transcript, height=300)

                # Option to download the transcript
                st.download_button(
                    label="Download Transcript",
                    data=transcript,
                    file_name="transcript.txt",
                    mime="text/plain"
                )
            else:
                st.error("An error occurred during processing. No transcript was returned.")
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred while connecting to the backend: {str(e)}")
else:
    st.warning("Please enter the Colab backend URL and upload an audio file.")

# Instructions and additional information
st.sidebar.header("Instructions")
st.sidebar.info(
    "1. Enter the Colab backend URL.\n"
    "2. Upload an MP3 or M4A audio file.\n"
    "3. Click 'Transcribe and Diarize' to process the audio.\n"
    "4. View the transcription with speaker labels.\n"
    "5. Download the transcript if desired."
)

st.sidebar.header("About")
st.sidebar.info(
    "This app transcribes audio and identifies different speakers. "
    "It uses WhisperX for transcription and diarization. "
    "The process may take a few minutes depending on the length of your audio file."
)