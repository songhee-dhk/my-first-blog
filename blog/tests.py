from django.test import TestCase
from .models import Post, Comment
from django.contrib.auth.models import User
from django.utils import timezone

import json


def get_data_and_fields_response(response):
    data = json.loads(response.json()['data'])
    return data, data[0]['fields']


class PostTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'user@email.com', 'pass1234')
        self.client.login(username=self.user.username, password=self.user.password)

        self.post = Post.objects.create(author=self.user, title='test_title', text='test_text', published_date=timezone.now())
        self.post.save()

    def test_post_list(self):
        response = self.client.get('/')
        data, post = get_data_and_fields_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(post['author'], self.user.pk)
        self.assertEqual(post['title'], self.post.title)
        self.assertEqual(post['text'], self.post.text)

    def test_post_detail(self):
        response = self.client.get('/post/%s/' % self.post.pk)
        data, post = get_data_and_fields_response(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(post['author'], self.user.pk)
        self.assertEqual(post['title'], self.post.title)
        self.assertEqual(post['text'], self.post.text)
