# FRONTEND CODE (STREAMLIT)
import streamlit as st
import requests
import json
import time

st.title("Transcribo app by Aletia")

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
                # Test connection to backend
                test_response = requests.get(colab_url, timeout=10)
                
                # Upload file
                files = {'audio': (uploaded_file.name, uploaded_file, uploaded_file.type)}
                response = requests.post(f"{colab_url}/upload", files=files)
                
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
        if st.button("Verificar Estado"):
            try:
                response = requests.get(f"{colab_url}/status/{job_id}")
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data["status"]
                    
                    if status == "processing":
                        st.info(f"El archivo {status_data['filename']} aún está siendo procesado. Por favor, verifica más tarde.")
                    
                    elif status == "complete":
                        st.success(f"¡El procesamiento de {status_data['filename']} está completo!")
                        
                        # Add button to download result
                        if st.button("Descargar Transcripción"):
                            result_url = f"{colab_url}/result/{job_id}"
                            st.markdown(f"[Haz clic aquí para descargar la transcripción]({result_url})")
                    
                    elif status == "error":
                        st.error(f"Ocurrió un error durante el procesamiento. Por favor, intenta nuevamente o contacta al administrador.")
                
                else:
                    st.error(f"Error al verificar estado: {response.text}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Add instructions in sidebar
st.sidebar.header("Instrucciones")
st.sidebar.info(
    "1. Ingresa la URL proporcionada por el admin.\n"
    "2. En la pestaña 'Subir Audio', sube un archivo de audio MP3 or M4A.\n"
    "3. Inicia el procesamiento y guarda el ID del trabajo.\n"
    "4. Usa la pestaña 'Verificar Estado' para monitorear el progreso y descargar la transcripción cuando esté lista.\n"
    "5. Para archivos largos (1+ horas), el procesamiento puede tomar 20-60 minutos."
)