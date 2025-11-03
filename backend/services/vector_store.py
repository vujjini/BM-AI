from langchain_qdrant import QdrantVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from config import settings
from typing import List
from langchain_core.documents import Document
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self):
        logger.info("Initializing vector store service...")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        # Initialize Qdrant client - supports both local and cloud setups
        if settings.QDRANT_URL:
            # Cloud setup with URL
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY
            )
        else:
            # Local setup with host and port
            logger.info("Using local Qdrant setup")
            self.client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT
            )
        logger.info("Qdrant client initialized successfully")
        self.collection_name = "building_logs"
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize Qdrant vector store with auto-collection creation"""
        try:
            # Check if Qdrant is running
            self._check_qdrant_connection()
            
            # Ensure collection exists
            self._ensure_collection_exists()
            
            # Initialize vector store
            self.vectorstore = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.embeddings
            )
            logger.info(f"Successfully initialized Qdrant vector store with collection '{self.collection_name}'")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {e}")
            logger.error("Make sure Qdrant is running locally on port 6333")
            logger.error("You can start Qdrant with Docker: docker run -p 6333:6333 qdrant/qdrant")
    
    def _check_qdrant_connection(self):
        """Check if Qdrant is running and accessible"""
        try:
            # Try to get collections to test connection (works with all Qdrant versions)
            collections = self.client.get_collections()
            logger.info(f"Connected to Qdrant successfully. Found {len(collections.collections)} collections.")
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Qdrant: {e}. Make sure Qdrant is running on {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    
    def _ensure_collection_exists(self):
        """Ensure the collection exists, create if it doesn't"""
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                logger.info(f"Collection '{self.collection_name}' not found. Creating...")
                
                # Create collection with appropriate vector configuration
                # Google's text-embedding-004 model produces 768-dimensional vectors
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,  # Google text-embedding-004 dimension
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Successfully created collection '{self.collection_name}'")
            else:
                logger.info(f"Collection '{self.collection_name}' already exists")
                
        except Exception as e:
            raise RuntimeError(f"Failed to ensure collection exists: {e}")
    
    def add_documents(self, documents: List[Document]):
        """Add documents to vector store"""
        if self.vectorstore and documents:
            self.vectorstore.add_documents(documents)
    
    def get_retriever(self, k: int = 3):
        """Get retriever for similarity search"""
        if self.vectorstore:
            return self.vectorstore.as_retriever(search_kwargs={"k": k})
        return None

# Global instance
vector_store_service = VectorStoreService()