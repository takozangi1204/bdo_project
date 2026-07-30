import datetime
from scheduler.models import Event, Todo, Category


def format_time_display(time_str):
    """Formats '09:00' to '9:00 AM' or '17:00' to '5:00 PM'."""
    if not time_str:
        return ''
    try:
        parts = time_str.split(':')
        hh = int(parts[0])
        mm = int(parts[1])
        h12 = 12 if hh == 0 or hh == 12 else (hh - 12 if hh > 12 else hh)
        ampm = 'AM' if hh < 12 else 'PM'
        return f"{h12}:{mm:02d} {ampm}"
    except (ValueError, IndexError):
        return time_str


def get_weekly_schedule_html(target_date=None):
    """Generates Section 3 HTML containing boxes for Monday to Sunday with scheduled events/todos in category colors."""
    if not target_date:
        target_date = datetime.date.today()

    monday = target_date - datetime.timedelta(days=target_date.weekday())
    sunday = monday + datetime.timedelta(days=6)

    # Pre-query all categories into dict
    categories = {c.cat_id: c for c in Category.objects.all()}

    # Fetch events & todos for the week
    events = list(Event.objects.filter(date__gte=monday, date__lte=sunday).select_related('category'))
    todos = list(Todo.objects.filter(date__gte=monday, date__lte=sunday).select_related('category'))

    day_boxes = []

    for i in range(7):
        day_date = monday + datetime.timedelta(days=i)
        day_name = day_date.strftime('%A')
        date_label = day_date.strftime('%d %b %Y')

        day_events = [e for e in events if e.date == day_date]
        day_todos = [t for t in todos if t.date == day_date]

        items_html = []

        for e in day_events:
            cat = e.category
            cat_name = cat.name if cat else 'General'
            cat_color = cat.color if cat and cat.color else '#6c5ce7'
            cat_bg = cat.bg if cat and cat.bg else '#f0f3ff'

            time_text = ""
            if e.start_time:
                s_fmt = format_time_display(e.start_time)
                e_fmt = format_time_display(e.end_time) if e.end_time else ""
                time_text = f"{s_fmt} – {e_fmt}" if e_fmt else s_fmt

            time_badge = f'<div style="font-size: 11px; color: #64748b; margin-top: 2px;">{time_text}</div>' if time_text else ''

            items_html.append(f"""
            <div style="background-color: {cat_bg}; border: 1px solid {cat_color}; border-left: 4px solid {cat_color}; padding: 7px 12px; border-radius: 6px; font-size: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="color: #1e293b;">{e.title}</strong>
                    <span style="font-size: 10px; background: {cat_color}; color: #ffffff; padding: 1px 6px; border-radius: 10px; font-weight: bold;">{cat_name}</span>
                </div>
                {time_badge}
            </div>
            """)

        for t in day_todos:
            cat = t.category
            cat_name = cat.name if cat else 'General'
            cat_color = cat.color if cat and cat.color else '#6c5ce7'
            cat_bg = cat.bg if cat and cat.bg else '#f0f3ff'

            check_mark = "✓" if t.completed else "○"
            check_style = "color: #16a34a; font-weight: bold;" if t.completed else "color: #64748b;"

            items_html.append(f"""
            <div style="background-color: {cat_bg}; border: 1px solid {cat_color}; border-left: 4px solid {cat_color}; padding: 7px 12px; border-radius: 6px; font-size: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="{check_style} font-size: 13px; margin-right: 4px;">{check_mark}</span>
                        <strong style="color: #1e293b;">{t.title}</strong>
                    </div>
                    <span style="font-size: 10px; background: {cat_color}; color: #ffffff; padding: 1px 6px; border-radius: 10px; font-weight: bold;">{cat_name}</span>
                </div>
            </div>
            """)

        if not items_html:
            content_block = '<div style="font-size: 12px; color: #94a3b8; font-style: italic; padding: 4px 0;">No scheduled events or tasks</div>'
        else:
            content_block = f'<div style="display: flex; flex-direction: column; gap: 6px;">{"".join(items_html)}</div>'

        header_bg = "background: #f8fafc; color: #1e293b;"

        day_boxes.append(f"""
        <div style="background: #ffffff; border: 1px solid #e2e6ea; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
            <div style="{header_bg} padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 13px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                <span>{day_name}</span>
                <span style="font-size: 11px; opacity: 0.8; font-weight: normal;">{date_label}</span>
            </div>
            {content_block}
        </div>
        """)

    schedule_html = f"""
    <div style="margin-top: 16px;">
        <h3 style="font-size: 15px; color: #1a1a2e; margin-top: 16px; margin-bottom: 8px;">3. This Week's Schedule (As of Monday)</h3>
        {"".join(day_boxes)}
    </div>
    """

    return schedule_html


def get_weekly_schedule_text(target_date=None):
    """Generates Section 3 Plain Text summary for Monday to Sunday."""
    if not target_date:
        target_date = datetime.date.today()

    monday = target_date - datetime.timedelta(days=target_date.weekday())
    sunday = monday + datetime.timedelta(days=6)

    events = list(Event.objects.filter(date__gte=monday, date__lte=sunday).select_related('category'))
    todos = list(Todo.objects.filter(date__gte=monday, date__lte=sunday).select_related('category'))

    lines = ["3. THIS WEEK'S SCHEDULE (As of Monday):"]

    for i in range(7):
        day_date = monday + datetime.timedelta(days=i)
        day_name = day_date.strftime('%A, %d %b %Y')

        day_events = [e for e in events if e.date == day_date]
        day_todos = [t for t in todos if t.date == day_date]

        lines.append(f"[{day_name}]")
        if not day_events and not day_todos:
            lines.append("  - No scheduled items")
        else:
            for e in day_events:
                t_str = f" ({format_time_display(e.start_time)})" if e.start_time else ""
                lines.append(f"  - [Event{t_str}] {e.title} [{e.category.name if e.category else 'General'}]")
            for t in day_todos:
                st = "✓" if t.completed else "○"
                lines.append(f"  - [To-Do {st}] {t.title} [{t.category.name if t.category else 'General'}]")
        lines.append("")

    return "\n".join(lines)
