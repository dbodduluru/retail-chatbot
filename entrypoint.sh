#!/bin/bash
ollama serve &
for i in {1..10}; do
    if curl -s http://127.0.0.1:11434 > /dev/null; then
        echo "Ollama is up!"
        break
    fi
    echo "Waiting for Ollama... ($i/10)"
    sleep 1
done
if ! ollama list | grep -q "deepseek-r1:7b"; then
    echo "Pulling deepseek-r1:7b..."
    ollama pull deepseek-r1:7b
fi
exec python app.py