import chromadb
from chromadb.utils import embedding_functions
import os
from mongo_chat_platform.logger import logger

class ChromaService:
    def __init__(self, collection_name="mongo_schema_metadata"):
        logger.info(f"Initializing ChromaService for collection: {collection_name}")
        api_key = os.getenv("CHROMA_API_KEY")
        tenant = os.getenv("CHROMA_TENANT")
        database = os.getenv("CHROMA_DATABASE")
        
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        if api_key:
            # Cloud Client (User Preferred)
            try:
                # Cloud Client (User Preferred)
                logger.info("Connecting to ChromaDB Cloud...")
                self.client = chromadb.CloudClient(
                    api_key=api_key,
                    tenant=tenant,
                    database=database
                )
                # Use cosine similarity
                metadata = {"hnsw:space": "cosine"}
            except ValueError as e:
                # This catches the specific "Database ... does not match" error
                if "does not match" in str(e):
                    msg = (f"ChromaDB Configuration Error: The database name '{database}' "
                           f"does not match the one associated with yours API key. "
                           f"Please check your .env file or create the database in Chroma Cloud.")
                    logger.critical(msg)
                    raise ValueError(msg)
                raise e
            except Exception as e:
                logger.critical(f"Failed to connect to ChromaDB: {e}")
                raise e
        else:
            # Local Persistent Client (Fallback)
            logger.info("Connecting to local ChromaDB...")
            self.client = chromadb.PersistentClient(path="./chroma_db")
            metadata = None
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name, 
            embedding_function=self.embedding_fn,
            metadata=metadata
        )
        
        # Initialize second collection for chat history
        self.chat_collection = self.client.get_or_create_collection(
            name="mongo_chat_history",
            embedding_function=self.embedding_fn,
            metadata=metadata
        )
        logger.info(f"ChromaDB collection '{collection_name}' and 'mongo_chat_history' ready.")

    def store_schema(self, db_name, collection_name, schema_str):
        """
        Stores validation schema or sample document structure for a collection.
        ID format: dbname_collectionname
        """
        doc_id = f"{db_name}_{collection_name}"
        logger.info(f"Storing schema for {doc_id}")
        metadata = {"db_name": db_name, "collection_name": collection_name}
        
        # Upsert: Update if exists
        self.collection.upsert(
            documents=[schema_str],
            metadatas=[metadata],
            ids=[doc_id]
        )

    def store_chat_interaction(self, user_query, ai_response, session_id):
        """
        Stores Q&A pair in vector DB for semantic history retrieval.
        """
        import uuid
        interaction_id = str(uuid.uuid4())
        text = f"User: {user_query}\nAssistant: {ai_response}"
        metadata = {"session_id": session_id, "type": "chat_history"}
        
        logger.info(f"Storing chat interaction {interaction_id} in ChromaDB")
        self.chat_collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[interaction_id]
        )

    def retrieve_context(self, query, n_results=15):
        """
        Retrieves relevant schema/collection info based on user query.
        """
        logger.debug(f"Retrieving context for query: {query}")
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        found_count = len(results['documents'][0]) if results['documents'] else 0
        logger.debug(f"ChromaDB: Found {found_count} relevant schema documents")
        
        # Flatten results
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        
        return list(zip(documents, metadatas))

    def retrieve_chat_history(self, query, session_id, n_results=5):
        """
        Retrieves relevant past interactions from the vector DB.
        """
        results = self.chat_collection.query(
            query_texts=[query],
            n_results=n_results
            # where={"session_id": session_id} # Optional: Filter by session if needed, or leave open for global knowledge
        )
        found_count = len(results['documents'][0]) if results['documents'] else 0
        logger.debug(f"ChromaDB: Found {found_count} relevant history items")
        documents = results['documents'][0] if results['documents'] else []
        return documents
