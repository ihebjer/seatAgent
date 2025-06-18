import os
import yaml
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredHTMLLoader,
    CSVLoader
)

class Constants:    
    def __init__(self):
        parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        config_path = os.path.join(parent_folder, "config.yaml")
        
        with open(config_path, 'r') as file:
            self.CONFIG = yaml.safe_load(file)
        
        # Set root directory to the parent folder of 'utils'
        self.CONFIG['directories']['root'] = parent_folder
        
        self.init_directories()
        self.init_model_settings()
        self.init_chroma_settings()
        self.init_document_loaders()
    
    def init_directories(self):
        self.ROOT_DIR = self.CONFIG['directories']['root']
        self.SOURCE_DOCS_DIR = os.path.join(self.ROOT_DIR, self.CONFIG['directories']['source_docs'])
        self.PROCESSED_DOCS_DIR = os.path.join(self.ROOT_DIR, self.CONFIG['directories']['processed_docs'])
        self.CHROMA_DB_DIR = os.path.join(self.ROOT_DIR, self.CONFIG['directories']['chroma_db'])
        self.LOGS_DIR = os.path.join(self.ROOT_DIR, self.CONFIG['directories']['logs'])
        
        for dir_path in [self.SOURCE_DOCS_DIR, self.PROCESSED_DOCS_DIR, 
                         self.CHROMA_DB_DIR, self.LOGS_DIR]:
            os.makedirs(dir_path, exist_ok=True)
    
    def init_model_settings(self):
        self.MODEL_PATH = self.CONFIG['model']['path']
        self.MODEL_GPU_LAYERS = self.CONFIG['model']['gpu_layers']
        self.BATCH_SIZE = self.CONFIG['model']['batch_size']
        self.CONTEXT_WINDOW = self.CONFIG['model']['context_window']
        self.SELECTED_EMBEDDING_MODEL = self.CONFIG['model']['embedding_model']
    
    def init_chroma_settings(self):
        self.CHROMA_SETTINGS = {
            "persist_directory": self.CHROMA_DB_DIR,
        }
    
    def init_document_loaders(self):
        self.DOCUMENT_LOADERS = {
            "pdf": PyPDFLoader,
            "docx": UnstructuredWordDocumentLoader,
            "html": UnstructuredHTMLLoader,
            "csv": CSVLoader
        }

CONST = Constants()