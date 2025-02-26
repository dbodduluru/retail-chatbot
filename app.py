from flask import Flask, request, jsonify, render_template
from confluent_kafka import Consumer, KafkaException
import ollama
import json
import threading
from http import HTTPStatus

app = Flask(__name__)
history = []

# Load static training data
with open('training_data.txt', 'r') as f:
    TRAINING_DATA = f.read()

# Kafka consumer setup
kafka_conf = {
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'retail-chatbot-group',
    'auto.offset.reset': 'latest'
}
consumer = Consumer(kafka_conf)
consumer.subscribe(['inventory_updates'])
inventory_data = {}

def kafka_listener():
    while True:
        try:
            msg = consumer.poll(timeout=1.0)
            if msg is None: continue
            if msg.error():
                raise KafkaException(msg.error())
            data = json.loads(msg.value().decode('utf-8'))
            item = data.get('item')
            if item:
                inventory_data[item] = data
            print(f"Kafka inventory update: {data}")
        except Exception as e:
            print(f"Kafka error: {e}")

threading.Thread(target=kafka_listener, daemon=True).start()

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

        inventory_context = json.dumps(inventory_data) if inventory_data else "No live inventory updates yet."
        prompt = f"{TRAINING_DATA}\n\nLive Inventory: {inventory_context}\nCurrent conversation: {json.dumps(context)}\nUser: {user_input}"

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
    app.run(host='0.0.0.0', port=5000, debug=True)