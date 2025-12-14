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
    from datetime import datetime
    
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
            context_docs = chroma_service.retrieve_context(user_query, db_name=db_name, n_results=15)
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
            
            OBJECTIVE:
            Answer the user's question based on the schema and history.
            
            RULES for "Tool Use" vs "Code Generation":
            
            SCENARIO 1: AUTOMATIC DATA RETRIEVAL (The user wants the ANSWER)
            If the user asks "How many users?" or "List the top 5 companies", use the tool to get the real data.
            Output ONLY:
            <<<QUERY>>>
            {{
                "collection": "collection_name",
                "action": "find" or "count" or "aggregate" or "distinct",
                "query": {{ ...valid query... }},
                "limit": 5
            }}
            <<<END_QUERY>>>
            
            SCENARIO 2: CODE GENERATION (The user wants the CODE)
            If the user asks "How do I write a query to..." or "Give me the code for...", DO NOT USE <<<QUERY>>>.
            
            IMPORTANT: Do NOT use markdown code blocks (tripple backticks) or language tags (like json/javascript).
            Just write the code as plain text, indented if necessary.
            
            Example:
            Here is the query:
            
            db.collection.find({{ 
                "field": "value" 
            }})
            
            NEVER output the internal JSON tool format to the user in Scenario 2.
            """
            
            logger.info(f"Generating LLM response for query: {user_query}")
            
            # Simple conversation history formatting for LLM
            llm_history = [{"role": m['role'], "content": m['content']} for m in chat_history] 
            
            # 1. First Pass: Get Initial Response (Potential Tool Call)
            response = llm_service.generate_response(system_prompt, user_query, llm_history)
            
            # 2. Check for Tool Execution
            import re
            tool_match = re.search(r'<<<QUERY>>>(.*?)<<<END_QUERY>>>', response, re.DOTALL)
            
            if tool_match:
                try:
                    tool_json_str = tool_match.group(1).strip()
                    logger.info(f"Tool Call Detected: {tool_json_str}")
                    tool_input = json.loads(tool_json_str)
                    
                    # Execute Tool
                    tool_result = mongo_service.execute_tool_query(tool_input)
                    logger.info(f"Tool Result: {tool_result}")
                    
                    # Append execution to history context for final answer
                    # We simulate a "System" or "Tool" role interaction for the LLM context
                    tool_interaction = [
                        {"role": "assistant", "content": response}, # The tool call
                        {"role": "user", "content": f"Tool Execution Result: {tool_result}\n\nNow answer my original question based on this result."}
                    ]
                    
                    # 3. Second Pass: Get Final Answer based on Data
                    final_response = llm_service.generate_response(system_prompt, user_query, llm_history + tool_interaction)
                    response = final_response # Override response with the actual answer
                    
                except json.JSONDecodeError:
                    logger.error("Failed to parse tool JSON")
                    response += "\n(System: Failed to execute query due to invalid JSON format)"
                except Exception as e:
                    logger.error(f"Tool execution loop failed: {e}")
                    response += f"\n(System: Tool execution error: {str(e)})"

            # Update History
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            chat_history.append({'role': 'user', 'content': user_query, 'timestamp': timestamp})
            chat_history.append({'role': 'assistant', 'content': response, 'timestamp': timestamp})
            
            # Log Interaction Persistently
            # getting IP
            def get_system_ip():
                """
                Attempts to get the actual LAN IPv4 of the host machine
                instead of returning 127.0.0.1 for local vs local connections.
                """
                import socket
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    # This doesn't actually connect, but allows us to see what interface 
                    # would be used to reach an external IP (8.8.8.8)
                    s.connect(('8.8.8.8', 80))
                    IP = s.getsockname()[0]
                    s.close()
                    return IP
                except Exception:
                    return '127.0.0.1'

            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
                
            # If detecting localhost, try to get the real System IP for better history tracking
            if ip in ['127.0.0.1', '::1']:
                ip = get_system_ip()
                
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
                return JsonResponse({
                    'success': True, 
                    'response': response, 
                    'user_query': user_query,
                    'timestamp': timestamp
                })

    context = {
        'db_name': db_name,
        'chat_history': chat_history
    }
    return render(request, 'chat/interface.html', context)
