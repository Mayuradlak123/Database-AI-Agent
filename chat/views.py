from django.shortcuts import render, redirect
from django.contrib import messages
from mongo_chat_platform.services.mongo_service import MongoService
from mongo_chat_platform.services.chroma_service import ChromaService
from mongo_chat_platform.services.llm_service import LLMService
from mongo_chat_platform.services.logging_service import ConversationLogger
from mongo_chat_platform.logger import logger
from django.http import JsonResponse
import json

def chat_interface(request):
    # 1. Check Session
    mongo_uri = request.session.get('mongo_uri')
    if not mongo_uri:
        logger.warning("Attempted to access chat without active session")
        return redirect('connect:home')
    
    db_name = request.session.get('db_name')
    
    # Initialize Services
    try:
        mongo_service = MongoService(mongo_uri, db_name)
        # Note: In a real app, instantiate services as singletons or carefully to avoid overhead
        chroma_service = ChromaService()
        llm_service = LLMService()
        logger_service = ConversationLogger()
    except Exception as e:
        logger.critical(f"Service initialization failed: {e}")
        messages.error(request, f"Service Initialization Failed: {str(e)}")
        return redirect('connect:home')

    # 2. Indexing (If not done for this session)
    if not request.session.get('is_indexed'):
        try:
            logger.info("Starting schema indexing...")
            schema_info = mongo_service.extract_schema_info()
            for col_name, schema in schema_info.items():
                chroma_service.store_schema(db_name, col_name, schema)
            request.session['is_indexed'] = True
            logger.info("Schema indexing completed")
            messages.success(request, "Database schema indexed successfully!")
        except Exception as e:
            logger.error(f"Schema indexing failed: {e}")
            messages.warning(request, f"Indexing failed: {str(e)}. Chat may be less accurate.")

    # 3. Handle Chat Interaction
    chat_history = request.session.get('chat_history', [])

    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        
        if is_ajax:
            try:
                data = json.loads(request.body)
                user_query = data.get('query')
            except:
                user_query = None
        else:
            user_query = request.POST.get('query')

        if user_query:
            # Add User Query to History (Temp for Context)
            # Note: We append to the session history at the end
            
            # RAG Retrieval (Schema)
            context_docs = chroma_service.retrieve_context(user_query, n_results=15)
            context_str = "\n".join([f"Collection: {meta['collection_name']}\nSchema Sample: {doc}" for doc, meta in context_docs])
            
            # RAG Retrieval (History)
            similar_chats = chroma_service.retrieve_chat_history(user_query, request.session.session_key)
            history_context = "\n".join([f"Past Interaction: {chat}" for chat in similar_chats])
            
            # Generate Response
            system_prompt = f"""
            You are a helpful assistant for a MongoDB database.
            Connected Database: {db_name}
            
            Relevant Collections & Schemas:
            {context_str}
            
            Relevant Past Conversations:
            {history_context}
            
            Answer the user's question based on the schema and history.
            If the user asks for a query, output valid MongoDB JSON/Aggregation.
            If the user just asks for information that requires querying the DB, tell them you can generate a query for it.
            """
            
            logger.info(f"Generating LLM response for query: {user_query}")
            
            # Simple conversation history formatting for LLM
            llm_history = [{"role": m['role'], "content": m['content']} for m in chat_history] 
            
            response = llm_service.generate_response(system_prompt, user_query, llm_history)
            
            # Update History
            chat_history.append({'role': 'user', 'content': user_query})
            chat_history.append({'role': 'assistant', 'content': response})
            
            # Log Interaction Persistently
            # getting IP
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
                
            try:
                # Log to Mongo Logger (Audit)
                logger_service.log_interaction(ip, request.session.session_key, user_query, response)
                
                # Store in ChromaDB (Vector Memory)
                chroma_service.store_chat_interaction(user_query, response, request.session.session_key)
                
                logger.debug(f"Logged interaction for IP: {ip}")
            except Exception as e:
                logger.error(f"Logging interaction failed: {e}")
                print(f"Logging failed: {e}")

            # Update Session
            request.session['chat_history'] = chat_history
            request.session.modified = True
            
            if is_ajax:
                return JsonResponse({'success': True, 'response': response, 'user_query': user_query})

    context = {
        'db_name': db_name,
        'chat_history': chat_history
    }
    return render(request, 'chat/interface.html', context)
