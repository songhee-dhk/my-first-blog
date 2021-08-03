from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from .models import Post, Comment
from .forms import PostForm, CommentForm
from django.http import JsonResponse
from http import HTTPStatus
import json
from django.forms.models import model_to_dict
from .helpers import CustomDateTimeJSONEncoder
from django.views.decorators.http import require_POST


def post_list(request):
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by(
        "published_date"
    )
    data = json.dumps(
        [model_to_dict(post) for post in posts], cls=CustomDateTimeJSONEncoder
    )

    return JsonResponse({"data": data}, status=HTTPStatus.OK)


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)

    return JsonResponse(model_to_dict(post), status=HTTPStatus.OK)


@login_required
def post_new(request):
    form = PostForm
    return render(request, "blog/post_edit.html", {"form": form})


@login_required
@require_POST
def post_new(request):
    data = json.loads(request.body)

    if "title" in data and "text" in data:
        post = Post.objects.create(
            author=request.user, title=data["title"], text=data["text"]
        )
        post.save()
        return JsonResponse(data=model_to_dict(post),status=HTTPStatus.CREATED)
    else:
        return JsonResponse({"message": "잘못된 입력입니다"}, status=HTTPStatus.BAD_REQUEST)


@login_required
@require_POST
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    data = json.loads(request.body)

    if "title" in data and "text" in data:
        post.title = data["title"]
        post.text = data["text"]
        post.author = request.user
        post.save()
        return JsonResponse(model_to_dict(post), status=HTTPStatus.OK)
    else:
        return JsonResponse({"message": "잘못된 입력입니다"}, status=HTTPStatus.BAD_REQUEST)


@login_required
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by("created_date")
    return render(request, "blog/post_draft_list.html", {"posts": posts})


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


def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.save()
        return redirect("post_detail", pk=post.pk)


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
