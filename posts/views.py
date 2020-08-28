import datetime as dt

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'group.html',
        {'group': group, 'page': page, 'paginator': paginator}
    )


@login_required
def new_post(request):
    f = PostForm(request.POST or None)
    if f.is_valid():
        f.instance.author = request.user
        f.save()
        return redirect('index')
    return render(request, 'new.html', {'form': f})


def profile(request, username):
    user = get_object_or_404(User, username=username)
    post_list = user.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=user
            ).exists()
    return render(request, 'profile.html', {
        'page': page,
        'paginator': paginator,
        'post_author': user,
        'following': following
        })


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    # post_comment = get_object_or_404(Comment, post=post)
    # items = post_comment.comments.all()
    items = post.comments.all()
    f = CommentForm(request.POST or None)
    return render(request, 'post.html', {
        'form': f,
        'items': items,
        'post': post,
        'post_author': post.author,
    })


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    f = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if post.author == request.user:
        if f.is_valid():
            f.instance.pub_date = dt.datetime.today()
            f.save()
            return redirect('post', username=username, post_id=post_id)
        return render(request, 'new.html', {'form': f, 'post': post})
    return redirect('post', username, post_id)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    f = CommentForm(request.POST or None)
    if f.is_valid():
        f.instance.author = request.user
        f.instance.post_id = post_id
        f.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'post.html', {'form': f, 'post': post, 'post_author': post.author})


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect('profile', username=username)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)
