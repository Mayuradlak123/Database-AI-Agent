from pymongo import MongoClient
import datetime
from pymongo import MongoClient
import datetime
import os
from mongo_chat_platform.logger import logger

class ConversationLogger:
    def __init__(self):
        # Use a separate env var for the app's own persistence, or fallback to a local default
        uri = os.getenv("MONGO_LOGS_URI")
        if not uri:
             logger.error("MONGO_LOGS_URI not set. Logging will fail.")
             raise ValueError("MONGO_LOGS_URI not set")
        
        try:
            self.client = MongoClient(uri)
            self.db = self.client.get_default_database()
            self.collection = self.db['chat_logs']
            logger.info("ConversationLogger initialized successfully")
        except Exception as e:
            logger.exception("Failed to initialize ConversationLogger")
            raise e

    def log_interaction(self, ip_address, session_id, user_query, ai_response):
        log_entry = {
            "ip_address": ip_address,
            "session_id": session_id,
            "timestamp": datetime.datetime.utcnow(),
            "interaction": {
                "user": user_query,
                "assistant": ai_response
            }
        }
        try:
            result = self.collection.insert_one(log_entry)
            logger.info(f"Interaction successfully persisted to MongoDB Logs. ID: {result.inserted_id}")
        except Exception as e:
            logger.critical(f"FATAL: Failed to insert log entry into MongoDB: {e}")
            # We print here as a last resort if the logger itself is failing or if this is running in a context where logger is silenced
            print(f"Error logging conversation: {e}")

    def get_history_by_ip(self, ip_address, limit=50):
        logger.debug(f"Retrieving history for IP: {ip_address}, Limit: {limit}")
        try:
            history = list(self.collection.find({"ip_address": ip_address}).sort("timestamp", -1).limit(limit))
            logger.debug(f"Retrieved {len(history)} past interactions")
            return history
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []
