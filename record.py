# import os
# import uuid
# import logging
# import wave
# import io
# import json
# import asyncio
# import websockets
# from typing import List
# from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
# from fastapi.responses import FileResponse
# from fastapi.middleware.cors import CORSMiddleware
# from pydub import AudioSegment
# import openai
# import torch
# from transformers import AutoTokenizer, AutoModel
# from torch.nn.functional import cosine_similarity
# from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine_similarity
# import numpy as np
# import speech_recognition as sr

# app = FastAPI()

# # Configure OpenAI API key
# openai.api_key = "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"

# # Allow CORS for your frontend
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],  # Adjust this if your frontend runs on a different origin
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Initialize the model and tokenizer
# tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
# model = AutoModel.from_pretrained("bert-base-uncased")

# # Global variables
# recording_data = []
# filenames = []
# questions = []
# answers = []

# # Function to generate machine learning questions
# def generate_questions():
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": "Generate 10 machine learning questions."}
#         ]
#     )
#     questions_list = response.choices[0].message['content'].strip().split('\n')
#     return questions_list

# # Endpoint to generate questions
# @app.get("/generate_questions")
# def get_questions():
#     global questions
#     questions = generate_questions()
#     return {"questions": questions}

# # WebSocket handler for audio recording
# @app.websocket("/ws/audio")
# async def websocket_audio_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     audio_buffer = bytearray()
#     file_path = None

#     try:
#         while True:
#             data = await websocket.receive_bytes()
#             audio_buffer.extend(data)
            
#             # Optional: Process data here if needed

#     except WebSocketDisconnect:
#         logging.info("WebSocket disconnected")
#     except Exception as e:
#         logging.error(f"Error handling WebSocket audio: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
#     finally:
#         if audio_buffer:
#             file_path = f"audio_{uuid.uuid4()}.webm"  # Save as WebM initially
#             save_audio_file(audio_buffer, file_path)
#             wav_path = convert_to_wav(file_path)  # Convert to WAV
#             filenames.append(wav_path)
#         await websocket.close()

# def save_audio_file(audio_data: bytearray, filename: str):
#     with open(filename, 'wb') as f:
#         f.write(audio_data)
#     print(f"Audio saved as {filename}")



# def convert_to_wav(file_path: str):
#     audio = AudioSegment.from_file(file_path)
#     wav_path = file_path.replace(".webm", ".wav")
#     audio.export(wav_path, format="wav")
#     os.remove(file_path)  # Remove the original file
#     print(f"Audio converted to {wav_path}")
#     return wav_path


# # Function to transcribe audio to text
# def transcribe_audio(filename: str):
#     recognizer = sr.Recognizer()
#     with sr.AudioFile(filename) as source:
#         audio_data = recognizer.record(source)
#         try:
#             text = recognizer.recognize_google(audio_data)
#             return text
#         except sr.UnknownValueError:
#             return "No answer"



# # Endpoint to combine audio recordings
# @app.post("/combine")
# async def combine_answers():
#     combined_filename = "combined_answers.wav"
#     if not filenames:
#         raise HTTPException(status_code=404, detail="No recordings found")

#     combine_audio_files(filenames, combined_filename)
#     filenames.clear()  # Clear the filenames list after combining

#     return {"combined_filename": combined_filename}

# # Combine audio files function
# def combine_audio_files(file_list, output_file):
#     combined = AudioSegment.empty()
#     for file in file_list:
#         audio = AudioSegment.from_wav(file)
#         combined += audio

#     combined.export(output_file, format="wav")
#     print(f"Combined file saved as {output_file}")




# # Endpoint to download individual recordings
# @app.get("/download/{filename}")
# def download_file(filename: str):
#     file_path = os.path.join("recordings", filename)
#     if not os.path.exists(file_path):
#         raise HTTPException(status_code=404, detail="File not found")
#     return FileResponse(file_path, media_type="audio/wav", filename=filename)



# # Endpoint to transcribe combined audio file
# @app.post("/transcribe_combined")
# async def transcribe_combined():
#     combined_filename = "combined_answers.wav"
#     if not os.path.exists(combined_filename):
#         raise HTTPException(status_code=404, detail="Combined audio file not found")

#     transcription = transcribe_audio(combined_filename)
#     global answers
#     answers.append(transcription)

#     # Save questions and answers to a text file
#     with open("questions_and_answers.txt", "w") as file:
#         for i, question in enumerate(questions):
#             answer = answers[i] if i < len(answers) else "No answer"
#             file.write(f"Question: {question}\nAnswer: {answer}\n\n")
    
#     return {"transcription": transcription}



# # Function to get embeddings
# def get_embedding(text):
#     inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
#     with torch.no_grad():
#         outputs = model(**inputs)
#     embeddings = outputs.last_hidden_state.mean(dim=1)
#     return embeddings

# # Function to compute cosine similarity
# def compute_cosine_similarity(embeddings):
#     n = len(embeddings)
#     similarities = torch.zeros((n, n))
#     for i in range(n):
#         for j in range(n):
#             if i != j:
#                 similarities[i][j] = cosine_similarity(embeddings[i].numpy().reshape(1, -1), embeddings[j].numpy().reshape(1, -1)).item()
#             else:
#                 similarities[i][j] = 1.0
#     return similarities

# # Function to calculate similarity scores and save embeddings
# def calculate_similarity_scores(file_paths: List[str]):
#     documents = []
#     for file in file_paths:
#         with open(file, 'r', encoding='utf-8') as f:
#             documents.append(f.read())

#     embeddings = [get_embedding(doc) for doc in documents]

#     # Save embeddings to files
#     for i, embedding in enumerate(embeddings):
#         torch.save(embedding, f"embedding_{i}.pt")

#     similarities = compute_cosine_similarity(embeddings)
#     return similarities.tolist(), embeddings

# # WebSocket server for transcription using speech_recognition library
# async def recognize_audio(websocket, path):
#     print("Client connected")

#     # Function to handle recognition
#     async def stream_recognition(audio_data):
#         recognizer = sr.Recognizer()
#         audio = sr.AudioFile(io.BytesIO(audio_data))
#         with audio as source:
#             data = recognizer.record(source)
#             try:
#                 transcription = recognizer.recognize_google(data)
#                 await websocket.send(json.dumps({"transcription": transcription}))
#             except sr.UnknownValueError:
#                 await websocket.send(json.dumps({"transcription": "No answer"}))

#     audio_chunks = b''

#     try:
#         async for message in websocket:
#             audio_chunks += message
#             if len(audio_chunks) > 16000 * 2:  # Process after enough data is collected
#                 await stream_recognition(audio_chunks)
#                 audio_chunks = b''  # Clear buffer

#     except websockets.exceptions.ConnectionClosed:
#         print("Client disconnected")

import os
import uuid
import logging
import io
import json
import asyncio
import websockets
from typing import List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydub import AudioSegment
import openai
import torch
from transformers import AutoTokenizer, AutoModel
from torch.nn.functional import cosine_similarity
import speech_recognition as sr

app = FastAPI()

# Configure OpenAI API key
openai.api_key = "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"

# Allow CORS for your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this if your frontend runs on a different origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
model = AutoModel.from_pretrained("bert-base-uncased")

# Global variables
recording_data = []
filenames = []
questions = []
answers = []

# Function to generate machine learning questions
def generate_questions():
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Generate 10 machine learning questions."}
        ]
    )
    questions_list = response.choices[0].message['content'].strip().split('\n')
    return questions_list

# Endpoint to generate questions
@app.get("/generate_questions")
def get_questions():
    global questions
    questions = generate_questions()
    return {"questions": questions}

# WebSocket handler for audio recording
@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_buffer = bytearray()
    file_path = None

    try:
        while True:
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            
            # Optional: Process data here if needed

    except WebSocketDisconnect:
        logging.info("WebSocket disconnected")
    except Exception as e:
        logging.error(f"Error handling WebSocket audio: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        if audio_buffer:
            file_path = f"audio_{uuid.uuid4()}.webm"  # Save as WebM initially
            save_audio_file(audio_buffer, file_path)
            wav_path = convert_to_wav(file_path)  # Convert to WAV
            filenames.append(wav_path)
        await websocket.close()



def save_audio_file(audio_data: bytearray, filename: str):
    with open(filename, 'wb') as f:
        f.write(audio_data)
    print(f"Audio saved as {filename}")



def convert_to_wav(file_path: str):
    audio = AudioSegment.from_file(file_path)
    wav_path = file_path.replace(".webm", ".wav")
    audio.export(wav_path, format="wav")
    os.remove(file_path)  # Remove the original file
    print(f"Audio converted to {wav_path}")
    return wav_path



# Function to transcribe audio to text
def transcribe_audio(filename: str):
    recognizer = sr.Recognizer()
    with sr.AudioFile(filename) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data)
            return text
        except sr.UnknownValueError:
            return "No answer"



# Endpoint to combine audio recordings
@app.post("/combine")
async def combine_answers():
    combined_filename = "combined_answers.wav"
    if not filenames:
        raise HTTPException(status_code=404, detail="No recordings found")

    combine_audio_files(filenames, combined_filename)
    filenames.clear()  # Clear the filenames list after combining

    return {"combined_filename": combined_filename}





# Combine audio files function
def combine_audio_files(file_list, output_file):
    combined = AudioSegment.empty()
    for file in file_list:
        audio = AudioSegment.from_wav(file)
        combined += audio

    combined.export(output_file, format="wav")
    print(f"Combined file saved as {output_file}")




# Endpoint to download individual recordings
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join("recordings", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="audio/wav", filename=filename)





# Endpoint to transcribe combined audio file
@app.post("/transcribe_combined")
async def transcribe_combined():
    combined_filename = "combined_answers.wav"
    if not os.path.exists(combined_filename):
        raise HTTPException(status_code=404, detail="Combined audio file not found")

    # Transcribe each audio file and save to answers list
    global answers
    answers = []
    for filename in filenames:
        transcription = transcribe_audio(filename)
        answers.append(transcription)

  # Save questions and answers to a text file
    with open("questions_and_answers.txt", "w") as file:
        for i, question in enumerate(questions):
            answer = answers[i] if i < len(answers) else "No answer"
            file.write(f"Question: {question}\nAnswer: {answer}\n\n")
    
    return {"transcription": answers}

# Endpoint to download the text file with questions and answers
@app.get("/download_transcriptions")
def download_transcriptions():
    file_path = "questions_and_answers.txt"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="text/plain", filename="questions_and_answers.txt")













####################################step 2 #########################################33
# Function to get embeddings
def get_embedding(text):
    inputs = tokenizer(text, return_tensors='pt', padding=True, truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return embeddings

# Function to compute cosine similarity
def compute_cosine_similarity(embeddings):
    n = len(embeddings)
    similarities = torch.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if i != j:
                similarities[i][j] = cosine_similarity(embeddings[i].numpy().reshape(1, -1), embeddings[j].numpy().reshape(1, -1)).item()
            else:
                similarities[i][j] = 1.0
    return similarities

# Function to calculate similarity scores and save embeddings
def calculate_similarity_scores(file_paths: List[str]):
    documents = []
    for file in file_paths:
        with open(file, 'r', encoding='utf-8') as f:
            documents.append(f.read())

    embeddings = [get_embedding(doc) for doc in documents]

    # Save embeddings to files
    for i, embedding in enumerate(embeddings):
        torch.save(embedding, f"embedding_{i}.pt")

    similarities = compute_cosine_similarity(embeddings)
    return similarities.tolist(), embeddings

# WebSocket server for transcription using speech_recognition library
async def recognize_audio(websocket, path):
    print("Client connected")

    # Function to handle recognition
    async def stream_recognition(audio_data):
        recognizer = sr.Recognizer()
        audio = sr.AudioFile(io.BytesIO(audio_data))
        with audio as source:
            data = recognizer.record(source)
            try:
                transcription = recognizer.recognize_google(data)
                await websocket.send(json.dumps({"transcription": transcription}))
            except sr.UnknownValueError:
                await websocket.send(json.dumps({"transcription": "No answer"}))

    audio_chunks = b''

    try:
        async for message in websocket:
            audio_chunks += message
            if len(audio_chunks) > 16000 * 2:  # Process after enough data is collected
                await stream_recognition(audio_chunks)
                audio_chunks = b''  # Clear buffer

    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

