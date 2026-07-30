import os
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings


MEMBER_COLORS = {
    'everyone': {'bg': '#fef3c7', 'text': '#92400e', 'border': '#fde68a'},
    'taiki':    {'bg': '#e0e7ff', 'text': '#3730a3', 'border': '#c7d2fe'},
    'ding':     {'bg': '#dcfce7', 'text': '#166534', 'border': '#bbf7d0'},
    'yusuf':    {'bg': '#ffe4e6', 'text': '#9f1239', 'border': '#fecdd3'},
    'suhani':   {'bg': '#f3e8ff', 'text': '#6b21a8', 'border': '#e9d5ff'},
    'sarala':   {'bg': '#e0f2fe', 'text': '#075985', 'border': '#bae6fd'},
}


def get_person_tag(name):
    if not name or name == 'No Need to Submit':
        return '<span style="color: #636e72; font-style: italic;">No Need to Submit</span>'
    key = name.strip().lower()
    c = MEMBER_COLORS.get(key, {'bg': '#f1f5f9', 'text': '#334155', 'border': '#cbd5e1'})
    return f'<span style="background: {c["bg"]}; color: {c["text"]}; border: 1px solid {c["border"]}; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 12px; display: inline-block; white-space: nowrap;">👤 {name}</span>'


class Command(BaseCommand):
    help = "Send an automatic Monday morning 8:00 AM role rotation summary email to all team members."

    def add_arguments(self, parser):
        parser.add_argument(
            '--recipient',
            type=str,
            default=None,
            help='Recipient email address(es) for the Monday reminder.'
        )

    def handle(self, *args, **options):
        recipient = options['recipient']

        current_week = "Week 4"

        summary_rotation = [
            {'week': 'Week 1', 'writer': 'Ding', 'deadline': 'Sun, 12 Jul, 11:59 PM', 'past': True},
            {'week': 'Week 2', 'writer': 'Sarala', 'deadline': 'Sun, 19 Jul, 11:59 PM', 'past': True},
            {'week': 'Week 3', 'writer': 'Suhani', 'deadline': 'Sun, 26 Jul, 11:59 PM', 'past': True},
            {'week': 'Week 4', 'writer': 'Taiki', 'deadline': 'Sun, 2 Aug, 11:59 PM', 'current': True},
            {'week': 'Week 5', 'writer': 'Yusuf', 'deadline': 'Sun, 9 Aug, 11:59 PM'},
            {'week': 'Week 6', 'writer': 'Ding', 'deadline': 'Sun, 16 Aug, 11:59 PM'},
            {'week': 'Week 7', 'writer': 'Sarala', 'deadline': 'Sun, 23 Aug, 11:59 PM'},
            {'week': 'Week 8', 'writer': 'Suhani', 'deadline': 'Sun, 30 Aug, 11:59 PM'},
            {'week': 'Week 9', 'writer': 'Taiki', 'deadline': 'Sun, 6 Sep, 11:59 PM'},
            {'week': 'Week 10', 'writer': 'No Need to Submit', 'deadline': 'N/A'},
            {'week': 'Week 11', 'writer': 'No Need to Submit', 'deadline': 'N/A'},
        ]

        meeting_rotation = [
            {'dateTime': '<strong>Week 2</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(16 Jul, 2:00 PM)</span>', 'chair': 'Suhani', 'asking': 'Taiki', 'notes': 'Yusuf', 'agenda': 'Ding', 'resting': 'Sarala', 'past': True},
            {'dateTime': '<strong>Week 4</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(30 Jul, 2:00 PM)</span>', 'chair': 'Taiki', 'asking': 'Yusuf', 'notes': 'Ding', 'agenda': 'Sarala', 'resting': 'Suhani', 'current': True},
            {'dateTime': '<strong>Week 6</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(11 Aug, 11:00 AM)</span>', 'chair': 'Yusuf', 'asking': 'Ding', 'notes': 'Sarala', 'agenda': 'Suhani', 'resting': 'Taiki'},
            {'dateTime': '<strong>Week 8</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(27 Aug, 2:00 PM)</span>', 'chair': 'Ding', 'asking': 'Sarala', 'notes': 'Suhani', 'agenda': 'Taiki', 'resting': 'Yusuf'},
            {'dateTime': '<strong>Week 11</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(17 Sep, 2:00 PM)</span>', 'chair': 'Sarala', 'asking': 'Suhani', 'notes': 'Taiki', 'agenda': 'Yusuf', 'resting': 'Ding'},
            {'dateTime': '<strong>Week 12</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(24 Sep, 2:00 PM)</span>', 'chair': 'Suhani', 'asking': 'Taiki', 'notes': 'Yusuf', 'agenda': 'Ding', 'resting': 'Sarala'},
        ]

        # Build Section 1 HTML Table (ONLY HIGHLIGHTED CURRENT WEEK ROW)
        active_summary = [r for r in summary_rotation if r.get('current')]
        summary_rows_html = ""
        for r in active_summary:
            bg_style = 'background: #fffdf0; border-left: 4px solid #d97706;'
            badge = get_person_tag(r['writer'])
            summary_rows_html += f"""
            <tr style="{bg_style}">
                <td style="padding: 10px 14px; border-bottom: 1px solid #e2e6ea; font-weight: bold;">{r['week']}</td>
                <td style="padding: 10px 14px; border-bottom: 1px solid #e2e6ea;">{badge}</td>
                <td style="padding: 10px 14px; border-bottom: 1px solid #e2e6ea; color: #636e72;">{r['deadline']}</td>
            </tr>
            """

        # Build Section 2 HTML Table (ONLY HIGHLIGHTED CURRENT WEEK ROW)
        active_meeting = [r for r in meeting_rotation if r.get('current')]
        meeting_rows_html = ""
        for r in active_meeting:
            bg_style = 'background: #fffdf0; border-left: 4px solid #d97706;'
            meeting_rows_html += f"""
            <tr style="{bg_style}">
                <td style="padding: 10px 12px; border-bottom: 1px solid #e2e6ea; font-size: 13px; font-weight: bold;">{r['dateTime']}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #e2e6ea;">{get_person_tag(r['chair'])}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #e2e6ea;">{get_person_tag(r['asking'])}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #e2e6ea;">{get_person_tag(r['notes'])}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #e2e6ea;">{get_person_tag(r['agenda'])}</td>
                <td style="padding: 10px 12px; border-bottom: 1px solid #e2e6ea;">{get_person_tag(r['resting'])}</td>
            </tr>
            """

        subject = f"[BDO MBUA Project] {current_week} Reminder"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bdo.local')

        app_url = "http://127.0.0.1:8000/role_rotation/dashboard/"

        from role_rotation.utils import get_weekly_schedule_html, get_weekly_schedule_text
        section3_html = get_weekly_schedule_html()
        section3_text = get_weekly_schedule_text()

        text_message = (
            f"Hello Team,\n\n"
            f"Here is your [BDO MBUA Project] {current_week} Reminder:\n\n"
            f"1. Brief Weekly Report Table:\n"
            f"Active Writer for {current_week}: Taiki (Internal Deadline: Sun, 2 Aug, 11:59 PM)\n\n"
            f"2. Next Meeting with BDO:\n"
            f"Upcoming Meeting: Week 4 (30 Jul, 2:00 PM)\n"
            f"Chairperson: Taiki | Asking: Yusuf | Notes: Ding | Agenda: Sarala | Resting: Suhani\n\n"
            f"{section3_text}\n"
            f"Check the details: {app_url}\n\n"
            f"Best regards,\nRole Rotation Team"
        )

        html_message = f"""
        <html>
          <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2d3436; max-width: 750px; margin: 0 auto; padding: 0; background-color: #ffffff;">
            <div style="padding: 16px 20px;">
              <h2 style="font-size: 18px; font-weight: 700; color: #1a1a2e; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #6c5ce7; padding-bottom: 8px;">[BDO MBUA Project] {current_week} Reminder</h2>

              <!-- SECTION 1 -->
              <h3 style="font-size: 15px; color: #1a1a2e; margin-top: 16px; margin-bottom: 8px;">1. Brief Weekly Report</h3>
              <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px;">
                <thead>
                  <tr style="background: #f8f9fa; color: #636e72; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em;">
                    <th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e6ea;">Week Cycle</th>
                    <th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e6ea;">Assigned Writer</th>
                    <th style="padding: 8px 12px; text-align: left; border-bottom: 2px solid #e2e6ea;">Internal Deadline</th>
                  </tr>
                </thead>
                <tbody>
                  {summary_rows_html}
                </tbody>
              </table>

              <!-- SECTION 2 -->
              <h3 style="font-size: 15px; color: #1a1a2e; margin-top: 16px; margin-bottom: 8px;">2. Next Meeting with BDO</h3>
              <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 12px;">
                <thead>
                  <tr style="background: #f8f9fa; color: #636e72; text-transform: uppercase; font-size: 11px; letter-spacing: 0.05em;">
                    <th style="padding: 8px 10px; text-align: left; border-bottom: 2px solid #e2e6ea;">Meeting Date & Time</th>
                    <th style="padding: 8px 10px; text-align: left; border-bottom: 2px solid #e2e6ea;">Chairperson</th>
                    <th style="padding: 8px 10px; text-align: left; border-bottom: 2px solid #e2e6ea;">Asking Questions</th>
                    <th style="padding: 8px 10px; text-align: left; border-bottom: 2px solid #e2e6ea;">Taking Notes</th>
                    <th style="padding: 8px 10px; text-align: left; border-bottom: 2px solid #e2e6ea;">Preparing Agenda</th>
                    <th style="padding: 8px 10px; text-align: left; border-bottom: 2px solid #e2e6ea;">Resting</th>
                  </tr>
                </thead>
                <tbody>
                  {meeting_rows_html}
                </tbody>
              </table>

              <!-- SECTION 3: THIS WEEK'S SCHEDULE -->
              {section3_html}

              <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #e2e6ea; font-size: 12px; color: #636e72;">
                Check the details: <a href="{app_url}" target="_blank" style="color: #6c5ce7; font-weight: 600; text-decoration: none;">{app_url} ↗</a>
              </div>
            </div>
          </body>
        </html>
        """

        from role_rotation.models import EmailRecipient

        if recipient:
            recipient_list = [e.strip() for e in recipient.split(',') if e.strip()]
        else:
            db_emails = list(EmailRecipient.objects.filter(is_active=True).values_list('email', flat=True))
            if db_emails:
                recipient_list = db_emails
            else:
                default_rem_email = getattr(settings, 'REMINDER_RECIPIENT_EMAIL', '')
                team_list = getattr(settings, 'TEAM_EMAIL_RECIPIENTS', [default_rem_email] if default_rem_email else [])
                recipient_list = team_list

        to_emails = recipient_list if len(recipient_list) == 1 else []
        bcc_emails = [] if len(recipient_list) == 1 else recipient_list

        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=from_email,
            to=to_emails,
            bcc=bcc_emails,
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)

        success_msg = f"Monday morning schedule email for {current_week} sent successfully via BCC."
        self.stdout.write(self.style.SUCCESS(success_msg))
        return success_msg
