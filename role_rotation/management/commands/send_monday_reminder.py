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

        import datetime
        today = datetime.date.today()
        week1_monday = datetime.date(2026, 7, 6)
        days_diff = (today - week1_monday).days
        current_week_num = max(1, min(12, (days_diff // 7) + 1))
        current_week = f"Week {current_week_num}"

        summary_rotation = [
            {'week_num': 1, 'week': 'Week 1', 'writer': 'Ding', 'deadline_date': datetime.date(2026, 7, 12), 'deadline': 'Sun, 12 Jul, 11:59 PM'},
            {'week_num': 2, 'week': 'Week 2', 'writer': 'Sarala', 'deadline_date': datetime.date(2026, 7, 19), 'deadline': 'Sun, 19 Jul, 11:59 PM'},
            {'week_num': 3, 'week': 'Week 3', 'writer': 'Suhani', 'deadline_date': datetime.date(2026, 7, 26), 'deadline': 'Sun, 26 Jul, 11:59 PM'},
            {'week_num': 4, 'week': 'Week 4', 'writer': 'Taiki', 'deadline_date': datetime.date(2026, 8, 2), 'deadline': 'Sun, 2 Aug, 11:59 PM'},
            {'week_num': 5, 'week': 'Week 5', 'writer': 'Yusuf', 'deadline_date': datetime.date(2026, 8, 9), 'deadline': 'Sun, 9 Aug, 11:59 PM'},
            {'week_num': 6, 'week': 'Week 6', 'writer': 'Ding', 'deadline_date': datetime.date(2026, 8, 16), 'deadline': 'Sun, 16 Aug, 11:59 PM'},
            {'week_num': 7, 'week': 'Week 7', 'writer': 'Sarala', 'deadline_date': datetime.date(2026, 8, 23), 'deadline': 'Sun, 23 Aug, 11:59 PM'},
            {'week_num': 8, 'week': 'Week 8', 'writer': 'Suhani', 'deadline_date': datetime.date(2026, 8, 30), 'deadline': 'Sun, 30 Aug, 11:59 PM'},
            {'week_num': 9, 'week': 'Week 9', 'writer': 'Taiki', 'deadline_date': datetime.date(2026, 9, 6), 'deadline': 'Sun, 6 Sep, 11:59 PM'},
            {'week_num': 10, 'week': 'Week 10', 'writer': 'No Need to Submit', 'deadline_date': None, 'deadline': 'N/A'},
            {'week_num': 11, 'week': 'Week 11', 'writer': 'No Need to Submit', 'deadline_date': None, 'deadline': 'N/A'},
        ]

        meeting_rotation = [
            {'week_num': 2, 'meeting_date': datetime.date(2026, 7, 16), 'date_label': '16 Jul, 2:00 PM', 'dateTime': '<strong>Week 2</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(16 Jul, 2:00 PM)</span>', 'chair': 'Suhani', 'asking': 'Taiki', 'notes': 'Yusuf', 'agenda': 'Ding', 'resting': 'Sarala'},
            {'week_num': 4, 'meeting_date': datetime.date(2026, 7, 30), 'date_label': '30 Jul, 2:00 PM', 'dateTime': '<strong>Week 4</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(30 Jul, 2:00 PM)</span>', 'chair': 'Taiki', 'asking': 'Yusuf', 'notes': 'Ding', 'agenda': 'Sarala', 'resting': 'Suhani'},
            {'week_num': 6, 'meeting_date': datetime.date(2026, 8, 11), 'date_label': '11 Aug, 11:00 AM', 'dateTime': '<strong>Week 6</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(11 Aug, 11:00 AM)</span>', 'chair': 'Yusuf', 'asking': 'Ding', 'notes': 'Sarala', 'agenda': 'Suhani', 'resting': 'Taiki'},
            {'week_num': 8, 'meeting_date': datetime.date(2026, 8, 27), 'date_label': '27 Aug, 2:00 PM', 'dateTime': '<strong>Week 8</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(27 Aug, 2:00 PM)</span>', 'chair': 'Ding', 'asking': 'Sarala', 'notes': 'Suhani', 'agenda': 'Taiki', 'resting': 'Yusuf'},
            {'week_num': 11, 'meeting_date': datetime.date(2026, 9, 17), 'date_label': '17 Sep, 2:00 PM', 'dateTime': '<strong>Week 11</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(17 Sep, 2:00 PM)</span>', 'chair': 'Sarala', 'asking': 'Suhani', 'notes': 'Taiki', 'agenda': 'Yusuf', 'resting': 'Ding'},
            {'week_num': 12, 'meeting_date': datetime.date(2026, 9, 24), 'date_label': '24 Sep, 2:00 PM', 'dateTime': '<strong>Week 12</strong><br><span style="font-size: 11px; color: #636e72; font-weight: normal;">(24 Sep, 2:00 PM)</span>', 'chair': 'Suhani', 'asking': 'Taiki', 'notes': 'Yusuf', 'agenda': 'Ding', 'resting': 'Sarala'},
        ]

        for r in summary_rotation:
            if r['week_num'] < current_week_num:
                r['past'] = True
            elif r['week_num'] == current_week_num:
                r['current'] = True

        found_upcoming = False
        for m in meeting_rotation:
            if m['meeting_date'] < today:
                m['past'] = True
            elif not found_upcoming:
                m['current'] = True
                found_upcoming = True

        curr_summary = next((r for r in summary_rotation if r.get('current')), summary_rotation[-1])
        curr_meeting = next((m for m in meeting_rotation if m.get('current')), meeting_rotation[-1])

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

        subject = f"[BDO MBUA Project] {current_week} Update"
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@bdo.local')

        site_url = os.environ.get('APP_URL') or os.environ.get('SITE_URL') or 'https://bdo-project-app.onrender.com'
        if not site_url.startswith('http'):
            site_url = f"https://{site_url}"
        app_url = f"{site_url.rstrip('/')}/role_rotation/dashboard/"

        from role_rotation.utils import get_weekly_schedule_html, get_weekly_schedule_text
        section3_html = get_weekly_schedule_html()
        section3_text = get_weekly_schedule_text()

        text_message = (
            f"Hello Team,\n\n"
            f"Here is your [BDO MBUA Project] {current_week} Update:\n\n"
            f"1. Brief Weekly Report Table:\n"
            f"Active Writer for {current_week}: {curr_summary['writer']} (Internal Deadline: {curr_summary['deadline']})\n\n"
            f"2. Next Meeting with BDO:\n"
            f"Upcoming Meeting: Week {curr_meeting['week_num']} ({curr_meeting['date_label']})\n"
            f"Chairperson: {curr_meeting['chair']} | Asking: {curr_meeting['asking']} | Notes: {curr_meeting['notes']} | Agenda: {curr_meeting['agenda']} | Resting: {curr_meeting['resting']}\n\n"
            f"{section3_text}\n"
            f"Check the details: {app_url}\n\n"
            f"Best regards,\nRole Rotation Team"
        )

        html_message = f"""
        <html>
          <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #2d3436; max-width: 750px; margin: 0 auto; padding: 0; background-color: #ffffff;">
            <div style="padding: 16px 20px;">
              <h2 style="font-size: 18px; font-weight: 700; color: #1a1a2e; margin-top: 0; margin-bottom: 16px; border-bottom: 2px solid #6c5ce7; padding-bottom: 8px;">[BDO MBUA Project] {current_week} Update</h2>

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

              <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #e2e6ea; font-size: 13px; color: #636e72;">
                Check the details: <a href="{app_url}" target="_blank" style="color: #6c5ce7; font-weight: 600; text-decoration: none;">Role Rotation Dashboard ↗</a>
              </div>

              <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid #e2e6ea; font-size: 12px; color: #b2bec3; text-align: center;">
                BDO MBUA Project • Role Rotation System
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
                team_list = getattr(settings, 'TEAM_EMAIL_RECIPIENTS', [])
                if team_list:
                    recipient_list = team_list
                elif default_rem_email:
                    recipient_list = [default_rem_email]
                else:
                    recipient_list = ['takozangi0619@outlook.jp', 'takozangi0619@icloud.com']

        to_emails = []
        bcc_emails = recipient_list

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
