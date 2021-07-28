from django.test import TestCase
from .models import Post, Comment
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse  # django 버전 문제로 요걸로 해야한다고 합니다..
from http import HTTPStatus

import json


class PostTest(TestCase):
    def _create_post(self, user, title, text):
        post = Post.objects.create(author=user,
                                   title=title, text=text,
                                   published_date=timezone.now())
        return post

    def setUp(self):
        self.user = User.objects.create_user('testuser', 'user@email.com', 'pass1234')
        self.client.login(username=self.user.username, password=self.user.password)

    def test_get_all_posts(self):
        # Given : 새로운 Post 30개 생성
        for _ in range(0, 30):
            self._create_post(self.user, 'Post title', 'Post content')

        # When : 모든 Post 조회
        response = self.client

        # Then : 생성된 모든 Post가 정상적으로 조회되는지 확인
        data = json.loads(response.json()['data'])

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertEqual(30, len(data))

    def test_get_post_detail(self):
        # Given : 새로운 Post 생성
        saved_post = self._create_post(self.user, 'Post title', 'Post content')

        # When : 생성된 Post 단건 조회
        response = self.client.get(reverse('post_detail',
                                           kwargs={'pk': saved_post.pk}))

        # Then : 조회한 Post와 생성한 Post가 일치하는지 확인
        post = json.loads(response.json()['data'])[0]['fields']

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertEqual(self.user.pk, post['author'])
        self.assertEqual(saved_post.title, post['title'])
        self.assertEqual(saved_post.text, post['text'])

    def test_404_post_not_exist(self):
        # When : 존재하지 않은 Post 조회
        response = self.client.get(reverse('post_detail',
                                           kwargs={'pk': 1234}))

        # Then : 404 에러를 반환
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)
