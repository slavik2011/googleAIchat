import os
import google.generativeai as genai
from flask import Flask, render_template, request, redirect, url_for
import sys

app = Flask(__name__)

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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        user_input = request.form["user-input"].strip()

        if not user_input:
            return render_template("index.html", error_message="Please enter a message.")

        try:
            # Start a new chat session if there isn't one already
            chat_session = model.start_chat() if not hasattr(index, 'chat_session') else index.chat_session

            content = {"parts": [{"text": user_input}]}
            response = chat_session.send_message(content)

            if not response:
                return render_template("index.html", error_message="Error receiving response from the AI model.")

            # Extract the response text 
            response_text = response.content.parts[0].text

            # Append the user input and AI response to the chat history
            chat_session.history.append({"role": "user", "content": content})
            chat_session.history.append({"role": "assistant", "content": {"parts": [{"text": response_text}]}})

            return render_template("index.html", chat_session=chat_session)
        except Exception as e:
            return render_template("index.html", error_message=f"An error occurred: {str(e)}")
    else:
        return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)), host='0.0.0.0')
