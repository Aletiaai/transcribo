# Install required libraries
!pip install git+https://github.com/m-bain/whisperx.git --upgrade
!pip install pydub flask flask-cors

# Import necessary libraries
import whisperx
import gc
from pydub import AudioSegment
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64
import io

app = Flask(__name__)
CORS(app)

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    # Get the audio file from the request
    audio_file = request.files['audio']
    
    # Save the audio file temporarily
    temp_audio_path = 'temp_audio'
    audio_file.save(temp_audio_path)
    
    # Check the file format and convert if necessary
    if audio_file.filename.endswith('.m4a'):
        audio = AudioSegment.from_file(temp_audio_path, format='m4a')
        audio.export('temp_audio.mp3', format='mp3')
        temp_audio_path = 'temp_audio.mp3'
    elif audio_file.filename.endswith('.mp3'):
        # If it's already an MP3, we don't need to convert
        pass
    else:
        return jsonify({'error': 'Unsupported file format. Please upload an MP3 or M4A file.'}), 400
    
    # Transcription
    device = "cuda"
    batch_size = 16
    compute_type = "float16"

    try:
        model = whisperx.load_model("large-v2", device, compute_type=compute_type)
        audio = whisperx.load_audio(temp_audio_path)
        result = model.transcribe(audio, batch_size=batch_size)

        # Alignment
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

        # Diarization
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=os.environ['HF_TOKEN'], device=device)
        diarize_segments = diarize_model(audio)
        result = whisperx.assign_word_speakers(diarize_segments, result)

        # Process results
        formatted_output = []
        current_speaker = None

        for segment in result['segments']:
            segment_text = segment.get('text', '').strip()
            speaker = segment.get('speaker', 'UNKNOWN')

            if speaker != current_speaker:
                formatted_output.append(f"\nSpeaker {speaker}:")
                current_speaker = speaker

            formatted_output.append(segment_text)

        return jsonify({'transcript': '\n'.join(formatted_output)})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up temporary files
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
        if os.path.exists('temp_audio.mp3'):
            os.remove('temp_audio.mp3')

# Run the Flask app
from google.colab.output import eval_js
print(eval_js("google.colab.kernel.proxyPort(5000)"))

app.run(port=5000)