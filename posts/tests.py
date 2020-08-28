import time

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from .models import Comment, Follow, Group, Post, User


class ProfileTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.client_test = Client()
        self.user_is_login = User.objects.create(username='dummy')

        self.user_not_login = User.objects.create(
            username='second_dummy'
        )

        self.client.force_login(self.user_is_login)

        self.group = Group.objects.create(
            title='test group',
            slug='test',
            description='testing'
        )

    def test_create_profile(self):
        response = self.client.get(reverse('profile', kwargs={'username': self.user_is_login.username}))
        self.assertEqual(response.status_code, 200)

    def test_create_post(self):
        text = 'mmm testing'
        response = self.client.post(
            reverse('new_post'),
            {'text': text, 'author': self.user_is_login, 'group': self.group.id},
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        post_list = Post.objects.filter(text=text, author=self.user_is_login, group=self.group)
        self.assertEqual(post_list.count(), 1)
        post_count = Post.objects.all()
        self.assertEqual(post_count.count(), 1)

    def test_login_redirect(self):
        text = 'mmm testing'
        response = self.client_test.post(
            reverse('new_post'),
            {'text': text, 'author': self.user_not_login, 'group': self.group.id},
            follow=True
        )
        self.assertRedirects(response, reverse('login') + '?next=' + reverse('new_post'))
        self.assertEqual(Post.objects.count(), 0)

    def check_post(self, url, text, author, group):
        response = self.client.get(url)
        if response.context.get('paginator') is None:
            post = response.context.get('post')
        else:
            p = response.context.get('paginator')
            self.assertEqual(1, p.count)
            post = response.context['page'][0]
        self.assertEqual(post.text, text)
        self.assertEqual(post.author, author)
        self.assertEqual(post.group, group)

    def test_published_post(self):
        text = 'mmm testing'
        post = Post.objects.create(
            text=text,
            author=self.user_is_login,
            group=self.group
        )
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user_is_login}),
            reverse(
                'post',
                kwargs={'username': self.user_is_login, 'post_id': post.id}
            ),
        ]

        for url in urls:
            self.check_post(url, text, self.user_is_login, self.group)

    def test_edit(self):
        text = 'mmm testing'
        post = Post.objects.create(
            text='111',
            author=self.user_is_login,
            group=self.group
        )
        self.client.post(
            reverse('post_edit', kwargs={'username': self.user_is_login, 'post_id': post.id}),
            {'text': text, 'group': self.group.id},
            follow=True
        )
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user_is_login}),
            reverse(
                'post',
                kwargs={'username': self.user_is_login, 'post_id': post.id}
            ),
            reverse('group', kwargs={'slug': self.group.slug}),
        ]

        for url in urls:
            self.check_post(url, text, self.user_is_login, self.group)
            self.check_post(url, text, self.user_is_login, self.group)

    def test_cash(self):
        cache.clear()
        post_one = Post.objects.create(
            text='111',
            author=self.user_is_login,
            group=self.group
            )
        response = self.client.get(reverse('index'))
        self.assertContains(response, post_one.text)
        
        post_two = Post.objects.create(
            text='222',
            author=self.user_is_login,
            group=self.group
            )
        response = self.client.get(reverse('index'))
        self.assertNotContains(response, post_two.text)
        cache.clear()
        response = self.client.get(reverse('index'))
        self.assertContains(response, post_two.text)

    def test_follow_and_unfollow(self):
        author = User.objects.create(
            username='dude',
            password='123'
        )
        self.client.get(reverse('profile_follow', args=[author]))
        sub_count = Follow.objects.filter(user=self.user_is_login, author=author).count()
        self.assertEqual(sub_count, 1)
        self.assertEqual(Follow.objects.count(), 1)
        
        self.client.get(reverse('profile_unfollow', args=[author]))
        sub_count = Follow.objects.filter(user=self.user_is_login, author=author).count()
        self.assertEqual(sub_count, 0)
        self.assertEqual(Follow.objects.count(), 0)

    def test_new_follow_post(self):
        author = User.objects.create(
            username='dude',
            password='123'
        )
        self.client.get(reverse('profile_follow', args=[author]))
        post = Post.objects.create(
            text='111',
            author=author,
            group=self.group
        )
        response = self.client.get(reverse('follow_index'))
        self.assertContains(response, post.text)
        cache.clear()
        self.client_test.force_login(self.user_not_login)
        response = self.client_test.get(reverse('follow_index'))
        self.assertNotContains(response, post.text)
    
    def test_auth_comment(self):
        comment_text = 'testcomment'
        post = Post.objects.create(
            text='111',
            author=self.user_is_login,
            group=self.group
        )
        
        response = self.client.post(
            reverse('add_comment', args=[self.user_is_login, post.id]),
            {'text': comment_text},
            follow=True
            )
        self.assertContains(response, comment_text)
        comments = Comment.objects.filter(text=comment_text)
        self.assertEqual(comments.count(), 1)

        another_text = 'anothercomment'
        response = self.client_test.post(
            reverse('add_comment', args=[self.user_is_login, post.id]),
            {'text': another_text},
            follow=True
            )
        self.assertNotContains(response, comment_text)
        comments = Comment.objects.filter(text=another_text)
        self.assertEqual(comments.count(), 0)


class ImageTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_is_login = User.objects.create(username='dummy')

        self.user_not_login = User.objects.create(
            username='second_dummy'
        )

        self.client.force_login(self.user_is_login)
        self.group = Group.objects.create(
            title='test group',
            slug='test',
            description='testing'
        )

    def test_return_404(self):
        response = self.client.get('0000001/')
        self.assertEqual(response.status_code, 404)

    def test_image(self):
        text = 'mmm testing'
        post_one = Post.objects.create(
            text=text,
            author=self.user_is_login,
            group=self.group
        )
        with open('posts/file.jpg', 'rb') as img:
            post = self.client.post(
                reverse('post_edit', kwargs={'username': self.user_is_login, 'post_id': post_one.id}),
                {'author': self.user_is_login, 'text': 'post with image', 'image': img}
                )
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user_is_login}),
            reverse(
                'post',
                kwargs={'username': self.user_is_login, 'post_id': post_one.id}
            ),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'img')
            self.assertEqual(Post.objects.count(), 1)

    def test_not_img(self):
        text = 'mmm testing'
        post_one = Post.objects.create(
            text=text,
            author=self.user_is_login,
            group=self.group
            )
        with open('posts/admin.py', 'rb') as img:
            post = self.client.post(
                reverse('post_edit', kwargs={'username': self.user_is_login, 'post_id': post_one.id}),
                {'author': self.user_is_login, 'text': 'post with image', 'image': img}
                )
