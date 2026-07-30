import os
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.conf import settings
from role_rotation.models import WeeklyTask
from playwright.sync_api import sync_playwright


MEMBER_COLORS = {
    'everyone': {'bg': '#fef3c7', 'text': '#92400e', 'border': '#fde68a', 'leftBorder': '#d97706', 'cardBg': '#fffdf5'},
    'taiki':    {'bg': '#e0e7ff', 'text': '#3730a3', 'border': '#c7d2fe', 'leftBorder': '#4f46e5', 'cardBg': '#f8fafc'},
    'ding':     {'bg': '#dcfce7', 'text': '#166534', 'border': '#bbf7d0', 'leftBorder': '#16a34a', 'cardBg': '#f6fbf7'},
    'yusuf':    {'bg': '#ffe4e6', 'text': '#9f1239', 'border': '#fecdd3', 'leftBorder': '#e11d48', 'cardBg': '#fff5f7'},
    'suhani':   {'bg': '#f3e8ff', 'text': '#6b21a8', 'border': '#e9d5ff', 'leftBorder': '#9333ea', 'cardBg': '#faf5ff'},
    'sarala':   {'bg': '#e0f2fe', 'text': '#075985', 'border': '#bae6fd', 'leftBorder': '#0284c7', 'cardBg': '#f0f9ff'},
}


def get_member_color(name):
    if not name:
        return {'bg': '#e0e7ff', 'text': '#3730a3', 'border': '#c7d2fe', 'leftBorder': '#6c5ce7', 'cardBg': '#ffffff'}
    key = name.strip().lower()
    return MEMBER_COLORS.get(key, {'bg': '#e0e7ff', 'text': '#3730a3', 'border': '#c7d2fe', 'leftBorder': '#6c5ce7', 'cardBg': '#ffffff'})


class Command(BaseCommand):
    help = "Send a reminder email listing uncompleted weekly tasks with a dashboard screenshot."

    def add_arguments(self, parser):
        parser.add_argument(
            '--day',
            type=int,
            default=5,
            help='Day of week (1=Monday, 5=Friday, 7=Sunday). Default is 5 (Friday).'
        )
        default_recipient = getattr(settings, 'REMINDER_RECIPIENT_EMAIL', '')
        parser.add_argument(
            '--recipient',
            type=str,
            default=default_recipient,
            help='Recipient email address for the reminder.'
        )

    def handle(self, *args, **options):
        recipient_arg = options.get('recipient')
        from role_rotation.models import EmailRecipient

        if recipient_arg:
            recipient_list = [e.strip() for e in recipient_arg.split(',') if e.strip()]
        else:
            db_emails = list(EmailRecipient.objects.filter(is_active=True).values_list('email', flat=True))
            if db_emails:
                recipient_list = db_emails
            else:
                default_rem_email = getattr(settings, 'REMINDER_RECIPIENT_EMAIL', '')
                if default_rem_email:
                    recipient_list = [default_rem_email]
                else:
                    recipient_list = ['takozangi0619@outlook.jp', 'takozangi0619@icloud.com']

        pending_tasks = WeeklyTask.objects.all().order_by('time', 'id')
        count = pending_tasks.count()

        if count == 0:
            msg = "No scheduled cadence tasks."
            self.stdout.write(self.style.SUCCESS(msg))
            return msg

        # --- 1. Format task list text (Scheduler Card Style) ---
        task_lines_html = []
        task_lines_text = []
        for idx, task in enumerate(pending_tasks, start=1):
            c = get_member_color(task.assigned_person) if task.assigned_person else {'bg': '#e0e7ff', 'text': '#3730a3', 'border': '#c7d2fe', 'leftBorder': '#6c5ce7', 'cardBg': '#ffffff'}
            time_part = f'<div style="font-size: 11px; font-weight: bold; color: {c["leftBorder"]}; text-transform: uppercase;">{task.time}</div>' if task.time else ''
            title_part = f'<div style="font-size: 14px; font-weight: bold; color: #1a1a2e; margin: 2px 0;">{task.title}</div>'
            assigned_part = f'<div style="font-size: 11px; color: {c["text"]}; font-weight: 700; background: {c["bg"]}; border: 1px solid {c["border"]}; display: inline-block; padding: 2px 8px; border-radius: 12px; margin-top: 4px;">👤 {task.assigned_person}</div>' if task.assigned_person else ''
            desc_part = f'<div style="font-size: 12px; color: #636e72; margin-top: 2px;">{task.description}</div>' if task.description else ''

            card_html = f'''
            <div style="background: {c["cardBg"]}; border: 1px solid {c["border"]}; border-left: 4px solid {c["leftBorder"]}; padding: 10px 14px; margin-bottom: 12px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                {time_part}
                {title_part}
                {assigned_part}
                {desc_part}
            </div>
            '''
            task_lines_html.append(card_html)

            text_block = []
            if task.time:
                text_block.append(f"{task.time}")
            text_block.append(f"{task.title}")
            task_lines_text.append(f"{idx}. [{task.get_day_of_week_display()}] {task.title} - Time: {task.time or 'N/A'} (Assigned: {task.assigned_person or 'Unassigned'})")
            
            task_lines_html.append(f"""
            <div style="background-color: {c['cardBg']}; border: 1px solid {c['border']}; border-left: 5px solid {c['leftBorder']}; border-radius: 6px; padding: 12px 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <strong style="font-size: 15px; color: #1e293b;">#{idx} {task.title}</strong>
                    <span style="background-color: {c['bg']}; color: {c['text']}; font-size: 11px; font-weight: bold; padding: 2px 8px; border-radius: 12px; text-transform: uppercase;">{task.assigned_person or 'Unassigned'}</span>
                </div>
                <div style="font-size: 13px; color: #64748b; margin-top: 4px;">
                    <strong>Group:</strong> {task.get_day_of_week_display()} &nbsp;|&nbsp; <strong>Time:</strong> {task.time or 'Flexible'}
                </div>
            </div>
            """)

        task_list_text = "\n".join(task_lines_text)
        task_list_html = "\n".join(task_lines_html)

        # --- 2. Take Screenshot using Playwright ---
        screenshot_path = os.path.join(settings.BASE_DIR, 'role_rotation_dashboard_temp.png')
        self.stdout.write("Capturing dashboard screenshot...")
        
        site_url = os.environ.get('APP_URL') or os.environ.get('SITE_URL') or 'https://bdo-project-app.onrender.com'
        if not site_url.startswith('http'):
            site_url = f"https://{site_url}"
        dashboard_url = f"{site_url.rstrip('/')}/role_rotation/dashboard/"

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(viewport={'width': 1280, 'height': 800})
                page.goto(dashboard_url, wait_until='load', timeout=10000)
                page.screenshot(path=screenshot_path, full_page=True)
                browser.close()
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Warning: Failed to capture screenshot ({e}). Sending email without image."))

        # --- 3. メールの件名と本文作成 ---
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bdo.local')
        subject = f"🔔 Friday Cadence Task Reminder ({count} tasks remaining)"

        from role_rotation.utils import get_weekly_schedule_html, get_weekly_schedule_text
        section3_html = get_weekly_schedule_html()
        section3_text = get_weekly_schedule_text()

        text_message = f"""
Hello,

This is a reminder of current weekly cadence tasks ({count} total):

{task_list_text}

{section3_text}

Please check the cadence dashboard for details: {dashboard_url}

Best regards,
Weekly Cadence App
        """

        html_message = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
            <h2 style="color: #4f46e5;">🔔 Friday Cadence Task Reminder</h2>
            <p>Hello team,</p>
            <p>Here is the current list of scheduled weekly cadence tasks (<strong>{count} total</strong>):</p>
            
            <div style="margin: 20px 0;">
              {task_list_html}
            </div>

            <!-- SECTION 3: THIS WEEK'S SCHEDULE -->
            {section3_html}

            <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
            <h3>Dashboard View</h3>
            <div style="border: 1px solid #ccc; padding: 10px; background-color: #f9f9f9; display: inline-block;">
              <img src="cid:dashboard_img" alt="Dashboard Screenshot" style="max-width: 100%; height: auto;" />
            </div>
            <br><br>
            <div style="margin-top: 16px; font-size: 13px; color: #636e72;">
              Check the details: <a href="{dashboard_url}" target="_blank" style="color: #4f46e5; font-weight: 600; text-decoration: none;">{dashboard_url} ↗</a>
            </div>
            <br><br>
            <p>Best regards,<br><strong>Weekly Cadence App</strong></p>
          </body>
        </html>
        """

        # --- 4. メールの作成と画像の添付 ---
        to_emails = recipient_list
        bcc_emails = []

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=to_emails,
            bcc=bcc_emails,
        )
        email.attach_alternative(html_message, "text/html")

        # スクリーンショットが存在すれば CID として埋め込み
        if os.path.exists(screenshot_path):
            with open(screenshot_path, 'rb') as f:
                img = MIMEImage(f.read())
                img.add_header('Content-ID', '<dashboard_img>')
                email.attach(img)

        # --- 5. 送信と後始末 ---
        email.send(fail_silently=False)

        if os.path.exists(screenshot_path):
            os.remove(screenshot_path)

        recipient_display = ", ".join(recipient_list)
        success_msg = f"Successfully sent cadence reminder with {count} task(s) and screenshot to {recipient_display}."
        self.stdout.write(self.style.SUCCESS(success_msg))
        return success_msg