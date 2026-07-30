from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from config.views import require_edit_mode
import json 
from .models import Phase, Task
# Create your views here.

def index(request):
    is_superuser = request.user.is_authenticated and request.user.is_superuser
    mode = request.session.get('app_mode', 'view')
    return render(request, 'roadmap/index.html', {'is_superuser': is_superuser, 'app_mode': mode})

def get_roadmap_data(request):
    phases = list(Phase.objects.all().order_by('order').values('phase_id', 'name', 'colour', 'bg'))

    formatted_phases = []
    for p in phases:
        formatted_phases.append({
            'id': p['phase_id'],
            'name': p['name'],
            'colour': p['colour'],
            'color': p['colour'],
            'bg': p['bg'],
        })
    
    tasks = Task.objects.select_related('phase').all()
    formatted_tasks = []
    for t in tasks:
        formatted_tasks.append({
            'id': str(t.id),
            'name': t.title,
            'phaseId': t.phase.phase_id,
            'startDate': t.start_date.strftime('%Y-%m-%d'),
            'endDate': t.end_date.strftime('%Y-%m-%d'),
            'status': t.status,
            'deliverables': t.deliverables or '',
        })
    
    return JsonResponse({'phases': formatted_phases, 'tasks': formatted_tasks})

@csrf_exempt 
def save_task(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked
    
    try:
        data = json.loads(request.body)
        phase_id = data.get('phaseId')
        if not phase_id:
            return JsonResponse({'status': 'error', 'message': 'phaseId is required'}, status=400)
            
        phase = Phase.objects.get(phase_id=phase_id)

        task_id = data.get('id')
        name = data.get('name')
        start_date = data.get('startDate') or data.get('start_date')
        end_date = data.get('endDate') or data.get('end_date')
        status = data.get('status', 'todo')
        deliverables = data.get('deliverables', '')

        if not name or not start_date or not end_date:
            return JsonResponse({'status': 'error', 'message': 'name, startDate, and endDate are required'}, status=400)

        if task_id:
            task = Task.objects.get(id=task_id)
            task.title = name
            task.phase = phase 
            task.start_date = start_date
            task.end_date = end_date
            task.status = status 
            task.deliverables = deliverables
            task.save() 
        else:
            task = Task.objects.create(
                title = name,
                phase = phase,
                start_date = start_date,
                end_date = end_date,
                status = status,
                deliverables = deliverables
            )
        
        return JsonResponse({'status': 'success', 'id': str(task.id)})
    
    except Phase.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Phase not found'}, status=400)
    except Task.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

from django.db import transaction

@csrf_exempt
def delete_task(request, task_id):
    if request.method not in ['DELETE', 'POST']:
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked
    
    try:
        Task.objects.filter(id=task_id).delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
def import_tasks(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked
    
    try:
        data = json.loads(request.body)
        
        if isinstance(data, list):
            tasks_data = data
            clear_existing = False
        elif isinstance(data, dict):
            tasks_data = data.get('tasks', [])
            clear_existing = data.get('clear_existing', False)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)

        if not isinstance(tasks_data, list):
            return JsonResponse({'status': 'error', 'message': 'tasks must be an array'}, status=400)

        imported_count = 0
        with transaction.atomic():
            if clear_existing:
                Task.objects.all().delete()
                
            for item in tasks_data:
                name = item.get('name') or item.get('title')
                phase_id = item.get('phaseId') or item.get('phase_id') or item.get('phase')
                start_date = item.get('startDate') or item.get('start_date')
                end_date = item.get('endDate') or item.get('end_date')
                status = item.get('status', 'todo')
                deliverables = item.get('deliverables', '')

                if not name or not phase_id or not start_date or not end_date:
                    continue

                phase = Phase.objects.filter(phase_id=phase_id).first()
                if not phase:
                    phase = Phase.objects.first()

                if phase:
                    Task.objects.create(
                        title=name,
                        phase=phase,
                        start_date=start_date,
                        end_date=end_date,
                        status=status,
                        deliverables=deliverables
                    )
                    imported_count += 1

        return JsonResponse({'status': 'success', 'imported_count': imported_count})
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def verify_superuser_password(password, username=None):
    if not password:
        return False, "Superuser password is required."
    if username:
        user = authenticate(username=username, password=password)
        if user and user.is_superuser and user.is_active:
            return True, None
        return False, "Invalid superuser credentials."
    
    superusers = User.objects.filter(is_superuser=True, is_active=True)
    if not superusers.exists():
        return False, "No superuser found in database. Please create a superuser first via 'python manage.py createsuperuser'."
    
    for user in superusers:
        if user.check_password(password):
            return True, None
            
    return False, "Invalid superuser password."


@csrf_exempt
def clear_all_tasks(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked
    
    try:
        data = json.loads(request.body)
        password = data.get('password', '')
        username = data.get('username', None)
        
        is_valid, err_msg = verify_superuser_password(password, username)
        if not is_valid:
            return JsonResponse({'status': 'error', 'message': err_msg}, status=403)

        count, _ = Task.objects.all().delete()
        return JsonResponse({'status': 'success', 'deleted_count': count})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)







