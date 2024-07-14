import streamlit as st
import requests
import os

# Streamlit app title
st.title("Transcripción de Audio")

# Colab URL input
colab_url = st.text_input("Ingresa la URL proveida por el admin:")

# File uploader
uploaded_file = st.file_uploader("Selecciona un archivo de audio", type=['mp3', 'm4a'])

if uploaded_file is not None and colab_url:
    # Display file details
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
    st.write(file_details)

    # Transcription and diarization
    if st.button("Transcribir"):
        st.info("Procesando audio... Esto puede tomar varios minutos.")
        
        try:
            # Send file to Colab backend
            files = {'audio': (uploaded_file.name, uploaded_file, uploaded_file.type)}
            response = requests.post(f'{colab_url}/transcribe', files=files)
            
            if response.status_code == 200:
                result = response.json()
                transcript = result['transcript']
                
                st.subheader("Transcripción con identificación de participantes:")
                st.text_area("", transcript, height=300)

                # Option to download the transcript
                st.download_button(
                    label="Descarga la transcripción",
                    data=transcript,
                    file_name="transcript.txt",
                    mime="text/plain"
                )
            else:
                st.error(f"An error occurred during processing. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"An error occurred while connecting to the transcript engine: {str(e)}")
else:
    st.warning("Por favor ingresa la la URL proveida por el admin y selecciona un archivo de audio.")

# Instructions and additional information
st.sidebar.header("Instrucciones")
st.sidebar.info(
    "1. Ingresa la URL que te asigna el admin.\n"
    "2. Subre un arcvhivo de audio MP3 o M4A.\n"
    "3. Da click en 'Transcribir' para procesar el audio.\n"
    "4. Revisa la transcripción.\n"
    "5. Descarga la transcripción si así lo deseas."
)

st.sidebar.header("Acerca de esta app")
st.sidebar.info(
    "Esta app transcribe audio e identifica a los diferentes participantes. "
    "Usa un modelo de inteligencia Artificial para la transcripción. "
    "El proceso toma aproximadamente 30 minutos para un archivo de audio de 1.5 horas."
)