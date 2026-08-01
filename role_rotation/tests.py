import json
from django.test import TestCase, Client
from django.core import mail
from django.core.management import call_command
from django.urls import reverse
from role_rotation.models import WeeklyTask


class WeeklyTaskModelTest(TestCase):
    def test_task_creation_and_str(self):
        task = WeeklyTask.objects.create(
            title="Friday Team Sync",
            description="Prepare slide deck and demo",
            day_of_week=5,
            time="14:00",
            assigned_person="Alex"
        )
        self.assertEqual(str(task), "Ad-Hoc / Special: Friday Team Sync [14:00] (Alex)")
        self.assertEqual(task.day_of_week, 5)
        self.assertEqual(task.time, "14:00")
        self.assertEqual(task.assigned_person, "Alex")


class CadenceViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session['app_mode'] = 'edit'
        session.save()
        self.task1 = WeeklyTask.objects.create(
            title="Daily Standup",
            description="Morning sync",
            day_of_week=1,
            time="09:00",
            assigned_person="Manager"
        )
        self.task2 = WeeklyTask.objects.create(
            title="Ad-Hoc Demo",
            description="Review special release",
            day_of_week=5,
            time="17:00",
            assigned_person="Team Lead"
        )

    def test_dashboard_view(self):
        response = self.client.get(reverse('cadence_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'role_rotation/dashboard.html')

    def test_get_tasks_api(self):
        response = self.client.get(reverse('cadence_get_tasks'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['tasks']), 2)
        self.assertEqual(data['tasks'][0]['time'], '09:00')
        self.assertEqual(data['tasks'][0]['assigned_person'], 'Manager')

    def test_save_task_create_api(self):
        payload = {
            'title': 'Bi-Weekly Retrospective',
            'description': 'Sprint retro',
            'day_of_week': 3,
            'time': '15:00',
            'assigned_person': 'Senior Dev'
        }
        response = self.client.post(
            reverse('cadence_save_task'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(WeeklyTask.objects.count(), 3)
        created = WeeklyTask.objects.get(id=data['task']['id'])
        self.assertEqual(created.title, 'Bi-Weekly Retrospective')
        self.assertEqual(created.time, '15:00')
        self.assertEqual(created.assigned_person, 'Senior Dev')

    def test_save_task_update_api(self):
        payload = {
            'id': self.task1.id,
            'title': 'Daily Standup (Updated)',
            'description': 'Updated description',
            'day_of_week': 1,
            'time': '10:00',
            'assigned_person': 'Product Owner'
        }
        response = self.client.post(
            reverse('cadence_save_task'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.title, 'Daily Standup (Updated)')
        self.assertEqual(self.task1.time, '10:00')
        self.assertEqual(self.task1.assigned_person, 'Product Owner')

    def test_delete_task_api(self):
        response = self.client.post(reverse('cadence_delete_task', args=[self.task1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WeeklyTask.objects.filter(id=self.task1.id).exists())

    def test_trigger_friday_reminder_api(self):
        response = self.client.post(reverse('cadence_trigger_reminder'), data=json.dumps({'recipient': 'test@example.com'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn("Ad-Hoc Demo", mail.outbox[0].body)

    def test_view_mode_blocks_write(self):
        client = Client()  # Default view mode session
        payload = {'title': 'Unauthorized Task', 'day_of_week': 1}
        res = client.post(reverse('cadence_save_task'), data=json.dumps(payload), content_type='application/json')
        self.assertEqual(res.status_code, 403)


    def test_trigger_writer_reminder_api(self):
        from role_rotation.models import EmailRecipient
        EmailRecipient.objects.create(name="Taiki", email="taiki@example.com", is_active=True)
        response = self.client.post(reverse('role_rotation_trigger_writer_reminder'), data=json.dumps({'recipient': 'writer@example.com'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['writer@example.com'])
        self.assertIn("Weekly Brief Report", mail.outbox[0].subject)


class SendFridayReminderCommandTest(TestCase):
    def setUp(self):
        WeeklyTask.objects.create(
            title="Special Task 1",
            day_of_week=5,
            time="16:00",
            assigned_person="Tester"
        )

    def test_command_sends_email_for_friday_tasks(self):
        call_command('send_friday_reminder', day=5, recipient='test@example.com')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['test@example.com'])
        self.assertIn("Special Task 1", mail.outbox[0].body)

    def test_command_no_pending_tasks(self):
        WeeklyTask.objects.filter(day_of_week=5).delete()
        call_command('send_friday_reminder', day=5)
        self.assertEqual(len(mail.outbox), 0)


class SendWriterReminderCommandTest(TestCase):
    def test_command_sends_targeted_email_to_writer(self):
        from role_rotation.models import EmailRecipient
        EmailRecipient.objects.create(name="Taiki", email="taiki@example.com", is_active=True)
        call_command('send_writer_reminder')
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Weekly Brief Report", mail.outbox[0].subject)


class DownloadTemplateViewTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_download_michel_template(self):
        response = self.client.get(reverse('role_rotation_download_template', args=['michel']))
        self.assertEqual(response.status_code, 200)
        self.assertIn('[Michel Template] [MBUA 532] Brief Weekly Report.docx', response['Content-Disposition'])

    def test_download_james_template(self):
        response = self.client.get(reverse('role_rotation_download_template', args=['james']))
        self.assertEqual(response.status_code, 200)
        self.assertIn('[James Template] [BDO MBUA Project] Brief Weekly Report.docx', response['Content-Disposition'])


