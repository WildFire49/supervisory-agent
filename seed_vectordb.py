import os
import chromadb
import dotenv
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Load environment variables from .env file
dotenv.load_dotenv()

# --- Configuration ---
CHROMA_HOST = '3.6.132.24'
CHROMA_PORT = 8000
COLLECTION_NAME = "jlg_docs"
DOCUMENTS_DIR = "data/documents"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

def load_documents():
    """Loads all .pdf and .docx files from the specified directory."""
    documents = []
    print(f"Loading documents from '{DOCUMENTS_DIR}'...")
    if not os.path.exists(DOCUMENTS_DIR):
        print(f"Error: Directory '{DOCUMENTS_DIR}' not found.")
        return []
        
    for filename in os.listdir(DOCUMENTS_DIR):
        filepath = os.path.join(DOCUMENTS_DIR, filename)
        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
                documents.extend(loader.load())
                print(f"- Loaded {filename}")
            elif filename.endswith(".docx"):
                loader = Docx2txtLoader(filepath)
                documents.extend(loader.load())
                print(f"- Loaded {filename}")
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            
    print(f"Total documents loaded: {len(documents)}")
    return documents

def main():
    """Main function to process and upload documents to ChromaDB."""
    # 1. Get OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in .env file. Please ensure it is set.")
        return

    # 2. Load documents from the directory
    docs = load_documents()
    if not docs:
        print("No documents found to process. Please add files to the 'data/documents' directory.")
        return

    # 3. Split documents into chunks
    print("Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    splits = text_splitter.split_documents(docs)
    print(f"Created {len(splits)} text chunks.")

    # 4. Initialize OpenAI embeddings
    print("Initializing OpenAI embeddings...")
    embeddings = OpenAIEmbeddings(openai_api_key=api_key)

    # 5. Connect to ChromaDB and upload documents
    print(f"Connecting to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT} and seeding collection '{COLLECTION_NAME}'...")
    try:
        # The LangChain Chroma class handles connecting, creating the collection if it doesn't exist,
        # and adding the documents with their embeddings all in one step.
        db = Chroma.from_documents(
            documents=splits,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            client=chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        )
        print("\n--- Seeding Complete! ---")
        # Verify the number of documents in the collection
        client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
        collection = client.get_collection(name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' now contains {collection.count()} documents.")

    except Exception as e:
        print(f"An error occurred while seeding ChromaDB: {e}")

if __name__ == "__main__":
    main()

