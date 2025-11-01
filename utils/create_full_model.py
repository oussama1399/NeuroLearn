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

def create_full_model(
    name,
    role,
    model_name,
    system_prompt,
    rag_file=None,
    chunk_size=7,
    overlap=1,
    embedding_model="all-MiniLM-L6-v2",
    metadata=None,
    model_file="models.json"
):
    # 1. Extract data from rag_file (if provided)
    if rag_file:
        print(f"Extracting data from: {rag_file}")
        text = extract_data(rag_file)
        print("Chunking sentences...")
        chunks = sentence_chunking(text, chunk_size=chunk_size, overlap=overlap)
        print("Creating embeddings...")
        embeddings = create_embeddings(chunks, model_name=embedding_model)
        print("Storing embeddings in ChromaDB...")
        store_embeddings(embeddings, chunks, metadata=metadata)
    else:
        print("No RAG file provided, skipping RAG pipeline.")

    # 2. Create and save model config
    manager = ModelManager(model_file=model_file)
    manager.create_model(
        name=name,
        role=role,
        model_name=model_name,
        system_prompt=system_prompt,
        rag_file=rag_file
    )
    print(f"Model '{name}' created and saved.")
