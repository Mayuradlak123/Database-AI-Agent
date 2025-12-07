import os
from groq import Groq
from django.conf import settings
from mongo_chat_platform.logger import logger

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
             # Fallback or error logging
             logger.warning("GROQ_API_KEY not found in environment variables.")
        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
        logger.info(f"LLMService initialized with model: {self.model}")

    def generate_response(self, system_prompt, user_query, conversation_history=None):
        """
        Generates a response from the LLM.
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        if conversation_history:
            for msg in conversation_history:
                messages.append(msg)
        
        messages.append({"role": "user", "content": user_query})

        try:
            logger.info(f"Generating LLM response. Model: {self.model}")
            logger.debug(f"Context Message Count: {len(messages)}")
            if len(messages) > 0:
                 logger.debug(f"System Prompt Preview: {messages[0]['content'][:100]}...")

            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1, # Low temperature for factual data querying
                max_tokens=1024,
                top_p=1,
                stream=False,
                stop=None,
            )
            response = completion.choices[0].message.content
            logger.info("LLM Response generated successfully")
            logger.debug(f"Response Preview: {response[:100]}...")
            return response
        except Exception as e:
            logger.exception(f"CRITICAL: Error communicating with Groq API: {str(e)}")
            return f"Error generating response: {str(e)}"

    def generate_mongo_query(self, schema_info, user_query, history=None):
        """
        Specialized method to generate MongoDB queries.
        """
        system_prompt = f"""
        You are an expert MongoDB developer. Your task is to generate a valid MongoDB query or aggregation pipeline based on the user's natural language request and the provided schema.
        
        Schema Information:
        {schema_info}
        
        Rules:
        1. Return ONLY the JSON query/pipeline. Do not include markdown formatting (like ```json), explanations, or comments.
        2. If an aggregation is needed, return a list [ {{...}}, {{...}} ].
        3. If a simple find is needed, return {{ ... }}.
        4. Use double quotes for keys.
        """
        return self.generate_response(system_prompt, user_query, history)
