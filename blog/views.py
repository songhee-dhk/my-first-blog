from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Post, Comment
from django.http import JsonResponse
from http import HTTPStatus
import json
from django.forms.models import model_to_dict
from .helpers import CustomDateTimeJSONEncoder
from django.views.decorators.http import require_POST
from django.db.models import prefetch_related_objects


def post_list(request):
    posts = (
        Post.objects
            # .prefetch_related("comments")
        .filter(published_date__lte=timezone.now())
        .order_by("published_date")
    )

    data = json.dumps(
        [model_to_dict(post) for post in posts], cls=CustomDateTimeJSONEncoder
    )

    return JsonResponse({"data": data}, status=HTTPStatus.OK)


def post_detail(request, pk):
    # post = get_object_or_404(Post, pk=pk)
    post = Post.objects.prefetch_related("comments").get(pk=pk)
    data = model_to_dict(post)
    data["comments"] = [model_to_dict(comment) for comment in post.comments.all()]

    print(Post.objects.select_related().get(pk=pk))

    return JsonResponse(data, status=HTTPStatus.OK)


@login_required
@require_POST
def post_new(request):
    data = json.loads(request.body)

    try:
        post = Post.objects.create(
            author=request.user, title=data["title"], text=data["text"]
        )
    except KeyError:
        return JsonResponse({"message": "잘못된 입력입니다"}, status=HTTPStatus.BAD_REQUEST)
    else:
        return JsonResponse(model_to_dict(post), status=HTTPStatus.CREATED)


@login_required
@require_POST
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)

    data = json.loads(request.body)
    post.author = request.user
    try:
        post.title = data["title"]
        post.text = data["text"]
    except KeyError:
        return JsonResponse({"message": "잘못된 입력입니다"}, status=HTTPStatus.BAD_REQUEST)
    else:
        post.save()
        return JsonResponse(model_to_dict(post), status=HTTPStatus.OK)


@login_required
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by("created_date")
    data = json.dumps(
        [model_to_dict(post) for post in posts], cls=CustomDateTimeJSONEncoder
    )
    return JsonResponse({"data": data}, status=HTTPStatus.OK)


@login_required
@require_POST
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return JsonResponse(model_to_dict(post), status=HTTPStatus.OK)


def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect("post_list")


@require_POST
def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    # post = Post.objects.get(pk=pk)
    data = json.loads(request.body)

    try:
        comment = Comment.objects.create(
            post=post, author=data["author"], text=data["text"]
        )
        print(Post.objects.prefetch_related("comments").filter(pk=pk)[0].comments)
    except KeyError:
        return JsonResponse({"message": "잘못된 입력입니다"}, status=HTTPStatus.BAD_REQUEST)
    else:
        return JsonResponse(model_to_dict(comment), status=HTTPStatus.CREATED)


@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    return redirect("post_detail", pk=comment.post.pk)


@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return redirect("post_detail", pk=comment.post.pk)
