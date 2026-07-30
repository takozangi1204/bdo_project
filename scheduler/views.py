import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Category, Event, Todo, SchedulerSetting, BreakPeriod
from config.views import require_edit_mode


def index(request):
    """Serve the Scheduler main page."""
    mode = request.session.get('app_mode', 'view')
    return render(request, 'scheduler/index.html', {'app_mode': mode})


def get_scheduler_data(request):
    """Return all scheduler data as JSON."""
    categories = list(Category.objects.all().values(
        'cat_id', 'name', 'color', 'bg', 'sort_order'))

    events = list(Event.objects.all().values(
        'event_id', 'series_id', 'date', 'category_id', 'title',
        'url', 'start_time', 'end_time'))

    todos = list(Todo.objects.all().values(
        'todo_id', 'date', 'category_id', 'title', 'url',
        'completed', 'sort_order'))

    settings_qs = SchedulerSetting.objects.all()
    settings = {s.key: s.value for s in settings_qs}

    breaks = list(BreakPeriod.objects.all().values(
        'break_id', 'name', 'start_date', 'end_date'))

    # Convert date fields to strings
    for e in events:
        e['date'] = str(e['date'])
    for t in todos:
        t['date'] = str(t['date'])
    for b in breaks:
        b['start_date'] = str(b['start_date'])
        b['end_date'] = str(b['end_date'])

    return JsonResponse({
        'status': 'success',
        'categories': categories,
        'events': events,
        'todos': todos,
        'settings': settings,
        'breaks': breaks,
    })


@csrf_exempt
def save_event(request):
    """Create or update an event."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    data = json.loads(request.body)
    event_id = data.get('event_id')
    series_id = data.get('series_id') or None
    date = data.get('date')
    cat_id = data.get('catId')
    title = data.get('title', '')
    url = data.get('url', '')
    start_time = data.get('startTime', '')
    end_time = data.get('endTime', '')

    if not event_id or not date or not cat_id or not title:
        return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

    # Ensure category exists
    cat = Category.objects.filter(cat_id=cat_id).first()
    if not cat:
        return JsonResponse({'status': 'error', 'message': f'Category {cat_id} not found'}, status=400)

    obj, created = Event.objects.update_or_create(
        event_id=event_id,
        defaults={
            'series_id': series_id,
            'date': date,
            'category': cat,
            'title': title,
            'url': url,
            'start_time': start_time,
            'end_time': end_time,
        }
    )
    return JsonResponse({'status': 'success', 'created': created})


@csrf_exempt
def delete_event(request, event_id):
    """Delete a single event."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    deleted_count, _ = Event.objects.filter(event_id=event_id).delete()
    return JsonResponse({'status': 'success', 'deleted': deleted_count})


@csrf_exempt
def delete_event_series(request, series_id):
    """Delete all events in a recurrence series."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    deleted_count, _ = Event.objects.filter(series_id=series_id).delete()
    return JsonResponse({'status': 'success', 'deleted': deleted_count})


@csrf_exempt
def save_todo(request):
    """Create or update a to-do item."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    data = json.loads(request.body)
    todo_id = data.get('todo_id')
    date = data.get('date')
    cat_id = data.get('catId')
    title = data.get('title', '')
    url = data.get('url', '')
    completed = data.get('completed', False)
    sort_order = data.get('sort_order', 0)

    if not todo_id or not date or not cat_id or not title:
        return JsonResponse({'status': 'error', 'message': 'Missing required fields'}, status=400)

    cat = Category.objects.filter(cat_id=cat_id).first()
    if not cat:
        return JsonResponse({'status': 'error', 'message': f'Category {cat_id} not found'}, status=400)

    obj, created = Todo.objects.update_or_create(
        todo_id=todo_id,
        defaults={
            'date': date,
            'category': cat,
            'title': title,
            'url': url,
            'completed': completed,
            'sort_order': sort_order,
        }
    )
    return JsonResponse({'status': 'success', 'created': created})


@csrf_exempt
def delete_todo(request, todo_id):
    """Delete a to-do item."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    deleted_count, _ = Todo.objects.filter(todo_id=todo_id).delete()
    return JsonResponse({'status': 'success', 'deleted': deleted_count})


@csrf_exempt
def toggle_todo(request, todo_id):
    """Toggle to-do completion state."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    todo = Todo.objects.filter(todo_id=todo_id).first()
    if not todo:
        return JsonResponse({'status': 'error', 'message': 'Todo not found'}, status=404)

    todo.completed = not todo.completed
    todo.save()
    return JsonResponse({'status': 'success', 'completed': todo.completed})


@csrf_exempt
def reorder_todos(request):
    """Reorder to-do items (update sort_order and optionally date)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    data = json.loads(request.body)
    items = data.get('items', [])

    with transaction.atomic():
        for item in items:
            Todo.objects.filter(todo_id=item['todo_id']).update(
                sort_order=item.get('sort_order', 0),
                date=item.get('date')
            )

    return JsonResponse({'status': 'success'})


@csrf_exempt
def save_categories(request):
    """Bulk save categories (replace all)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    data = json.loads(request.body)
    categories = data.get('categories', [])

    with transaction.atomic():
        # Get existing cat_ids to preserve FK integrity
        existing_ids = set(Category.objects.values_list('cat_id', flat=True))
        new_ids = set(c['id'] for c in categories)

        # Delete categories that are removed (cascade deletes their events/todos)
        removed_ids = existing_ids - new_ids
        if removed_ids:
            Category.objects.filter(cat_id__in=removed_ids).delete()

        for idx, cat in enumerate(categories):
            Category.objects.update_or_create(
                cat_id=cat['id'],
                defaults={
                    'name': cat.get('name', 'Unnamed'),
                    'color': cat.get('color', '#666666'),
                    'bg': cat.get('bg', '#f0f0f0'),
                    'sort_order': idx,
                }
            )

    return JsonResponse({'status': 'success', 'count': len(categories)})


@csrf_exempt
def save_settings(request):
    """Save settings and break periods."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    data = json.loads(request.body)
    settings = data.get('settings', {})
    breaks = data.get('breaks', [])

    with transaction.atomic():
        # Save key-value settings
        for key, value in settings.items():
            SchedulerSetting.objects.update_or_create(
                key=key, defaults={'value': str(value)}
            )

        # Replace all break periods
        BreakPeriod.objects.all().delete()
        for b in breaks:
            BreakPeriod.objects.create(
                break_id=b.get('id', ''),
                name=b.get('name', 'School Break'),
                start_date=b.get('startDate'),
                end_date=b.get('endDate'),
            )

    return JsonResponse({'status': 'success'})


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
def clear_all(request):
    """Delete all events and todos after validating superuser password."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
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

        with transaction.atomic():
            event_count = Event.objects.count()
            todo_count = Todo.objects.count()
            Event.objects.all().delete()
            Todo.objects.all().delete()

        return JsonResponse({
            'status': 'success',
            'deleted_events': event_count,
            'deleted_todos': todo_count,
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)





@csrf_exempt
def import_data(request):
    """Import JSON data (events, todos, categories, settings, breaks)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)
    blocked = require_edit_mode(request)
    if blocked:
        return blocked

    data = json.loads(request.body)

    imported_events = 0
    imported_todos = 0

    with transaction.atomic():
        # Import categories
        categories = data.get('categories', [])
        if categories:
            for idx, cat in enumerate(categories):
                Category.objects.update_or_create(
                    cat_id=cat.get('id', ''),
                    defaults={
                        'name': cat.get('name', 'Unnamed'),
                        'color': cat.get('color', '#666666'),
                        'bg': cat.get('bg', '#f0f0f0'),
                        'sort_order': idx,
                    }
                )

        # Import events
        events_data = data.get('events', [])
        for e in events_data:
            cat_id = e.get('catId') or e.get('category_id', '')
            cat = Category.objects.filter(cat_id=cat_id).first()
            if not cat:
                continue
            Event.objects.update_or_create(
                event_id=e.get('id') or e.get('event_id', ''),
                defaults={
                    'series_id': e.get('seriesId') or e.get('series_id'),
                    'date': e.get('date'),
                    'category': cat,
                    'title': e.get('title', ''),
                    'url': e.get('url', ''),
                    'start_time': e.get('startTime') or e.get('start_time', ''),
                    'end_time': e.get('endTime') or e.get('end_time', ''),
                }
            )
            imported_events += 1

        # Import todos
        todos_data = data.get('todos', [])
        for t in todos_data:
            cat_id = t.get('catId') or t.get('category_id', '')
            cat = Category.objects.filter(cat_id=cat_id).first()
            if not cat:
                continue
            Todo.objects.update_or_create(
                todo_id=t.get('id') or t.get('todo_id', ''),
                defaults={
                    'date': t.get('date'),
                    'category': cat,
                    'title': t.get('title', ''),
                    'url': t.get('url', ''),
                    'completed': t.get('completed', False),
                    'sort_order': t.get('sort_order', 0),
                }
            )
            imported_todos += 1

        # Import settings
        settings = data.get('settings', {})
        if isinstance(settings, dict):
            for key, value in settings.items():
                if key == 'breaks':
                    continue  # Handled separately
                SchedulerSetting.objects.update_or_create(
                    key=key, defaults={'value': str(value)}
                )

            # Import breaks from settings
            breaks = settings.get('breaks', [])
            if breaks:
                BreakPeriod.objects.all().delete()
                for b in breaks:
                    BreakPeriod.objects.create(
                        break_id=b.get('id', ''),
                        name=b.get('name', 'School Break'),
                        start_date=b.get('startDate'),
                        end_date=b.get('endDate'),
                    )

    return JsonResponse({
        'status': 'success',
        'imported_events': imported_events,
        'imported_todos': imported_todos,
    })
