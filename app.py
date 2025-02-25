from flask import Flask, request, jsonify, render_template
import ollama
import json
from http import HTTPStatus

app = Flask(__name__)
history = []

# Load training data
with open('training_data.txt', 'r') as f:
    TRAINING_DATA = f.read()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        user_input = request.json.get('message', '').strip()
        if not user_input:
            return jsonify({"error": "No message provided"}), HTTPStatus.BAD_REQUEST

        history.append({"role": "user", "content": user_input})
        context = history[-3:]

        # Combine training data with user context
        prompt = f"{TRAINING_DATA}\n\nCurrent conversation: {json.dumps(context)}\nUser: {user_input}"

        # Call DeepSeek-R1
        response = ollama.chat(
            model="deepseek-r1:7b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.6}
        )
        print(f"Raw Ollama response: {response}")  # Debug

        bot_reply = response['message']['content'].strip()
        history.append({"role": "assistant", "content": bot_reply})

        return jsonify({"response": bot_reply})

    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": "Something went wrong, try again!"}), HTTPStatus.INTERNAL_SERVER_ERROR

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)