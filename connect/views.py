from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import MongoConnectionForm
from pymongo import MongoClient
import pymongo
from django.urls import reverse
from mongo_chat_platform.logger import logger
from django.http import JsonResponse
import json

def connect_view(request):
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json'
        
        if is_ajax:
            try:
                data = json.loads(request.body)
                uri = data.get('mongo_uri')
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
        else:
            form = MongoConnectionForm(request.POST)
            if form.is_valid():
                uri = form.cleaned_data['mongo_uri']
            else:
                return render(request, 'connect/index.html', {'form': form})

        if uri:
            try:
                logger.info(f"Attempting MongoDB connection for URI: {uri.split('@')[-1]}") # Log without credentials
                # 1. Attempt to connect
                client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                # 2. Verify connection by running a ping command
                client.admin.command('ping')
                logger.info("MongoDB connection verification successful")
                
                # 3. Store URI in session (In production, encrypt this!)
                request.session['mongo_uri'] = uri
                
                # 4. Get database name
                try:
                    db_name = client.get_default_database().name
                except:
                    db_name = None 
                
                request.session['db_name'] = db_name

                success_msg = f"Successfully connected to MongoDB! {f'Database: {db_name}' if db_name else ''}"
                
                if is_ajax:
                     return JsonResponse({'success': True, 'message': success_msg, 'redirect_url': reverse('chat:interface')})
                else:
                    messages.success(request, success_msg)
                    return redirect('chat:interface') 

            except pymongo.errors.ConfigurationError as e:
                err_msg = f"Configuration Error: {str(e)}"
                logger.error(err_msg)
                if is_ajax: return JsonResponse({'success': False, 'message': err_msg}, status=400)
                messages.error(request, err_msg)
            except pymongo.errors.OperationFailure as e:
                err_msg = f"Authentication Failed: {str(e)}"
                logger.error(err_msg)
                if is_ajax: return JsonResponse({'success': False, 'message': err_msg}, status=401)
                messages.error(request, err_msg)
            except Exception as e:
                err_msg = f"Connection Failed: {str(e)}"
                logger.error(err_msg)
                if is_ajax: return JsonResponse({'success': False, 'message': err_msg}, status=500)
                messages.error(request, err_msg)
        
        if not is_ajax:
             # Form invalid fallthrough (should be covered above but good for safety)
             return render(request, 'connect/index.html', {'form': MongoConnectionForm(request.POST)})

    else:
        form = MongoConnectionForm()

    return render(request, 'connect/index.html', {'form': form})

def logout_view(request):
    logger.info("User disconnected from MongoDB session")
    request.session.flush()
    messages.info(request, "You have been disconnected.")
    return redirect('connect:home')
