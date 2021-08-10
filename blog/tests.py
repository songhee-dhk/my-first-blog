import json
from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Post, Comment

import json


class APITestMixin:
    def get(self, path, data={}, *args, **kwargs):
        return self.client.get(path, data, *args, **kwargs)

    def post(self, path, data={}, *args, **kwargs):
        return self.client.post(
            path, json.dumps(data), content_type="application/json", *args, **kwargs
        )


class TestPost(APITestMixin, TestCase):
    def _create_post(self, user, title, text):
        post = Post.objects.create(
            author=user, title=title, text=text, published_date=timezone.now()
        )
        return post

    def _login_user(self):
        return self.client.login(username=self.username, password=self.password)

    def setUp(self):
        self.post_author = User.objects.create_user("author")

        self.username = "username"
        self.password = "password"
        self.user = User.objects.create_user(self.username)
        self.user.set_password(self.password)
        self.user.save()

    def test_get_all_posts(self):
        # Given : 새로운 Post 30개 생성
        for _ in range(30):
            self._create_post(self.user, "Post title", "Post content")

        # When : 모든 Post 조회
        response = self.get(reverse("post_list"))

        # Then : 생성된 모든 Post가 정상적으로 조회되는지 확인
        data = response.json()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(data), 30)

    def test_get_post_detail(self):
        # Given : 새로운 Post 생성
        saved_post = self._create_post(self.user, "Post title", "Post content")

        # When : 생성된 Post 단건 조회
        response = self.get(reverse("post_detail", kwargs={"pk": saved_post.pk}))

        # Then : 조회한 Post와 생성한 Post가 일치하는지 확인
        post = response.json()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post["author"], self.user.pk)
        self.assertEqual(post["title"], saved_post.title)
        self.assertEqual(post["text"], saved_post.text)

    def test_return_404_when_request_not_exist_post(self):
        # Given : 존재하지 않는 Post pk
        not_exist_pk = 1234

        # When : 존재하지 않는 Post 조회
        response = self.get(reverse("post_detail", kwargs={"pk": not_exist_pk}))

        # Then : 404 에러를 반환
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_return_created_when_create_post(self):
        # Given : 로그인한 유저와 Post를 정상적으로 생성할 수 있는 데이터
        self._login_user()
        data = {"title": "Post Title", "text": "Post Text"}

        # When : 정상적인 Post 등록
        response = self.post(reverse("post_new"), data)

        # Then : 정상적으로 Post의 값들이 생성되었는지 확인
        post = response.json()

        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertIn("id", post)
        self.assertEqual(post["author"], self.user.pk)

    def test_redirect_login_page_when_not_logged_in_user_attempts_to_create_a_post(
        self,
    ):
        # Given : 로그인하지 않은 상태와 정상적으로 Post를 생성할 수 있는 데이터
        data = {"title": "Post Title", "text": "Post Text"}

        # When : Post를 생성
        response = self.post(reverse("post_new"), data)

        # Then : Post가 생성되지 않고 로그인 페이지로 이동하게 한다
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_return_bad_request_when_create_post_in_empty_data(self):
        # Given : 비어있는 Form
        self._login_user()
        empty_reqeust_data = {}

        # When : 빈 Form으로 Post 생성을 요청
        response = self.post(reverse("post_new"), empty_reqeust_data)

        # Then : Post가 정상적으로 생성되지 않고, Bad_Request를 반환
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_return_ok_when_update_post(self):
        # Given : 정상적으로 Post의 수정이 가능한 데이터
        exist_post = self._create_post(self.post_author, "Old Title", "Old Text")
        self._login_user()
        update_request_data = {"title": "New Title", "text": "New Text"}

        # When : Post 수정 내용과 함께 요청을 보냄
        response = self.post(
            reverse("post_edit", kwargs={"pk": exist_post.pk}), update_request_data
        )

        # Then : Post의 내용이 정상적으로 수정
        post = response.json()

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(post["author"], self.user.pk)
        self.assertEqual(post["title"], update_request_data["title"])
        self.assertEqual(post["text"], update_request_data["text"])

    def test_redirect_login_page_when_not_logged_in_user_attempts_to_update_post(self):
        # Given : 로그인하지 않은 상태와 정상적으로 Post를 수정할 수 있는 데이터
        exist_post = self._create_post(self.post_author, "Old Title", "Old Text")
        update_request_data = {"title": "New Title", "text": "New Text"}

        # When : Post의 수정을 요청
        response = self.post(
            reverse("post_edit", kwargs={"pk": exist_post.pk}), update_request_data
        )

        # Then : Post가 수정되지 않는다
        self.assertNotEqual(exist_post.author, self.user.pk)
        self.assertNotEqual(exist_post.title, update_request_data["title"])
        self.assertNotEqual(exist_post.text, update_request_data["text"])

        # And : 로그인 페이지로 이동
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_return_bad_request_when_attempts_to_update_post_in_empty_data(self):
        # Given : 로그인했지만 비어있는 Form
        exist_post = self._create_post(self.post_author, "Old Title", "Old Text")
        self._login_user()
        empty_request_data = {}

        # When : 빈 Form으로 Post 수정을 요청
        response = self.post(
            reverse("post_edit", kwargs={"pk": exist_post.pk}), empty_request_data
        )

        # Then : Bad_Request를 반환
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_should_return_404_when_attempts_to_update_not_exist_post(self):
        # Given : 존재하지 않는 Post pk
        self._login_user()
        not_exist_pk = 1234

        # When : 존재하지 않는 Post의 수정을 요청
        response = self.post(
            reverse("post_edit", kwargs={"pk": not_exist_pk}),
        )

        # Then : Not Found를 반환
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_publish_post_return_ok(self):
        # Given : publish 되지 않은 Post 생성
        self._login_user()
        not_published_post = Post.objects.create(
            author=self.user, title="Post title", text="Post text"
        )

        # When : Post의 publish 요청
        response = self.post(
            reverse("post_publish", kwargs={"pk": not_published_post.pk})
        )

        # Then : 200 OK를 반환
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # And : Post의 published_date 값이 생성
        self.assertTrue(response.json()["published_date"])

    def test_delete_post_return_no_content(self):
        # Given : 삭제할 Post를 생성
        post = self._create_post(self.user, "Post title", "Post content")

        # When : Post의 삭제를 요청
        response = self.client.delete(reverse("post_remove", kwargs={"pk": post.pk}))

        # Then : 204 No Content를 반환
        self.assertEqual(response.status_code, HTTPStatus.NO_CONTENT)

        # And : 정상적으로 Post가 삭제되어 존재하는 Post가 없어짐
        self.assertFalse(Post.objects.exists())

    def test_return_not_found_when_delete_not_exist_post(self):
        # Given : 존재하지 않는 Post의 pk
        not_exist_pk = 1234

        # When : Post의 삭제를 요청
        response = self.client.delete(
            reverse("post_remove", kwargs={"pk": not_exist_pk})
        )

        # Then : 404 Not found를 반환
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


class TestComment(APITestMixin, TestCase):
    def _login_user(self):
        return self.client.login(username=self.username, password=self.password)

    def _create_comment(self, post, author, text):
        return Comment.objects.create(post=post, author=author, text=text)

    def setUp(self):
        self.username = "username"
        self.password = "password"
        self.user = User.objects.create_user(self.username)
        self.user.set_password(self.password)
        self.user.save()

        self.saved_post = Post.objects.create(
            author=self.user, title="Post title", text="Post text"
        )

    def test_return_ok_when_request_comment_list(self):
        # Given : Post에 10개의 Comment 생성
        author = "author"
        text = "comment text"
        for _ in range(10):
            self._create_comment(self.saved_post, author, text)

        # When : Comment가 작성된 Post에 있는 모든 Comment를 조회
        response = self.get(reverse("comment_list", kwargs={"pk": self.saved_post.pk}))

        # Then : 200 OK가 반환
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # And : Comment들이 정상적으로 모두 반환
        data = response.json()
        random_comment_pk = 3
        comment = data[random_comment_pk]

        self.assertEqual(len(data), 10)
        self.assertEqual(comment["author"], author)
        self.assertEqual(comment["text"], text)

    def test_return_not_found_when_request_not_exist_post_comment_list(self):
        # Given : 존재하지 않는 Post의 pk
        not_exist_post_pk = 1234

        # When : 존재하지 않는 Post의 Comment 조회를 요청
        response = self.get(reverse("comment_list", kwargs={"pk": not_exist_post_pk}))

        # Then : 404 not found를 반환
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_should_return_ok_when_create_comment(self):
        # Given : 정상적으로 Comment 작성이 가능한 데이터
        valid_request_data = {"author": "comment author", "text": "comment text"}

        # When : Comment의 생성을 요청
        response = self.post(
            reverse("add_comment_to_post", kwargs={"pk": self.saved_post.pk}),
            valid_request_data,
        )

        # Then : 201 Created가 반환
        self.assertEqual(response.status_code, HTTPStatus.CREATED)

        # And : 생성 후 반환된 데이터와 전달한 데이터가 일치하는지 확인
        data = response.json()

        self.assertTrue(data["id"])
        self.assertEqual(data["author"], valid_request_data["author"])
        self.assertEqual(data["text"], valid_request_data["text"])

    def test_should_return_404_when_attempts_to_add_comment_to_not_exist_post(self):
        # Given : 없는 Post의 pk와 정상적으로 Comment의 작성이 가능한 데이터
        not_exist_post_pk = 1234
        valid_request_data = {"author": "comment author", "text": "comment text"}

        # When : Comment의 생성을 요청
        response = self.post(
            reverse("add_comment_to_post", kwargs={"pk": not_exist_post_pk}),
            valid_request_data,
        )

        # Then : 404 Not found가 반환
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_return_bad_request_when_add_invalid_comment(self):
        # Given : 정상적으로 Comment를 등록할 수 없는 데이터
        invalid_request_data = {}

        # When : 비어있는 Form으로 Comment 생성 요청
        response = self.post(
            reverse("add_comment_to_post", kwargs={"pk": self.saved_post.pk}),
            invalid_request_data,
        )

        # Then : 400 Bad Request를 반환한다
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_return_ok_when_request_update_comment_on_valid_data(self):
        # Given : 미리 생성된 Comment와 정상적으로 update할 수 있는 데이터
        saved_comment = self._create_comment(self.saved_post, "old author", "old text")
        valid_request_data = {"author": "update author", "text": "update text"}

        # When : 정상적으로 Comment의 수정을 요청
        response = self.post(
            reverse("comment_edit", kwargs={"pk": saved_comment.pk}), valid_request_data
        )

        # Then : 200 ok를 반환
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # And : 정상적으로 수정된 내용이 반환
        data = response.json()

        self.assertEqual(data["author"], valid_request_data["author"])
        self.assertEqual(data["text"], valid_request_data["text"])

    def test_return_bad_request_when_request_update_comment_on_invalid_data(self):
        # Given : 미리 생성된 Comment와 비어있는 데이터
        saved_comment = self._create_comment(self.saved_post, "old author", "old text")
        empty_request_data = {}

        # When : 정상적으로 Comment의 수정을 요청
        response = self.post(
            reverse("comment_edit", kwargs={"pk": saved_comment.pk}), empty_request_data
        )

        # Then : bad request를 반환
        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)

    def test_return_404_when_request_update_not_exist_comment(self):
        # Given : 존재하지 않는 comment의 pk와 정상적으로 수정이 가능한 form
        not_exist_comment_pk = 1234
        valid_request_data = {"author": "update author", "text": "update text"}

        # When : comment의 수정을 요청
        response = self.post(
            reverse("comment_edit", kwargs={"pk": not_exist_comment_pk}),
            valid_request_data,
        )

        # Then : 404 not found를 반환
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_return_ok_when_request_approve_comment(self):
        # Given : 아직 approve 되지 않은 comment
        self._login_user()
        saved_comment = self._create_comment(self.saved_post, "author", "text")

        # When : comment의 approve를 요청
        response = self.post(
            reverse("comment_approve", kwargs={"pk": saved_comment.pk})
        )

        # Then : 200 ok를 반환
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # And : comment의 approved_comment 값이 True로 변경
        data = response.json()

        self.assertTrue(data["approved_comment"])

    def test_return_404_when_request_approve_not_exist_comment(self):
        # Given : 존재하지 않는 comment의 pk
        self._login_user()
        not_exist_comment_pk = 1234

        # When : comment의 approve를 요청
        response = self.post(
            reverse("comment_approve", kwargs={"pk": not_exist_comment_pk})
        )

        # Then : 404 not found를 반환
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
