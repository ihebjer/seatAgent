import sys
import os

# Add the parent directory of 'utils' to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import traceback
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from constants import CONST
import argparse
import warnings
import chromadb
from chromadb.config import Settings


class DocumentIngester:
    def __init__(self , config=None):
        """Initialize the DocumentIngester with configurations and setup."""
        os.environ["TRANSFORMERS_NO_TF"] = "1"
        warnings.filterwarnings("ignore")
    
        os.makedirs(CONST.LOGS_DIR, exist_ok=True)
        self.log_file = os.path.join(CONST.LOGS_DIR, "ingest.log")
        logging.basicConfig(filename=self.log_file, level=logging.INFO,
                            format="%(asctime)s - %(levelname)s - %(message)s")

        try:
            print("Initializing embeddings model...")
            self.embeddings = HuggingFaceEmbeddings(model_name=CONST.SELECTED_EMBEDDING_MODEL)
            print("Embeddings model initialized successfully.")

            print("Connecting to vector store...")
            self.vector_store = Chroma(
                persist_directory=CONST.CHROMA_DB_DIR,
                embedding_function=self.embeddings
            )
            print("Vector store connected successfully.")
        except Exception as e:
            print(f"❌ Error during initialization: {e}")
            raise

    def load_document(self, file_path):
        """Loads a document using an appropriate loader based on file extension."""
        ext = file_path.split(".")[-1].lower()
        try:
            if ext in CONST.DOCUMENT_LOADERS:
                print(f"Using loader for extension: {ext}")
                loader_class = CONST.DOCUMENT_LOADERS[ext]
                loader = loader_class(file_path)
                return loader.load()
            else:
                print(f"❌ No loader found for extension: {ext}")
        except Exception as e:
            print(f"❌ Error loading document {file_path}: {e}")
           
        return None

    def split_documents(self, documents):
        """Split markdown-structured documents using RecursiveCharacterTextSplitter with semantic-aware separators."""
        try:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,                      # finer chunks = better isolation
                chunk_overlap=75,                    # small overlap to maintain context
                separators=["\n\n", "\n", ".", " "]  # prioritize semantic splits (headers, paragraphs, sentences)
            )

            all_chunks = []

            for doc in documents:
                chunks = text_splitter.split_documents([doc])
                for chunk in chunks:
                    chunk.metadata.update(doc.metadata)
                all_chunks.extend(chunks)

            return all_chunks

        except Exception as e:
            print(f"❌ Error splitting documents: {e}")
            if self.debug:
                traceback.print_exc()
            return []

    def process_file(self, file_path):
        """Processes and embeds a single file."""
        try:
            logging.info(f"Processing {file_path}...")
            print(f"🔄 Attempting to load: {file_path}")

            documents = self.load_document(file_path)
            if not documents:
                print(f"❌ Failed to load document: {file_path}")
                return

            print(f"✅ Successfully loaded {file_path} - {len(documents)} pages")

            chunks = self.split_documents(documents)
            if not chunks:
                print(f"❌ No chunks generated for {file_path}")
                return

            print(f"✅ Successfully split {file_path} into {len(chunks)} chunks")

            print(f"Adding {len(chunks)} chunks to vector store...")
            # Create vector store from documents
            vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=CONST.CHROMA_DB_DIR,
                collection_metadata={"hnsw:M": 32, "hnsw:construction_ef": 64}  
            )
            vector_store.persist()

            print(f"✅ Successfully processed {file_path} and stored embeddings.")
            logging.info(f"Successfully processed {file_path}")

        except Exception as e:
            logging.error(f"❌ Error processing {file_path}: {e}")
            print(f"❌ Error processing {file_path}: {e}")
           

    def ingest_documents(self):
        """Ingests all documents from the source directory."""
        try:
            print(f"Looking for documents in: {CONST.SOURCE_DOCS_DIR}")

            if not os.path.exists(CONST.SOURCE_DOCS_DIR):
                print(f"❌ Source directory does not exist: {CONST.SOURCE_DOCS_DIR}")
                return

            files = [
                os.path.join(CONST.SOURCE_DOCS_DIR, f)
                for f in os.listdir(CONST.SOURCE_DOCS_DIR)
                if os.path.isfile(os.path.join(CONST.SOURCE_DOCS_DIR, f))
            ]

            if not files:
                print(f"📂 No documents found in the source directory: {CONST.SOURCE_DOCS_DIR}")
                logging.warning("No documents found in the source directory.")
                return

            print(f"Found {len(files)} files to process: {[os.path.basename(f) for f in files]}")

            for file_path in files:
                self.process_file(file_path)

            print("✅ Document ingestion completed!")

        except Exception as e:
            print(f"❌ Error during ingestion: {e}")
            logging.error(f"Error during ingestion: {e}")
           

    def list_documents(self):
        """Lists all stored documents in ChromaDB."""
        try:
            docs = self.vector_store.get(include=["metadatas"])
            if not docs["metadatas"]:
                print("📂 No documents found in ChromaDB.")
                return
            for idx, meta in enumerate(docs["metadatas"]):
                print(f"📄 {idx + 1}: {meta}")
        except Exception as e:
            print(f"❌ Error listing documents: {e}")
           
    def delete_document_by_id(self, doc_id):
        """Deletes a specific document by its ID."""
        try:
            self.vector_store.delete([doc_id])
            self.vector_store.persist()
            print(f"🗑️ Successfully deleted document with ID: {doc_id}")
        except Exception as e:
            print(f"❌ Error deleting document {doc_id}: {e}")
            

    def delete_all_documents(self):
        """Deletes all stored documents from ChromaDB."""
        try:
            if not self.vector_store:
                print("❌ Vector store not initialized.")
                return

            # Safely fetch documents (handle None case)
            docs = self.vector_store._collection.get(include=["documents"]) if self.vector_store._collection else None
            if not docs or not docs.get("ids"):
                print("📂 No documents found in ChromaDB to delete.")
                return

            print(f"Deleting {len(docs['ids'])} documents...")
            self.vector_store.delete(ids=docs["ids"])
            self.vector_store.persist()
            print("🚮 All documents have been deleted from ChromaDB.")
        except Exception as e:
            print(f"❌ Error deleting all documents: {e}")
            if hasattr(self, 'debug') and self.debug:  # Optional: Print traceback if debug=True
                traceback.print_exc()
          

def main():
    parser = argparse.ArgumentParser(description="Manage ChromaDB documents.")
    parser.add_argument("--list-docs", action="store_true", help="List all stored documents in ChromaDB.")
    parser.add_argument("--delete-doc", type=str, help="Delete a specific document by ID.")
    parser.add_argument("--delete-all", action="store_true", help="Delete all documents from ChromaDB.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode with detailed error information.")
    args = parser.parse_args()

    try:
        print("Initializing DocumentIngester...")
        ingester = DocumentIngester()  
        print("Initialization complete.")

        if args.list_docs:
            ingester.list_documents()
        elif args.delete_doc:
            ingester.delete_document_by_id(args.delete_doc)
        elif args.delete_all:
            ingester.delete_all_documents()
        else:
            ingester.ingest_documents()
    except Exception as e:
        print(f"❌ Critical error: {e}")
        if args.debug:
            traceback.print_exc()


if __name__ == "__main__":
    main()