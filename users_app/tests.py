from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse


class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='business-user', password='test-password')

    def test_login_rejects_external_redirect_targets(self):
        response = self.client.post(reverse('login'), {
            'username': 'business-user',
            'password': 'test-password',
            'next': 'https://example.invalid/',
        })

        self.assertRedirects(response, reverse('dashboard_home'), fetch_redirect_response=False)

    def test_login_preserves_safe_local_redirect_target(self):
        response = self.client.post(reverse('login'), {
            'username': 'business-user',
            'password': 'test-password',
            'next': '/reports/',
        })

        self.assertRedirects(response, '/reports/', fetch_redirect_response=False)

    def test_login_accepts_current_csrf_cookie_token(self):
        client = Client(enforce_csrf_checks=True)
        response = client.get(reverse('login'))
        csrf_cookie = response.cookies['csrftoken'].value

        response = client.post(reverse('login'), {
            'username': 'business-user',
            'password': 'test-password',
            'csrfmiddlewaretoken': csrf_cookie,
        })

        self.assertRedirects(
            response,
            reverse('dashboard_home'),
            fetch_redirect_response=False,
        )

    def test_logout_requires_post(self):
        self.client.force_login(self.user)

        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        response = self.client.post(reverse('logout'))

        self.assertRedirects(response, reverse('login'), fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)
