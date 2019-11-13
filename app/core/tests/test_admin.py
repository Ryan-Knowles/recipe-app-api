from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse


class AdminSiteTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='ryan.knowles@bridgevine.com',
            password='test123'
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='pug@bridgevine.com',
            password='notsecure',
            name='Test user full name'
        )

    def test_users_listed(self):
        """
        Test that users are listed on the user page
        """

        url = reverse('admin:core_user_changelist')
        rsp = self.client.get(url)

        # Tests response for 200 status code and that the html
        # contains the user's name and user's email
        self.assertContains(rsp, self.user.name)
        self.assertContains(rsp, self.user.email)

    def test_user_change_page(self):
        """
        Test that the user change page works
        :return:
        """

        url = reverse('admin:core_user_change', args=[self.user.id])
        rsp = self.client.get(url)

        self.assertEqual(rsp.status_code, 200)

    def test_create_user_page(self):
        """
        Test that the create user page works
        :return:
        """

        url = reverse('admin:core_user_add')
        rsp = self.client.get(url)

        self.assertEqual(rsp.status_code, 200)
