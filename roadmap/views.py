from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from config.views import require_edit_mode, get_current_app_mode
import json 
from .models import Phase, Task
# Create your views here.

def index(request):
    is_superuser = request.user.is_authenticated and request.user.is_superuser
    mode = get_current_app_mode(request)
    return render(request, 'roadmap/index.html', {'is_superuser': is_superuser, 'app_mode': mode})

DEFAULT_PHASES = [
    ('setup', 'Setup', '#6B8DE3', '#E0E8FF', 1),
    ('empathise', 'Empathise (Diagnostic)', '#9B7FD4', '#EDE5FF', 2),
    ('define', 'Define (Analysis)', '#2ECC71', '#D5F5E3', 3),
    ('ideate', 'Ideate & Prototype (Design)', '#E8837C', '#FFE5E2', 4),
    ('test', 'Test (Execution)', '#E8A87C', '#FFF0E0', 5),
    ('milestone', 'Academic Schedule', '#E63946', '#FFE0E3', 6),
]

def ensure_default_phases():
    if not Phase.objects.exists():
        for pid, name, colour, bg, order in DEFAULT_PHASES:
            Phase.objects.create(
                phase_id=pid,
                name=name,
                colour=colour,
                bg=bg,
                order=order
            )

def get_roadmap_data(request):
    ensure_default_phases()
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
    
    tasks = Task.objects.select_related('phase').all().order_by('phase__order', 'order', 'id')
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
            'order': t.order,
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
            if 'order' in data and data['order'] is not None:
                task.order = data['order']
            task.save() 
        else:
            if 'order' in data and data['order'] is not None:
                task_order = data['order']
            else:
                from django.db.models import Max
                max_order = Task.objects.filter(phase=phase).aggregate(Max('order'))['order__max']
                task_order = (max_order + 1) if max_order is not None else 1

            task = Task.objects.create(
                title = name,
                phase = phase,
                start_date = start_date,
                end_date = end_date,
                status = status,
                deliverables = deliverables,
                order = task_order
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
def reorder_tasks(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked
    
    try:
        data = json.loads(request.body)
        task_orders = data.get('task_orders', []) if isinstance(data, dict) else data
        if not isinstance(task_orders, list):
            return JsonResponse({'status': 'error', 'message': 'task_orders must be a list'}, status=400)
        
        with transaction.atomic():
            for idx, item in enumerate(task_orders):
                if isinstance(item, dict):
                    t_id = item.get('id')
                    order_val = item.get('order', idx + 1)
                    phase_id = item.get('phaseId')
                else:
                    t_id = str(item)
                    order_val = idx + 1
                    phase_id = None

                if not t_id:
                    continue

                update_kwargs = {'order': order_val}
                if phase_id:
                    p = Phase.objects.filter(phase_id=phase_id).first()
                    if p:
                        update_kwargs['phase'] = p
                
                Task.objects.filter(id=t_id).update(**update_kwargs)
                
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
                
            phase_order_counter = {}
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
                    # Look up matching default phase color/bg if available
                    matched = next((p for p in DEFAULT_PHASES if p[0] == phase_id), None)
                    p_name = matched[1] if matched else f"Phase {phase_id}"
                    p_col = matched[2] if matched else '#3b82f6'
                    p_bg = matched[3] if matched else '#dbeafe'
                    p_ord = matched[4] if matched else 99

                    phase, _ = Phase.objects.get_or_create(
                        phase_id=phase_id or 'setup',
                        defaults={'name': p_name, 'colour': p_col, 'bg': p_bg, 'order': p_ord}
                    )

                p_key = phase.phase_id
                if p_key not in phase_order_counter:
                    from django.db.models import Max
                    max_o = Task.objects.filter(phase=phase).aggregate(Max('order'))['order__max']
                    phase_order_counter[p_key] = max_o if max_o is not None else 0
                phase_order_counter[p_key] += 1
                item_order = item.get('order', phase_order_counter[p_key])

                Task.objects.create(
                    title=name,
                    phase=phase,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,
                    deliverables=deliverables,
                    order=item_order
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







