import os
import google.generativeai as genai
from flask import Flask, render_template, request
import sys

app = Flask(__name__)

# Set up your Google Generative AI API key
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Configure the model and chat session
generation_config = {
  "temperature": 1,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 8192,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
  system_instruction="be prepared for answer education-related questions most of time",
)

chat_session = model.start_chat(
  history=[
  ]
)

@app.route("/", methods=["GET", "POST"])
def index():
  if request.method == "POST":
    user_input = request.form["user_input"]

    # Send the message to the AI and get the response
    response = chat_session.send_message(user_input)

    # Update the chat history
    chat_session.history.append({"role": "user", "content": user_input})
    chat_session.history.append({"role": "assistant", "content": response.text})

    return render_template("index.html", user_input=user_input, ai_response=response.text)
  else:
    return render_template("index.html")

if __name__ == "__main__":
  app.run(debug=True, port=int(sys.argv[1]), host='0.0.0.0')
