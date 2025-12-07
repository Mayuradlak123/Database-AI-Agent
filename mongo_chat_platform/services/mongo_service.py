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

    def execute_tool_query(self, tool_input):
        """
        Executes a parsed JSON query action.
        Expected format:
        {
            "collection": "str",
            "action": "find/aggregate/count/distinct",
            "query": dict/list,
            "limit": int (optional)
        }
        """
        collection = tool_input.get('collection')
        action = tool_input.get('action')
        query = tool_input.get('query', {})
        
        logger.info(f"Executing tool action: {action} on {collection}")
        
        if not collection or collection not in self.get_collection_names():
            return f"Error: Collection '{collection}' does not exist."

        col_obj = self.db[collection]

        try:
            if action == 'find':
                limit = tool_input.get('limit', 5)
                # Ensure limit is reasonable
                limit = min(limit, 20)
                cursor = col_obj.find(query).limit(limit)
                results = list(cursor)
                formatted = json.dumps(results, default=str)
                return f"Found {len(results)} documents: {formatted}"
            
            elif action == 'aggregate':
                if not isinstance(query, list):
                    return "Error: Aggregation pipeline must be a list."
                # Safety: Basic check to prevent modifications (though user should be read-only ideally)
                unsafe_stages = ['$out', '$merge']
                for stage in query:
                    if any(k in unsafe_stages for k in stage.keys()):
                        return "Error: Write operations ($out, $merge) are not allowed."
                
                results = list(col_obj.aggregate(query))
                formatted = json.dumps(results, default=str)
                return f"Aggregation Result: {formatted}"
            
            elif action == 'count':
                count = col_obj.count_documents(query)
                return f"Count: {count}"
            
            elif action == 'distinct':
                field = tool_input.get('field')
                if not field:
                    return "Error: 'field' required for distinct."
                results = col_obj.distinct(field, query)
                return f"Distinct values for '{field}': {results[:50]}" # Limit output

            else:
                return f"Error: Unknown action '{action}'."

        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return f"Database Error: {str(e)}"

    def extract_schema_info(self):
        """
        Generates a summary of all collections and their sample structure.
        """
        logger.info("Extracting schema info from MongoDB")
        schemas = {}
        for col in self.get_collection_names():
             schemas[col] = self.get_sample_document(col)
        return schemas
