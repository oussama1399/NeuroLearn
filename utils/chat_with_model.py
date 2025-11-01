
from utils.rag_utils import (
    extract_data,
    sentence_chunking,
    create_embeddings,
    store_embeddings,
    retrieve_relevant_chunks,
    generate_prompt,
)
from utils.model_manager import ModelManager
import requests
import json



def chat_with_model(model_name, model_file="models.json"):
    manager = ModelManager(model_file=model_file)
    config = manager.get_model(model_name)
    print(f"Loaded config for '{model_name}':\n{config}")

    # Prepare RAG context if rag_file is present
    db = None
    if config.get("rag_file"):
        print("Preparing RAG context...")
        text = extract_data(config["rag_file"])
        chunks = sentence_chunking(text)
        embeddings = create_embeddings(chunks)
        db = store_embeddings(embeddings, chunks)

    # Chat loop
    while True:
        user_query = input("You: ")
        if user_query.lower() in ["exit", "quit"]:
            print("Exiting chat.")
            break

        # Retrieve context if RAG is enabled
        retrieved = []
        if db:
            result = retrieve_relevant_chunks(db, user_query, top_k=25)
            if result and isinstance(result, (list, tuple)) and len(result) > 0:
                # Protect against None or unexpected return types
                retrieved = result[0] or []
            else:
                retrieved = []
        prompt = generate_prompt(
            user_query,
            retrieved,
            system_prompt=config.get("system_prompt")
        )

        # Send to Ollama (or your LLM API)
        ollama_url = "http://localhost:80/api/generate"
        payload = {
            "model": config["model"],
            "prompt": prompt
        }
        try:
            response = requests.post(ollama_url, json=payload, stream=True)
            answer = ""
            for line in response.iter_lines():
                if line:
                    try:
                        data = line.decode("utf-8")
                        obj = json.loads(data)
                        answer += obj.get("response", "")
                    except Exception:
                        continue
            print("Bot:", answer)
        except requests.exceptions.ConnectionError:
            print("Could not connect to Ollama at http://localhost:80. Is the server running?")
            break