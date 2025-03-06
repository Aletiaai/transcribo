import streamlit as st
import requests
import os
import time

# Streamlit app title
st.title("Transcribo app by Aletia")

# Colab URL input
colab_url = st.text_input("Ingresa la URL proporcionada por el admin:")

# Display the entered URL
if colab_url:
    st.write(f"URL ingresada: {colab_url}")

# File uploader
uploaded_file = st.file_uploader("Selecciona un archivo de audio", type=['mp3', 'm4a'])

def process_audio(uploaded_file, colab_url):
    files = {'audio': (uploaded_file.name, uploaded_file, uploaded_file.type)}
    debug_info = []

    try:
        with requests.post(colab_url, files=files, stream=True, timeout=7200, headers={'Connection': 'keep-alive'}) as response:  # 2-hours timeout
            response.raise_for_status()
            transcript = ""
            progress_placeholder = st.empty()
            status_placeholder = st.empty()
            transcript_started = False
            transcript_lines = []
            last_update_time = time.time()

            for line in response.iter_lines():
                # Reset the "no update" timer
                current_time = time.time()
                last_update_time = current_time

                if line:
                    decoded_line = line.decode('utf-8')
                    debug_info.append(f"Received line: {decoded_line}")  # Debug print

                    if decoded_line == "FINAL_TRANSCRIPT_START":
                        transcript_started = True
                        status_placeholder.info("Recibiendo transcripción final...")
                    elif decoded_line == "FINAL_TRANSCRIPT_END":
                        transcript_started = False
                        transcript = '\n'.join(transcript_lines)
                    elif transcript_started:
                        transcript_lines.append(decoded_line)
                    else:
                        progress_placeholder.text(decoded_line)
                        status_placeholder.info(f"Procesando... {decoded_line}")

            if not transcript:
                debug_info.append("No se recibio la transcipción final del motor de procesamiento.")
            elif transcript.strip() == "Ocurrio un error durante el proceso":
                debug_info.append("Ocurrio un error durante el proceso en el backend.")
            return transcript, debug_info

    except requests.exceptions.Timeout:
        return None, ["El procesamiento está tomando demasiado tiempo. La conexión expiró. Intenta con un archivo más corto o contacta al administrador."]
    except requests.exceptions.ConnectionError:
        return None, ["Se perdió la conexión con el backend. Esto sucede frecuentemente con archivos muy grandes. Intenta con un archivo más corto o contacta al administrador."]
    except requests.exceptions.RequestException as e:
        return None, [f"Ocurrió un error mientras se establecía la conexión con el backend: {str(e)}"]


if uploaded_file is not None and colab_url:
    # Display file details
    file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": uploaded_file.size}
    st.write(file_details)

    # Calculate and display estimated processing time
    file_size_mb = uploaded_file.size / (1024 * 1024)  # Convert to MB
    estimated_minutes = max(10, int(file_size_mb / 5))  # Rough estimate: 5MB per minute
    
    st.info(f"Tamaño del archivo: {file_size_mb:.1f} MB. Tiempo estimado de procesamiento: {estimated_minutes} minutos.")
    st.warning("Nota: Los archivos mayores a 100 MB (aproximadamente 1 hora) pueden causar problemas. Se recomienda dividir archivos largos en segmentos más pequeños.")

    # Transcription and diarization
    if st.button("Transcribir"):
        st.info(f"Procesando audio... ETA: {estimated_minutes} minutos. Por favor, no cierres esta ventana.")
        progress_bar = st.progress(0)

        # Create a placeholder for status updates
        status = st.empty()
        
        try:
            # Test connection to backend
            try:
                test_response = requests.get(colab_url, timeout=10)
                status.success(f"Conexión con el backend establecida. Código: {test_response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"No se pudo conectar con el backend: {str(e)}")
                st.stop()
            
            # Process audio file
            status.info("Enviando archivo al backend. Esto puede tomar varios minutos para archivos grandes...")
            transcript, debug_info = process_audio(uploaded_file, colab_url)
            
            # Debug information in a collapsible section
            with st.expander("Mostrar la información para el 'Debugging'", expanded=False):
                st.write("Probando la conexión con el backend...")
                st.write(f"Código de estatus de la prueba de conexión con el backend: {test_response.status_code}")
                st.write(f"Respuesta a la prueba de conexión con el backend: {test_response.text}")
                st.write("Enviando el archivo al motor de transcripción para su procesamiento...")
                for info in debug_info:
                    st.text(info)
            
            if transcript:
                if transcript.strip() == "":
                    st.error("Se recibió una transcripción vacía del backend.")
                else:
                    st.success("¡Transcripción completada!")
                    st.subheader("Transcripción con la identificación de participantes:")
                    st.text_area("", transcript, height=300)

                # Option to download the transcript
                st.download_button(
                    label="Descarga la transcripción",
                    data=transcript,
                    file_name="transcript.txt",
                    mime="text/plain"
                )
            else:
                st.error("Ocurrió un error durante el proceso. No se regresó ninguna transcripción.")
        except Exception as e:
            st.error(f"Error inesperado: {str(e)}")
else:
    st.warning("Por favor ingresa la URL proveída por el admin y sube un archivo de audio.")

# Instructions and additional information
st.sidebar.header("Instrucciones")
st.sidebar.info(
    "1. Ingresa la URL proporcionada por el admin.\n"
    "2. Sube un archivo de audio MP3 or M4A.\n"
    "3. Da Clic en 'Transcribir' para procesar el audio.\n"
    "4. Consulta la transcripción en la ventana.\n"
    "5. Descarga la transcripción."
)

st.sidebar.header("Acerca de")
st.sidebar.info(
    "Esta aplicación transcribe archivos de audio m4a o mp3 identificando a los diferentes participantes en el audio. "
    "El proceso Puede tomar más de 10 minutos dependiendo de la extensión de tu archivo de audio."
)