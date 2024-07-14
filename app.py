import streamlit as st
import requests
import os

# Streamlit app title
st.title("Audio Transcription and Diarization App")

# Colab URL input
colab_url = st.text_input("Enter the Colab backend URL:")

# File uploader
uploaded_file = st.file_uploader("Choose an audio file", type=['mp3', 'm4a'])

if uploaded_file is not None and colab_url:
    # Display file details
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
    st.write(file_details)

    # Transcription and diarization
    if st.button("Transcribe and Diarize"):
        st.info("Processing audio... This may take a few minutes.")
        
        try:
            # Send file to Colab backend
            files = {'audio': (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(f'{colab_url}/transcribe', files=files)
            
            if response.status_code == 200:
                result = response.json()
                transcript = result['transcript']
                
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
                st.error(f"An error occurred during processing. Status code: {response.status_code}")
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