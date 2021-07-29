from django.test import TestCase
from .models import Post, Comment
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from http import HTTPStatus

import json


class TestPost(TestCase):
    def _create_post(self, user, title, text):
        post = Post.objects.create(
            author=user, title=title, text=text, published_date=timezone.now()
        )
        return post

    def _login_user(self):
        return self.client.login(username=self.username, password=self.password)

    def setUp(self):
        self.username = "username"
        self.password = "password"
        self.user = User.objects.create(username=self.username)
        self.user.set_password(self.password)
        self.user.save()

    def test_get_all_posts(self):
        # Given : 새로운 Post 30개 생성
        for _ in range(30):
            self._create_post(self.user, "Post title", "Post content")

        # When : 모든 Post 조회
        response = self.client.get(reverse("post_list"))

        # Then : 생성된 모든 Post가 정상적으로 조회되는지 확인
        data = json.loads(response.json()["data"])

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(data), 30)

    def test_get_post_detail(self):
        # Given : 새로운 Post 생성
        saved_post = self._create_post(self.user, "Post title", "Post content")

        # When : 생성된 Post 단건 조회
        response = self.client.get(reverse("post_detail", kwargs={"pk": saved_post.pk}))

        # Then : 조회한 Post와 생성한 Post가 일치하는지 확인
        post = json.loads(response.json()["data"])[0]["fields"]

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post["author"], self.user.pk)
        self.assertEqual(post["title"], saved_post.title)
        self.assertEqual(post["text"], saved_post.text)

    def test_404_post_not_exist(self):
        # Given : 존재하지 않는 Post pk
        not_exist_pk = 1234

        # When : 존재하지 않는 Post 조회
        response = self.client.get(reverse("post_detail", kwargs={"pk": not_exist_pk}))

        # Then : 404 에러를 반환
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_create_post(self):
        # Given : 로그인한 유저와 Post를 정상적으로 생성할 수 있는 데이터
        self._login_user()
        data = {"title": "Post Title", "text": "Post Text"}

        # When : 정상적인 Post 등록
        response = self.client.post(reverse("post_new"), data=data)

        # Then : 정상적으로 Post의 값들이 생성되었는지 확인
        data = json.loads(response.json()["data"])[0]
        post = data["fields"]

        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertIn("pk", data)
        self.assertEqual(post["author"], self.user.pk)
        self.assertIsNone(post["published_date"])

    def test_redirect_login_page_when_not_login(self):
        # Given : 로그인하지 않은 상태와 정상적으로 Post를 생성할 수 있는 데이터
        data = {"title": "Post Title", "text": "Post Text"}

        # When : Post를 생성
        response = self.client.post(reverse("post_new"), data=data)

        # Then : Post가 생성되지 않고 로그인 페이지로 이동하게 한다
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_bad_request_when_empty_form(self):
        # Given : 비어있는 Form
        self._login_user()
        empty_form = {}

        # When : 빈 Form으로 Post 생성을 요청
        response = self.client.post(reverse("post_new"), data=empty_form)

        # Then : Post가 정상적으로 생성되지 않고, Bad_Request를 반환
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
