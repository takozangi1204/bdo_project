import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings


def get_mode_status(request):
    """Return the current app mode (view or edit) from session."""
    mode = request.session.get('app_mode', 'view')
    return JsonResponse({'status': 'success', 'mode': mode})


@csrf_exempt
def toggle_mode(request):
    """Toggle between view and edit mode. Requires password to switch to edit."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    password = data.get('password', '')
    current_mode = request.session.get('app_mode', 'view')

    if current_mode == 'edit':
        # Switching from edit -> view: no password needed
        request.session['app_mode'] = 'view'
        return JsonResponse({'status': 'success', 'mode': 'view'})
    else:
        # Switching from view -> edit: password required (checks Admin DB settings first, then env/settings, fallback to 112233zZ!!)
        from scheduler.models import SchedulerSetting
        setting = SchedulerSetting.objects.filter(key='edit_password').first()
        if setting and setting.value:
            expected = setting.value
        else:
            expected = getattr(settings, 'APP_EDIT_PASSWORD', '112233zZ!!')

        if password == expected:
            request.session['app_mode'] = 'edit'
            return JsonResponse({'status': 'success', 'mode': 'edit'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Incorrect password.'}, status=403)


def require_edit_mode(request):
    """Helper: returns an error JsonResponse if not in edit mode, or None if OK."""
    mode = request.session.get('app_mode', 'view')
    if mode != 'edit':
        return JsonResponse({
            'status': 'error',
            'message': 'Edit mode required. Please unlock edit mode first.'
        }, status=403)
    return None
