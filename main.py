import os
import google.generativeai as genai
from flask import Flask, render_template, request, jsonify, session
import uuid
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Replace with your actual API key!
API_KEY = "AIzaSyDcsgrTsg47uOcp8sX1BB4qJbsfr4iyz-w"  # Replace with your actual API key!!!
if not API_KEY:
    print("Error: GOOGLE_AI_API_KEY environment variable not set.")
    exit(1)

genai.configure(api_key=API_KEY)

generation_config = {
    "temperature": 0.7,
    "max_output_tokens": 512,
}

model = genai.GenerativeModel(
    model_name="gemini-pro", 
    generation_config=generation_config,
)

client_observations = {}

@app.route("/", methods=["GET", "POST"])
def index():
    if 'uuid' not in session:
        session['uuid'] = str(uuid.uuid4())

    if request.method == "POST":
        user_input = request.form.get("user-input", "").strip()
        if not user_input:
            return jsonify({"error": "Please enter a message."})

        try:
            chat_session = model.start_chat() if not hasattr(index, 'chat_session') else index.chat_session
            response = chat_session.send_message({"parts": [{"text": user_input}]})

            if response and response.parts:  # Explicitly Check for valid response
                response_text = response.parts[0].text
            else:
                response_text = "Error getting AI response"  # Provide default message if no response parts


            if session['uuid'] not in client_observations:
                client_observations[session['uuid']] = {"history": []}
            client_observations[session['uuid']]["history"].append({
                "timestamp": datetime.now().isoformat(),
                "user_input": user_input,
                "ai_response": response_text
            })
            return jsonify({"ai_response": response_text})  # Return AI response as JSON

        except Exception as e:
            print(f"An error occurred: {e}") # Print error to the console for debugging
            return jsonify({"error": str(e)})

    return render_template("index.html", uuid=session['uuid'])


@app.route("/get_observations/<uuid>")
def get_observations(uuid):
    if uuid in client_observations:
         # Store observations (example - replace with your storage method)
        with open(f"observations_{uuid}.json", "w") as f: 
            json.dump(client_observations[uuid], f)
        return jsonify(client_observations[uuid])
    return "No observations found for this UUID."


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0')
