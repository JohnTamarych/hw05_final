import os

from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
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

        cache.clear()

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
        cache.clear()
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
        post_one = Post.objects.create(
            text='111',
            author=self.user_is_login,
            group=self.group
            )
        response = self.client.get(reverse('index'))
        self.assertContains(response, post_one.text)
        post = response.context.get('post')
        self.assertEqual(post.text, post_one.text)
        self.assertEqual(post.author, post_one.author)
        self.assertEqual(post.group, post_one.group)

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

    def test_follow(self):
        author = User.objects.create(
            username='dude',
            password='123'
        )
        self.client.get(reverse('profile_follow', args=[author]))
        sub_count = Follow.objects.filter(user=self.user_is_login, author=author).count()
        self.assertEqual(sub_count, 1)
        self.assertEqual(Follow.objects.count(), 1)

    def test_unfollow(self):
        author = User.objects.create(
            username='dude',
            password='123'
        )
        Follow.objects.create(user=self.user_is_login, author=author)
        self.client.get(reverse('profile_unfollow', args=[author]))
        self.assertEqual(Follow.objects.count(), 0)

    def test_new_follow_post_appear(self):
        author = User.objects.create(
            username='dude',
            password='123'
        )
        Follow.objects.create(user=self.user_is_login, author=author)
        post = Post.objects.create(
            text='111',
            author=author,
            group=self.group
        )
        url = reverse('follow_index')
        self.check_post(url, post.text, author, self.group)

    def test_new_unfollow_post_not_appear(self):
        author = User.objects.create(
            username='dude',
            password='123'
        )
        Follow.objects.create(user=self.user_is_login, author=author)
        Post.objects.create(
            text='111',
            author=author,
            group=self.group
        )
        self.client_test.force_login(self.user_not_login)
        response = self.client_test.get(reverse('follow_index'))
        p = response.context.get('paginator')
        self.assertEqual(0, p.count)

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
        comments = Comment.objects.filter(text=comment_text, author=self.user_is_login, post=post)
        self.assertEqual(comments.count(), 1)
        p = response.context.get('post')
        self.assertEqual(p.comments.count(), 1)

    def test_not_auth_comment(self):
        another_text = 'anothercomment'
        post = Post.objects.create(
            text='111',
            author=self.user_is_login,
            group=self.group
        )
        response = self.client_test.post(
            reverse('add_comment', args=[self.user_is_login, post.id]),
            {'text': another_text},
            follow=True
            )
        self.assertNotContains(response, another_text)
        comments = Comment.objects.filter(text=another_text, author=self.user_is_login, post=post)
        self.assertEqual(comments.count(), 0)
        response = self.client_test.get(reverse('post', args=[self.user_is_login, post.id]))
        p = response.context.get('post')
        self.assertEqual(p.comments.count(), 0)

    def test_return_404(self):
        response = self.client.get('0000001/')
        self.assertEqual(response.status_code, 404)

    def tearDown(self):
        cache.clear()


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

    def test_image(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
            )
        img = SimpleUploadedFile('small.gif', small_gif, content_type='gif')
        text = 'mmm testing'
        post_one = Post.objects.create(
            text=text,
            author=self.user_is_login,
            group=self.group,
            image=img
        )
        urls = [
            reverse('index'),
            reverse('profile', kwargs={'username': self.user_is_login}),
            reverse(
                'post',
                kwargs={'username': self.user_is_login, 'post_id': post_one.id}
            ),
            reverse('group', kwargs={'slug': self.group.slug}),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, '<img')

    def test_not_img(self):
        test_file = SimpleUploadedFile(
            name='test_file.txt',
            content=b'file contents',
            content_type='text'
            )
        text = 'mmm testing'
        post_one = Post.objects.create(
            text=text,
            author=self.user_is_login,
            group=self.group,
            )
        response = self.client.post(
                reverse('post_edit', args=[self.user_is_login, post_one.id]),
                {'author': self.user_is_login, 'text': text, 'image': test_file}
            )
        self.assertFormError(
            response,
            'form',
            'image',
            'Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением.'
            )

    def tearDown(self):
        cache.clear()
        try:
            os.remove('media/posts/small.gif')
            os.remove('media/posts/test_file.txt')
        except:
            print('file already deleted')
