import tkinter as tk
from tkinter import ttk
import pyaudio
import wave
import whisper
import threading
import time

# Global variables
recording = False
audio_file = "output.wav"
transcription_file = "transcription.txt"
chunk_size = 1024
sample_format = pyaudio.paInt16
channels = 1
rate = 16000
frames = []

# Initialize Whisper model with error handling
try:
    model = whisper.load_model("small")
except Exception as e:
    print(f"Error loading Whisper model: {e}")
    model = None

# Function to start recording
def start_recording():
    global recording, frames
    recording = True
    frames = []
    progress_bar['value'] = 0
    progress_bar['maximum'] = 100

    # Get recording duration from spinbox
    duration = int(duration_spinbox.get())  # Get the value from the spinbox

    # Create PyAudio object with error handling
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=sample_format, channels=channels,
                        rate=rate, input=True, frames_per_buffer=chunk_size)
    except Exception as e:
        print(f"Error initializing microphone: {e}")
        return

    # Timer to stop recording after the specified duration
    def stop_timer():
        time.sleep(duration)  # Stop after the user-defined duration
        stop_recording()

    threading.Thread(target=stop_timer, daemon=True).start()

    # Start recording
    def record_audio():
        nonlocal stream
        while recording:
            try:
                data = stream.read(chunk_size)
                frames.append(data)
                # Update progress bar based on the length of recorded frames
                progress_bar['value'] = min(100, len(frames) / (rate / chunk_size) * 100)
                root.update_idletasks()
                time.sleep(0.1)
            except Exception as e:
                print(f"Error reading audio: {e}")
                break

        # Stop the stream and save the audio when recording is done
        stream.stop_stream()
        stream.close()
        p.terminate()
        save_audio()

    # Run recording in a separate thread to keep the UI responsive
    threading.Thread(target=record_audio, daemon=True).start()

# Function to stop recording
def stop_recording():
    global recording
    recording = False
    stop_button.config(state=tk.DISABLED)
    transcribe_button.config(state=tk.NORMAL)

# Function to save the audio
def save_audio():
    with wave.open(audio_file, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(sample_format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

# Function to transcribe audio
def transcribe_audio():
    if model is None:
        transcription_box.insert(tk.END, "Whisper model not loaded. Please restart the application.\n")
        return

    try:
        # Load the audio for transcription
        result = model.transcribe(audio_file)
        transcription_text = result['text']

        # Save the transcription to a file
        with open(transcription_file, 'w') as f:
            f.write(transcription_text)

        # Display transcription in a text box
        transcription_box.delete(1.0, tk.END)
        transcription_box.insert(tk.END, transcription_text)
    except Exception as e:
        transcription_box.insert(tk.END, f"Error transcribing audio: {e}\n")

# Set up the Tkinter window
root = tk.Tk()
root.title("Real-Time Audio Recorder and Transcriber")

# Start Recording Button
start_button = tk.Button(root, text="Start Recording", command=start_recording)
start_button.pack(pady=10)

# Stop Recording Button
stop_button = tk.Button(root, text="Stop Recording", state=tk.DISABLED, command=stop_recording)
stop_button.pack(pady=10)

# Transcribe Button
transcribe_button = tk.Button(root, text="Transcribe", state=tk.DISABLED, command=transcribe_audio)
transcribe_button.pack(pady=10)

# Progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=10)

# Transcription Box
transcription_box = tk.Text(root, height=10, width=50)
transcription_box.pack(pady=10)

# Recording duration input
duration_label = tk.Label(root, text="Recording Duration (seconds):")
duration_label.pack(pady=5)

duration_spinbox = tk.Spinbox(root, from_=1, to_=300, width=5)  # 1 to 300 seconds
duration_spinbox.pack(pady=5)

# Run the Tkinter main loop
root.mainloop()
