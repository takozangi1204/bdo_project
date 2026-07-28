import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Phase, Task

class RoadmapAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.phase_setup = Phase.objects.create(
            phase_id='setup',
            name='Setup',
            colour='#6B8DE3',
            bg='#E0E8FF',
            order=1
        )
        self.task1 = Task.objects.create(
            title='Project Kickoff',
            phase=self.phase_setup,
            start_date='2026-07-06',
            end_date='2026-07-12',
            status='inprogress',
            deliverables='Charter document'
        )

    def test_get_roadmap_data(self):
        response = self.client.get(reverse('get_data'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('phases', data)
        self.assertIn('tasks', data)
        
        # Check phase attributes including color and colour
        self.assertEqual(len(data['phases']), 1)
        phase = data['phases'][0]
        self.assertEqual(phase['id'], 'setup')
        self.assertEqual(phase['colour'], '#6B8DE3')
        self.assertEqual(phase['color'], '#6B8DE3')
        self.assertEqual(phase['bg'], '#E0E8FF')
        
        # Check task attributes
        self.assertEqual(len(data['tasks']), 1)
        task = data['tasks'][0]
        self.assertEqual(task['name'], 'Project Kickoff')
        self.assertEqual(task['phaseId'], 'setup')
        self.assertEqual(task['startDate'], '2026-07-06')
        self.assertEqual(task['endDate'], '2026-07-12')
        self.assertEqual(task['status'], 'inprogress')
        self.assertEqual(task['deliverables'], 'Charter document')

    def test_save_new_task_camel_case(self):
        payload = {
            'name': 'Literature Review',
            'phaseId': 'setup',
            'startDate': '2026-07-13',
            'endDate': '2026-07-19',
            'status': 'todo',
            'deliverables': 'Summary notes'
        }
        response = self.client.post(
            reverse('save_task'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'success')
        self.assertIn('id', res_data)
        
        new_task = Task.objects.get(id=res_data['id'])
        self.assertEqual(new_task.title, 'Literature Review')
        self.assertEqual(str(new_task.start_date), '2026-07-13')

    def test_update_existing_task(self):
        payload = {
            'id': str(self.task1.id),
            'name': 'Updated Kickoff Title',
            'phaseId': 'setup',
            'startDate': '2026-07-06',
            'endDate': '2026-07-15',
            'status': 'done',
            'deliverables': 'Updated Charter'
        }
        response = self.client.post(
            reverse('save_task'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.title, 'Updated Kickoff Title')
        self.assertEqual(self.task1.status, 'done')

    def test_delete_task(self):
        delete_url = reverse('delete_task', kwargs={'task_id': str(self.task1.id)})
        response = self.client.post(delete_url, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Task.objects.filter(id=self.task1.id).count(), 0)

    def test_save_task_invalid_method(self):
        response = self.client.get(reverse('save_task'))
        self.assertEqual(response.status_code, 405)

    def test_delete_task_invalid_method(self):
        delete_url = reverse('delete_task', kwargs={'task_id': str(self.task1.id)})
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 405)

    def test_import_tasks(self):
        import_payload = {
            'clear_existing': True,
            'tasks': [
                {
                    'name': 'Imported Task 1',
                    'phaseId': 'setup',
                    'startDate': '2026-07-20',
                    'endDate': '2026-07-27',
                    'status': 'todo',
                    'deliverables': 'Imported deliverable'
                },
                {
                    'name': 'Imported Task 2',
                    'phaseId': 'setup',
                    'startDate': '2026-07-28',
                    'endDate': '2026-08-04',
                    'status': 'inprogress',
                    'deliverables': ''
                }
            ]
        }
        response = self.client.post(
            reverse('import_tasks'),
            data=json.dumps(import_payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertEqual(res_data['status'], 'success')
        self.assertEqual(res_data['imported_count'], 2)
        
        # Verify old task was cleared and 2 new tasks exist
        self.assertEqual(Task.objects.count(), 2)
        self.assertTrue(Task.objects.filter(title='Imported Task 1').exists())

    def test_clear_all_tasks_requires_superuser_password(self):
        from django.contrib.auth.models import User
        User.objects.create_superuser('admin', 'admin@example.com', 'supersecret')

        # Invalid password attempt
        res_fail = self.client.post(
            reverse('clear_all_tasks'),
            data=json.dumps({'password': 'wrongpassword'}),
            content_type='application/json'
        )
        self.assertEqual(res_fail.status_code, 403)
        self.assertEqual(Task.objects.count(), 1)

        # Valid superuser password attempt
        res_ok = self.client.post(
            reverse('clear_all_tasks'),
            data=json.dumps({'password': 'supersecret'}),
            content_type='application/json'
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertEqual(Task.objects.count(), 0)







