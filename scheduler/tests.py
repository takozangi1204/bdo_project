import json
from django.test import TestCase, Client
from django.urls import reverse
from .models import Category, Event, Todo, SchedulerSetting, BreakPeriod


class SchedulerAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        session = self.client.session
        session['app_mode'] = 'edit'
        session.save()
        self.cat = Category.objects.create(
            cat_id='mbua514',
            name='MBUA514',
            color='#E63946',
            bg='#FFE0E3',
            sort_order=1
        )

    def test_get_scheduler_data(self):
        response = self.client.get(reverse('scheduler_data'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(len(data['categories']), 1)
        self.assertEqual(data['categories'][0]['name'], 'MBUA514')

    def test_save_and_delete_event(self):
        # Create event
        payload = {
            'event_id': 'evt_1',
            'series_id': 'series_1',
            'date': '2026-08-01',
            'catId': 'mbua514',
            'title': 'Test Event',
            'url': 'https://example.com',
            'startTime': '09:00',
            'endTime': '10:00'
        }
        res = self.client.post(
            reverse('scheduler_save_event'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(Event.objects.filter(event_id='evt_1').exists())

        # Delete event
        res_del = self.client.post(reverse('scheduler_delete_event', kwargs={'event_id': 'evt_1'}))
        self.assertEqual(res_del.status_code, 200)
        self.assertFalse(Event.objects.filter(event_id='evt_1').exists())

    def test_save_and_toggle_todo(self):
        # Create todo
        payload = {
            'todo_id': 'todo_1',
            'date': '2026-08-05',
            'catId': 'mbua514',
            'title': 'Study Django',
            'url': '',
            'completed': False,
            'sort_order': 0
        }
        res = self.client.post(
            reverse('scheduler_save_todo'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        todo = Todo.objects.get(todo_id='todo_1')
        self.assertFalse(todo.completed)

        # Toggle todo
        res_toggle = self.client.post(reverse('scheduler_toggle_todo', kwargs={'todo_id': 'todo_1'}))
        self.assertEqual(res_toggle.status_code, 200)
        todo.refresh_from_db()
        self.assertTrue(todo.completed)

    def test_bulk_save_categories(self):
        payload = {
            'categories': [
                {'id': 'cat_a', 'name': 'Category A', 'color': '#111', 'bg': '#eee'},
                {'id': 'cat_b', 'name': 'Category B', 'color': '#222', 'bg': '#ddd'}
            ]
        }
        res = self.client.post(
            reverse('scheduler_save_categories'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Category.objects.count(), 2)

    def test_save_settings_and_breaks(self):
        payload = {
            'settings': {
                'startDate': '2026-07-06',
                'endDate': '2026-10-18',
                'viewMode': 'events'
            },
            'breaks': [
                {'id': 'b1', 'name': 'Mid-Tri Break', 'startDate': '2026-08-17', 'endDate': '2026-08-30'}
            ]
        }
        res = self.client.post(
            reverse('scheduler_save_settings'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(SchedulerSetting.objects.get(key='startDate').value, '2026-07-06')
        self.assertEqual(BreakPeriod.objects.count(), 1)
        self.assertEqual(BreakPeriod.objects.first().name, 'Mid-Tri Break')



    def test_import_data(self):
        payload = {
            'categories': [
                {'id': 'c1', 'name': 'Cat 1', 'color': '#000', 'bg': '#fff'}
            ],
            'events': [
                {'id': 'ev_imp', 'date': '2026-08-10', 'catId': 'c1', 'title': 'Imported Event'}
            ],
            'todos': [
                {'id': 'td_imp', 'date': '2026-08-10', 'catId': 'c1', 'title': 'Imported Todo'}
            ]
        }
        res = self.client.post(
            reverse('scheduler_import'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(Event.objects.filter(event_id='ev_imp').exists())
        self.assertTrue(Todo.objects.filter(todo_id='td_imp').exists())

    def test_clear_all_requires_superuser_password(self):
        from django.contrib.auth.models import User
        User.objects.create_superuser('admin', 'admin@example.com', 'supersecret')

        Event.objects.create(event_id='e1', date='2026-08-01', category=self.cat, title='E1')
        Todo.objects.create(todo_id='t1', date='2026-08-01', category=self.cat, title='T1')

        # Invalid password attempt
        res_fail = self.client.post(
            reverse('scheduler_clear_all'),
            data=json.dumps({'password': 'wrongpassword'}),
            content_type='application/json'
        )
        self.assertEqual(res_fail.status_code, 403)
        self.assertEqual(Event.objects.count(), 1)
        self.assertEqual(Todo.objects.count(), 1)

        # Valid superuser password attempt
        res_ok = self.client.post(
            reverse('scheduler_clear_all'),
            data=json.dumps({'password': 'supersecret'}),
            content_type='application/json'
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertEqual(Event.objects.count(), 0)

    def test_view_mode_blocks_write(self):
        client = Client()  # Default view mode
        res = client.post(reverse('scheduler_save_event'), data=json.dumps({'title': 'Event'}), content_type='application/json')
        self.assertEqual(res.status_code, 403)
        self.assertEqual(Todo.objects.count(), 0)

