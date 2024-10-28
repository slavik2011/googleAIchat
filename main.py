import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit, join_room, leave_room
import sys

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session management
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
    "temperature": 0.7,  # Adjust for desired creativity
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 512,  # Adjust as needed
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-pro",  # Replace with your desired model
    generation_config=generation_config,
    #system_instruction="Respond in a concise and informative manner.",
)


@app.route("/")
def index():
    return render_template("index.html")  # Render the index.html template

@socketio.on('connect')
def handle_connect():
    # Generate a unique room name for the client
    client_id = str(uuid.uuid4())
    print(f'Client connected: {client_id}')
    join_room(client_id)  # Join the client's unique room
    emit('room', {'room': client_id})  # Send the client's room ID to the client

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid  # Get the client's Socket.IO ID
    print(f'Client disconnected: {client_id}')
    leave_room(client_id)  # Leave the client's unique room

@socketio.on('message')
def handle_message(data):
    user_input = data['message']
    client_id = data['room']  # Get the client's room ID from the data
    try:
        # Start a new chat session if there isn't one already
        chat_session = model.start_chat() if not hasattr(index, 'chat_session') else index.chat_session

        content = {"parts": [{"text": user_input}]}
        response = chat_session.send_message(content)

        if not response:
            emit('message', {'message': 'Error receiving response from the AI model.'}, room=client_id)
            return

        # Extract the response text (access the first part)
        response_text = response.parts[0].text if response.parts else ""

        # Send the response to the client in their specific room
        emit('message', {'message': response_text}, room=client_id)

        # You can save the conversation data here if needed (e.g., in a database)

    except Exception as e:
        emit('message', {'message': f'An error occurred: {str(e)}'}, room=client_id)

if __name__ == "__main__":
    socketio.run(app, debug=True, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0', allow_unsafe_werkzeug=True)
