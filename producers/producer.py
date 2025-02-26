from confluent_kafka import Producer
import json
import time
import random

p = Producer({'bootstrap.servers': 'localhost:9092'})
products = ["Wireless Earbuds", "Smartwatch", "Leather Jacket", "LED Desk Lamp"]

while True:
    item = random.choice(products)
    stock = random.randint(1, 10)
    data = {"item": item, "stock": stock, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
    p.produce('inventory_updates', json.dumps(data).encode('utf-8'))
    p.flush()
    print(f"Produced: {data}")
    time.sleep(5)