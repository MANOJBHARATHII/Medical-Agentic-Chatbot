# Medical-Agentic-Chatbot
conda create -n project python=3.11 -y

conda activate project

pip install -r requirements.txt

The application uses Groq for chat and image questions. Knowledge-base embeddings
run locally with `sentence-transformers/all-MiniLM-L6-v2`; the model is downloaded
on first use. Pinecone stores those local vectors in the index configured in `.env`.

Set `GROQ_API_KEY`, `PINECONE_API_KEY`, `TAVILY_API_KEY`, and `API_TOKEN` in `.env`,
then start the server with `python -m uvicorn app.main:app --reload`. Open
`http://127.0.0.1:8000` and enter the `API_TOKEN`. Ingest the PDF with
`python ingest.py` before enabling knowledge-base search. Chat works without the
knowledge base when its checkbox is left unchecked.