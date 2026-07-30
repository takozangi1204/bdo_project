import json
from django.test import TestCase, Client, override_settings
from django.urls import reverse


@override_settings(APP_EDIT_PASSWORD='testpassword')
class ModeToggleAPITestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_default_mode_is_view(self):
        res = self.client.get(reverse('mode_status'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['mode'], 'view')

    def test_toggle_mode_invalid_password(self):
        res = self.client.post(
            reverse('mode_toggle'),
            data=json.dumps({'password': 'wrongpassword'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()['status'], 'error')

    def test_toggle_mode_valid_password(self):
        res = self.client.post(
            reverse('mode_toggle'),
            data=json.dumps({'password': 'testpassword'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()['status'], 'success')
        self.assertEqual(res.json()['mode'], 'edit')

        # Check status endpoint now returns edit
        status_res = self.client.get(reverse('mode_status'))
        self.assertEqual(status_res.json()['mode'], 'edit')

        # Switch back from edit to view (no password required)
        res_view = self.client.post(
            reverse('mode_toggle'),
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(res_view.status_code, 200)
        self.assertEqual(res_view.json()['mode'], 'view')
