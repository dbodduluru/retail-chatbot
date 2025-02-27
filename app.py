from flask import Flask, request, jsonify, render_template
from confluent_kafka import Consumer, KafkaException
import ollama
import json
import threading
from http import HTTPStatus

app = Flask(__name__)
history = []  # Stores conversation history in memory

# Load static training data from file
with open('training_data.txt', 'r') as f:
    TRAINING_DATA = f.read()

# Kafka consumer setup for real-time inventory updates
kafka_conf = {
    'bootstrap.servers': 'kafka:9092',  # Internal Kafka listener in Docker network
    'group.id': 'retail-chatbot-group',  # Consumer group ID
    'auto.offset.reset': 'latest'       # Start reading from latest messages
}
consumer = Consumer(kafka_conf)
consumer.subscribe(['inventory_updates'])  # Topic for inventory data
inventory_data = {}  # Dictionary to hold live inventory from Kafka

def kafka_listener():
    """Background thread to listen for Kafka inventory updates."""
    while True:
        try:
            msg = consumer.poll(timeout=1.0)  # Poll Kafka every second
            if msg is None: continue
            if msg.error():
                raise KafkaException(msg.error())
            data = json.loads(msg.value().decode('utf-8'))
            item = data.get('item')
            if item:
                inventory_data[item] = data  # Update inventory with latest data
            print(f"Kafka inventory update: {data}")
        except Exception as e:
            print(f"Kafka error: {e}")

# Start Kafka listener in a background thread
threading.Thread(target=kafka_listener, daemon=True).start()

@app.route('/')
def index():
    """Serve the main chatbot UI."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle text-based chat requests from the UI."""
    try:
        user_input = request.json.get('message', '').strip()
        if not user_input:
            return jsonify({"error": "No message provided"}), HTTPStatus.BAD_REQUEST

        history.append({"role": "user", "content": user_input})
        context = history[-3:]  # Keep last 3 exchanges for context

        # Include live Kafka inventory data in the prompt
        inventory_context = json.dumps(inventory_data) if inventory_data else "No live inventory updates yet."
        prompt = f"{TRAINING_DATA}\n\nLive Inventory: {inventory_context}\nCurrent conversation: {json.dumps(context)}\nUser: {user_input}\n\nRespond concisely, no reasoning."

        # Call DeepSeek-R1 via Ollama for response
        response = ollama.chat(
            model="deepseek-r1:7b",
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.6}
        )
        bot_reply = response['message']['content'].strip()
        history.append({"role": "assistant", "content": bot_reply})

        return jsonify({"response": bot_reply})
    except Exception as e:
        print(f"Error in /chat: {e}")
        return jsonify({"error": "Something went wrong"}), HTTPStatus.INTERNAL_SERVER_ERROR

if __name__ == "__main__":
    # Run Flask app with debug mode for development
    app.run(host='0.0.0.0', port=5000, debug=True)