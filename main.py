import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import uuid
import sys
from google.generativeai.types import HarmCategory, HarmBlockThreshold

app = Flask(__name__)
app.secret_key = os.urandom(64)  # Set a secret key for session management
socketio = SocketIO(app)

# Set up your Google Generative AI API key
# Replace with your actual API key!  Never hardcode in a repo!
API_KEY = 'AIzaSyDcsgrTsg47uOcp8sX1BB4qJbsfr4iyz-w' 
if not API_KEY:
    print("Error: GOOGLE_AI_API_KEY environment variable not set.")
    sys.exit(1)  # Exit with an error code

genai.configure(api_key=API_KEY)

# Configuration for the model (you might want to adjust these)
generation_config = {
    "temperature": 1,  # Adjust for desired creativity
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,  # Adjust as needed
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-pro",  # Replace with your desired model
    generation_config=generation_config,
    #system_instruction="Respond in a concise and informative manner.",
)

# Dictionary to store client rooms
client_rooms = {}
# Dictionary to store chat sessions (one per room)
chat_sessions = {} 

@app.route("/")
def index():
    return render_template("index.html")  # Render the index.html template

@socketio.on('connect')
def handle_connect():
    # Generate a new room ID only if the client doesn't have one already
    client_id = request.sid
    if client_id not in client_rooms:
        new_room_id = str(uuid.uuid4())
        client_rooms[client_id] = new_room_id
        join_room(new_room_id)
        emit('room', {'room': new_room_id}, room=client_id)

        # Create a new chat session for the room
        chat_sessions[new_room_id] = model.start_chat() 
    else:
        # Client reconnected, use the existing room
        join_room(client_rooms[client_id])
        emit('room', {'room': client_rooms[client_id]}, room=client_id)

    print(f"Client connected to room: {client_rooms[client_id]}")

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    room_id = client_rooms.pop(client_id, None)  # Remove client from dictionary
    if room_id:
        leave_room(room_id)
        print(f'Client disconnected from room: {room_id}')

@socketio.on('message')
def handle_message(data):
    user_input = data['message']
    client_id = request.sid
    room_id = client_rooms.get(client_id)  # Get room ID from the dictionary

    if not room_id:
        emit('message', {'message': 'Error: Client not assigned to a room. Try refreshing the page'}, room=client_id)
        return

    try:
        # Get the chat session for the room
        chat_session = chat_sessions.get(room_id) 
        if not chat_session:
            emit('message', {'message': 'Error: No chat session found for this room. Try refreshing the page'}, room=client_id)
            return

        content = {"parts": [{"text": user_input}]}
        response = chat_session.send_message(content,
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    })

        if not response:
            emit('message', {'message': 'Error receiving response from the AI model. Ask website developer to fix that'}, room=room_id)
            return

        # Extract the response text (access the first part)
        response_text = response.parts[0].text if response.parts else ""

        # Send the response to the client in their specific room
        emit('message', {'message': response_text}, room=room_id)

        # You can save the conversation data here if needed (e.g., in a database)

    except Exception as e:
        emit('message', {'message': f'An error occurred: {str(e)}'}, room=room_id)

if __name__ == "__main__":
    socketio.run(app, debug=True, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0', allow_unsafe_werkzeug=True)
