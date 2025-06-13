from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from constants import CONST

embeddings = HuggingFaceEmbeddings(model_name=CONST.SELECTED_EMBEDDING_MODEL)
vector_store = Chroma(persist_directory=CONST.CHROMA_DB_DIR, embedding_function=embeddings)
doc_count = vector_store._collection.count()
print(f"✅ ChromaDB contains {doc_count} stored documents.")
