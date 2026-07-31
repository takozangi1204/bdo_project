import os
import datetime
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from role_rotation.models import EmailRecipient


class Command(BaseCommand):
    help = "Send a targeted reminder email to the assigned Weekly Brief Report writer for the current week."

    def add_arguments(self, parser):
        parser.add_argument(
            '--recipient',
            type=str,
            default=None,
            help='Override recipient email address.'
        )

    def handle(self, *args, **options):
        override_recipient = options.get('recipient')
        today = datetime.date.today()
        week1_monday = datetime.date(2026, 7, 6)
        days_diff = (today - week1_monday).days
        current_week_num = max(1, min(12, (days_diff // 7) + 1))
        current_week = f"Week {current_week_num}"

        summary_rotation = [
            {'week_num': 1, 'week': 'Week 1', 'writer': 'Ding', 'deadline': 'Sun, 12 Jul, 11:59 PM'},
            {'week_num': 2, 'week': 'Week 2', 'writer': 'Sarala', 'deadline': 'Sun, 19 Jul, 11:59 PM'},
            {'week_num': 3, 'week': 'Week 3', 'writer': 'Suhani', 'deadline': 'Sun, 26 Jul, 11:59 PM'},
            {'week_num': 4, 'week': 'Week 4', 'writer': 'Taiki', 'deadline': 'Sun, 2 Aug, 11:59 PM'},
            {'week_num': 5, 'week': 'Week 5', 'writer': 'Yusuf', 'deadline': 'Sun, 9 Aug, 11:59 PM'},
            {'week_num': 6, 'week': 'Week 6', 'writer': 'Ding', 'deadline': 'Sun, 16 Aug, 11:59 PM'},
            {'week_num': 7, 'week': 'Week 7', 'writer': 'Sarala', 'deadline': 'Sun, 23 Aug, 11:59 PM'},
            {'week_num': 8, 'week': 'Week 8', 'writer': 'Suhani', 'deadline': 'Sun, 30 Aug, 11:59 PM'},
            {'week_num': 9, 'week': 'Week 9', 'writer': 'Taiki', 'deadline': 'Sun, 6 Sep, 11:59 PM'},
            {'week_num': 10, 'week': 'Week 10', 'writer': 'No Need to Submit', 'deadline': 'N/A'},
            {'week_num': 11, 'week': 'Week 11', 'writer': 'No Need to Submit', 'deadline': 'N/A'},
        ]

        curr_summary = next((r for r in summary_rotation if r['week_num'] == current_week_num), summary_rotation[-1])
        writer_name = curr_summary['writer']

        if writer_name == 'No Need to Submit':
            msg = f"No Weekly Brief Report required for {current_week}."
            self.stdout.write(self.style.SUCCESS(msg))
            return msg

        # Lookup writer's email from EmailRecipient model in Django Admin
        recipient_email = override_recipient
        if not recipient_email:
            recipient_obj = EmailRecipient.objects.filter(name__iexact=writer_name, is_active=True).first()
            if recipient_obj:
                recipient_email = recipient_obj.email

        if not recipient_email:
            # Fallback to default reminder recipient or team emails if specific admin record is missing
            default_rem_email = getattr(settings, 'REMINDER_RECIPIENT_EMAIL', '')
            if default_rem_email:
                recipient_email = default_rem_email
            else:
                recipient_email = 'takozangi0619@outlook.jp'

        site_url = os.environ.get('APP_URL') or os.environ.get('SITE_URL') or 'https://bdo-project-app.onrender.com'
        if not site_url.startswith('http'):
            site_url = f"https://{site_url}"
        app_url = f"{site_url.rstrip('/')}/role_rotation/dashboard/"

        subject = f"🔔 Friendly Reminder: Weekly Brief Report Due ({current_week} - {writer_name})"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bdo.local')

        text_message = f"""
Hello {writer_name},

This is a friendly reminder that you are the assigned writer for the [BDO MBUA Project] Weekly Brief Report for {current_week}.

Internal Deadline: {curr_summary['deadline']}

Please prepare the report and gather feedback from the team before submission:
• James (Client): By 5:00 PM, Tuesday
• Michel (Course Lead): By 10:00 AM, Thursday

Dashboard & Templates: {app_url}

Thank you for leading this week's report!

Best regards,
Group Management System
"""

        html_message = f"""
        <html>
          <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2d3436; max-width: 650px; margin: 0 auto; padding: 16px;">
            <div style="border: 1px solid #e2e6ea; border-radius: 12px; padding: 24px; background: #ffffff; box-shadow: 0 4px 16px rgba(0,0,0,0.06);">
              <h2 style="font-size: 18px; font-weight: 700; color: #1a1a2e; margin-top: 0; margin-bottom: 12px; border-bottom: 2px solid #6c5ce7; padding-bottom: 8px;">
                🔔 Friendly Reminder: Weekly Brief Report Due ({current_week})
              </h2>
              
              <p style="font-size: 14px; color: #2d3436;">
                Hi <strong>{writer_name}</strong>,
              </p>
              
              <p style="font-size: 14px; color: #636e72;">
                Just a reminder that you are responsible for leading and writing the <strong>{current_week} Brief Report</strong>.
              </p>

              <div style="background: #fffdf0; border: 1px solid #fde68a; border-left: 4px solid #d97706; padding: 12px 16px; border-radius: 6px; margin: 16px 0;">
                <strong style="color: #92400e; font-size: 13px; display: block; margin-bottom: 4px;">Internal Deadline:</strong>
                <span style="font-size: 14px; font-weight: bold; color: #1a1a2e;">{curr_summary['deadline']}</span>
              </div>

              <div style="background: #f8f9fa; border: 1px solid #e2e6ea; padding: 12px 16px; border-radius: 6px; font-size: 13px; color: #2d3436;">
                <strong>Submission Deadlines:</strong>
                <ul style="margin: 6px 0 0 0; padding-left: 18px; color: #636e72;">
                  <li><strong>James (Client):</strong> Tuesday by 5:00 PM</li>
                  <li><strong>Michel (Course Lead):</strong> Thursday by 10:00 AM</li>
                </ul>
              </div>

              <div style="margin-top: 20px; font-size: 13px; color: #636e72;">
                <strong>Templates &amp; Details:</strong> <a href="{app_url}" target="_blank" style="color: #6c5ce7; font-weight: 600; text-decoration: none;">Group Management Dashboard ↗</a>
              </div>

              <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #e2e6ea; font-size: 12px; color: #b2bec3; text-align: center;">
                BDO MBUA Project • Group Management System
              </div>
            </div>
          </body>
        </html>
        """

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=[recipient_email],
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        success_msg = f"Report writer reminder email sent to {writer_name} <{recipient_email}>."
        self.stdout.write(self.style.SUCCESS(success_msg))
        return success_msg
