import json
from io import StringIO
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.management import call_command
from config.views import require_edit_mode
from .models import WeeklyTask


def cadence_dashboard(request):
    """Renders the Weekly Cadence Dashboard."""
    tasks = WeeklyTask.objects.all().order_by('day_of_week', 'time', 'id')
    mode = request.session.get('app_mode', 'view')
    return render(request, 'role_rotation/dashboard.html', {
        'tasks': tasks,
        'weekdays': WeeklyTask.WEEKDAYS,
        'app_mode': mode,
    })


def get_tasks(request):
    """Returns JSON representation of all weekly tasks."""
    tasks = WeeklyTask.objects.all().order_by('day_of_week', 'time', 'id')
    task_list = []
    for t in tasks:
        task_list.append({
            'id': t.id,
            'title': t.title,
            'description': t.description,
            'day_of_week': t.day_of_week,
            'day_name': t.get_day_of_week_display(),
            'time': t.time or '',
            'assigned_person': t.assigned_person or '',
            'is_completed': t.is_completed,
            'created_at': t.created_at.strftime('%Y-%m-%d %H:%M:%S') if t.created_at else '',
        })
    return JsonResponse({'status': 'success', 'tasks': task_list})


@csrf_exempt
def save_task(request):
    """Create or update a weekly task."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        data = request.POST

    task_id = data.get('id') or data.get('task_id')
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    day_of_week = data.get('day_of_week')
    time_val = data.get('time', '').strip()
    assigned_person = data.get('assigned_person', '').strip()
    is_completed = data.get('is_completed', False)

    if not title:
        return JsonResponse({'status': 'error', 'message': 'Title is required'}, status=400)

    try:
        day_of_week = int(day_of_week)
        if day_of_week < 1 or day_of_week > 5:
            day_of_week = 1
    except (ValueError, TypeError):
        day_of_week = 1

    if task_id:
        try:
            task = WeeklyTask.objects.get(id=task_id)
            task.title = title
            task.description = description
            task.day_of_week = day_of_week
            task.time = time_val
            task.assigned_person = assigned_person
            task.is_completed = bool(is_completed)
            task.save()
        except WeeklyTask.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
    else:
        task = WeeklyTask.objects.create(
            title=title,
            description=description,
            day_of_week=day_of_week,
            time=time_val,
            assigned_person=assigned_person,
            is_completed=bool(is_completed)
        )

    return JsonResponse({
        'status': 'success',
        'task': {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'day_of_week': task.day_of_week,
            'day_name': task.get_day_of_week_display(),
            'time': task.time,
            'assigned_person': task.assigned_person,
            'is_completed': task.is_completed,
        }
    })


@csrf_exempt
def toggle_task(request, task_id):
    """Toggle completion status (optional)."""
    if request.method not in ['POST', 'GET']:
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    try:
        task = WeeklyTask.objects.get(id=task_id)
        task.is_completed = not task.is_completed
        task.save()
        return JsonResponse({
            'status': 'success',
            'task_id': task.id,
            'is_completed': task.is_completed
        })
    except WeeklyTask.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)


@csrf_exempt
def delete_task(request, task_id):
    """Delete a weekly task."""
    if request.method not in ['POST', 'DELETE', 'GET']:
        return JsonResponse({'status': 'error', 'message': 'Invalid HTTP method'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    try:
        task = WeeklyTask.objects.get(id=task_id)
        task.delete()
        return JsonResponse({'status': 'success', 'deleted_id': task_id})
    except WeeklyTask.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)


@csrf_exempt
def reset_weekly_progress(request):
    """Clear or reset tasks."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    updated_count = WeeklyTask.objects.all().update(is_completed=False)
    return JsonResponse({
        'status': 'success',
        'message': f'Reset state for {updated_count} task(s).'
    })


import sys
import threading

def _async_send_friday(recipient):
    try:
        from django.core.management import call_command
        out = StringIO()
        call_command('send_friday_reminder', recipient=recipient, stdout=out)
        print("Background Friday Email Success:", out.getvalue())
    except Exception as e:
        print("Async Friday Email Error:", e)

def _async_send_monday(recipient):
    try:
        from django.core.management import call_command
        out = StringIO()
        if recipient:
            call_command('send_monday_reminder', recipient=recipient, stdout=out)
        else:
            call_command('send_monday_reminder', stdout=out)
        print("Background Monday Email Success:", out.getvalue())
    except Exception as e:
        print("Async Monday Email Error:", e)

@csrf_exempt
def trigger_friday_reminder(request):
    """Trigger Friday email reminder."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    recipient = None
    if request.body:
        try:
            data = json.loads(request.body)
            if data.get('recipient'):
                recipient = data.get('recipient')
        except (json.JSONDecodeError, TypeError):
            pass

    if 'test' in sys.argv:
        _async_send_friday(recipient)
    else:
        t = threading.Thread(target=_async_send_friday, args=(recipient,), daemon=False)
        t.start()

    return JsonResponse({
        'status': 'success',
        'message': 'Friday reminder email sent successfully.'
    })


@csrf_exempt
def trigger_monday_reminder(request):
    """Trigger Monday email reminder."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    recipient = None
    if request.body:
        try:
            data = json.loads(request.body)
            if data.get('recipient'):
                recipient = data.get('recipient')
        except (json.JSONDecodeError, TypeError):
            pass

    if 'test' in sys.argv:
        _async_send_monday(recipient)
    else:
        t = threading.Thread(target=_async_send_monday, args=(recipient,), daemon=False)
        t.start()

    return JsonResponse({
        'status': 'success',
        'message': 'Monday 8:00 AM update email sent successfully.'
    })



def download_template(request, recipient):
    """Serves downloadable Word document template files for James or Michel."""
    import os
    from django.http import FileResponse, Http404

    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, 'static', 'role_rotation', 'templates')
    root_dir = os.path.dirname(base_dir)
    
    recipient_lower = recipient.lower()
    if 'james' in recipient_lower:
        file_path = os.path.join(templates_dir, 'James_Brief_Weekly_Report_Template.docx')
        if not os.path.exists(file_path):
            file_path = os.path.join(root_dir, '[James version Template] [BDO MBUA Project] Brief Weekly Report.docx')
        filename = '[James Template] [BDO MBUA Project] Brief Weekly Report.docx'
    elif 'michel' in recipient_lower or 'michael' in recipient_lower:
        file_path = os.path.join(templates_dir, 'Michel_Brief_Weekly_Report_Template.docx')
        if not os.path.exists(file_path):
            file_path = os.path.join(root_dir, '[Michael version Template] BriefWeeklyReport.docx')
        filename = '[Michel Template] [BDO MBUA Project] Brief Weekly Report.docx'
    else:
        raise Http404("Template recipient not found")
        
    if not os.path.exists(file_path):
        raise Http404("Template file not found")
        
    response = FileResponse(open(file_path, 'rb'), content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

