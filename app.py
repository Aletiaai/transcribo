import streamlit as st
import requests
import json
import time
import io

def json_to_text(json_data):
    """Convert transcription JSON to formatted text file for Word/Google Docs"""
    text_content = "TRANSCRIPCIÓN\n\n"
    
    # Check if the expected structure exists
    if "segments" in json_data:
        for segment in json_data["segments"]:
            # Format: [HH:MM:SS] Speaker: Text
            start_time = format_time(segment.get("start", 0))
            speaker = segment.get("speaker", "")
            text = segment.get("text", "")
            
            # Add formatted line
            if speaker:
                text_content += f"[{start_time}] SPEAKER {speaker}: {text}\n\n"
            else:
                text_content += f"[{start_time}] {text}\n\n"
    else:
        # Fallback if JSON structure is different
        text_content += "No se pudo formatear la transcripción. Estructura JSON inesperada.\n\n"
        text_content += json.dumps(json_data, indent=2, ensure_ascii=False)
    
    return text_content

def format_time(seconds):
    """Format seconds to HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

st.title("Transcribo by Aletia")

# Colab URL input
colab_url = st.text_input("Ingresa la URL proporcionada por el admin:")

# Add tabs for different functions
tab1, tab2 = st.tabs(["Subir Audio", "Verificar Estado"])

with tab1:
    st.header("Subir Archivo de Audio")
    
    # File uploader
    uploaded_file = st.file_uploader("Selecciona un archivo de audio", type=['mp3', 'm4a'])
    
    if uploaded_file is not None and colab_url:
        # Display file details
        file_details = {"FileName": uploaded_file.name, "FileType": uploaded_file.type, "FileSize": f"{uploaded_file.size / (1024*1024):.2f} MB"}
        st.write(file_details)
        
        if st.button("Iniciar Procesamiento"):
            try:
                # Ensure URL has trailing slash
                if not colab_url.endswith('/'):
                    colab_url = colab_url + '/'
                
                # Test connection to backend
                test_response = requests.get(colab_url, timeout=10)
                
                # Upload file
                files = {'audio': (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(f"{colab_url}upload", files=files)
                
                if response.status_code == 200:
                    job_data = response.json()
                    job_id = job_data["job_id"]
                    
                    st.success(f"¡Archivo subido exitosamente! ID del trabajo: {job_id}")
                    st.info("El procesamiento continuará en segundo plano. Guarda este ID para verificar el estado después.")
                    
                    # Store job ID in session state for easy access
                    if 'jobs' not in st.session_state:
                        st.session_state.jobs = []
                    
                    st.session_state.jobs.append({
                        "id": job_id,
                        "filename": uploaded_file.name,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    # Show the job ID prominently
                    st.code(job_id, language=None)
                    
                else:
                    st.error(f"Error al subir el archivo: {response.text}")
                
            except Exception as e:
                st.error(f"Error: {str(e)}")

with tab2:
    st.header("Verificar Estado de Procesamiento")
    
    # Option to enter job ID or select from history
    if 'jobs' in st.session_state and st.session_state.jobs:
        st.subheader("Trabajos Recientes")
        for job in st.session_state.jobs:
            if st.button(f"{job['filename']} ({job['timestamp']})"):
                st.session_state.selected_job_id = job['id']
    
    job_id = st.text_input("O ingresa el ID del trabajo:",
                            value=st.session_state.get('selected_job_id', ''))
    
    if job_id and colab_url:
        # Ensure URL has trailing slash
        if not colab_url.endswith('/'):
            colab_url = colab_url + '/'
            
        if st.button("Verificar Estado"):
            try:
                response = requests.get(f"{colab_url}status/{job_id}")
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data["status"]
                    
                    # Store status in session state for use outside this button
                    st.session_state.job_status = status
                    st.session_state.job_filename = status_data.get('filename', 'unknown')
                    st.session_state.job_message = status_data.get('message', '')
                    
                    if status == "processing" or status == "queued":
                        st.info(f"El archivo {status_data['filename']} aún está siendo procesado. Por favor, verifica más tarde.")
                        st.text(f"Mensaje: {st.session_state.job_message}")
                    
                    elif status == "complete":
                        st.success(f"¡El procesamiento de {status_data['filename']} está completo!")
                    
                    elif status == "error":
                        st.error(f"Ocurrió un error durante el procesamiento: {st.session_state.job_message}")
                
                else:
                    st.error(f"Error al verificar estado: {response.text}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        # Put download functionality outside the Verificar Estado button
        if 'job_status' in st.session_state and st.session_state.job_status == "complete":
            if st.button("Descargar Transcripción"):
                try:
                    # Ensure URL has trailing slash
                    if not colab_url.endswith('/'):
                        colab_url = colab_url + '/'
                        
                    result_response = requests.get(f"{colab_url}result/{job_id}")
                    
                    if result_response.status_code == 200:
                        json_data = result_response.json()
                        
                        # Create text version for Word/Google Docs
                        text_content = json_to_text(json_data)
                        
                        # Create columns for download options
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            # Download as JSON
                            json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="Descargar como JSON",
                                data=json_str.encode('utf-8'),
                                file_name=f"transcripcion_{st.session_state.job_filename}.json",
                                mime="application/json"
                            )
                        
                        with col2:
                            # Download as Text (compatible with Word/Google Docs)
                            st.download_button(
                                label="Descargar como Texto (Word/Google Docs)",
                                data=text_content.encode('utf-8'),
                                file_name=f"transcripcion_{st.session_state.job_filename}.txt",
                                mime="text/plain"
                            )
                        
                        # Show preview of text content
                        with st.expander("Vista previa de la transcripción"):
                            st.text(text_content)
                            
                    else:
                        st.error(f"Error al obtener resultado: {result_response.text}")
                except Exception as e:
                    st.error(f"Error al descargar: {str(e)}")

# Add instructions in sidebar
st.sidebar.header("Instrucciones")
st.sidebar.info(
    "1. Ingresa la URL proporcionada por el admin.\n"
    "2. En la pestaña 'Subir Audio', sube un archivo de audio MP3 or M4A.\n"
    "3. Inicia el procesamiento y guarda el ID del trabajo.\n"
    "4. Usa la pestaña 'Verificar Estado' para monitorear el progreso y descargar la transcripción cuando esté lista.\n"
    "5. Para archivos largos (1+ horas), el procesamiento puede tomar 20-60 minutos."
)