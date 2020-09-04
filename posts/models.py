from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField(verbose_name='группа', max_length=200)
    slug = models.SlugField(unique=True, max_length=30)
    description = models.TextField(verbose_name='описание группы')

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='текст', help_text='напиши свой пост здесь',)
    pub_date = models.DateTimeField(
        'дата публикации',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        verbose_name='автор',
        on_delete=models.CASCADE,
        related_name='posts',
    )
    group = models.ForeignKey(
        Group,
        verbose_name='группа',
        help_text='выбери куда запостить',
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
    )
    image = models.ImageField(
        upload_to='posts/',
        verbose_name='пикча',
        help_text='добавь картинку',
        blank=True,
        null=True
        )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        author = self.author
        group = self.group
        if group is not None:
            responce = f'У {author} новый пост в {group}'
        else:
            responce = f'У {author} новый пост'
        return responce


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='коммент',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    author = models.ForeignKey(
        User,
        verbose_name='автор коммента',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    text = models.TextField(verbose_name='текст коммента', help_text='ваш комментарий',)
    created = models.DateTimeField(
        'дата публикации комментария',
        auto_now_add=True,
        )


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='пользователь, который подписывается',
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        verbose_name='пользователь на которого подписываются',
        on_delete=models.CASCADE,
        related_name='following',
    )
