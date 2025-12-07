from pymongo import MongoClient
import json
from mongo_chat_platform.logger import logger

class MongoService:
    def __init__(self, uri, db_name=None):
        logger.info("Initializing MongoService")
        self.client = MongoClient(uri)
        if db_name:
            self.db = self.client[db_name]
        else:
            self.db = self.client.get_default_database()

    def get_collection_names(self):
        try:
            names = self.db.list_collection_names()
            logger.debug(f"Retrieved {len(names)} collections: {names}")
            return names
        except Exception as e:
            logger.error(f"Failed to list collection names: {e}")
            raise e

    def get_sample_document(self, collection_name):
        logger.debug(f"Fetching sample document for collection: {collection_name}")
        try:
            doc = self.db[collection_name].find_one()
            if doc:
                # removing ObjectId for clearer schema representation
                if '_id' in doc:
                    del doc['_id']
                logger.debug(f"Sample retrieved for {collection_name}")
                return json.dumps(doc, default=str)
            logger.warning(f"No documents found in collection: {collection_name}")
            return "{}"
        except Exception as e:
            logger.error(f"Error fetching sample from {collection_name}: {e}")
            return "{}"

    def execute_query(self, query_str):
        """
        Executes a raw query string (simplified implementation).
        WARNING: This is risky. Real implementation needs safe parsing.
        """
        logger.info(f"Preparing to execute query: {query_str}")
        # Very basic unsafe parsing for POC
        # Expecting JSON like { "field": "value" } or [{ "$group": ... }]
        try:
            query = json.loads(query_str)
            logger.debug(f"Parsed query JSON: {query}")
            
            # Heuristic: List = Aggregation, Dict = Find
            # We don't know which collection to target from the query string alone easily without parsing.
            # So we probably need the LLM to tell us the collection OR we guess.
            # Updated: We will ask LLM to return { "collection": "name", "pipeline": [...] }
            logger.warning("Query execution attempted but not fully implemented.")
            return "Execution not fully implemented without query parsing safety."
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in query string: {e}")
            return f"Invalid JSON: {str(e)}"
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return str(e)

    def extract_schema_info(self):
        """
        Generates a summary of all collections and their sample structure.
        """
        logger.info("Extracting schema info from MongoDB")
        schemas = {}
        for col in self.get_collection_names():
             schemas[col] = self.get_sample_document(col)
        return schemas
