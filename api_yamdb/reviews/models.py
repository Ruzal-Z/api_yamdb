from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from reviews.validators import (
    validate_username,
    validate_username_bad_sign,
    validate_year,
)

MAX_CHAR_LENGTH = 150
MAX_EMAIL_LENGTH = 254
AUTHOR_TEXT_PUBDATE = 'Автор: {}> Текст: {:.15}> Дата публикации: {}'
REVIEW = '{}> Произведение: {}> Оценка: {}'
COMMENT = '{}> Отзыв: {:.}'


class Role(models.TextChoices):
    USER = 'user', 'пользователь'
    MODERATOR = 'moderator', 'модератор'
    ADMIN = 'admin', 'администратор'


class User(AbstractUser):
    username = models.CharField(
        max_length=MAX_CHAR_LENGTH,
        unique=True,
        validators=[validate_username, validate_username_bad_sign],
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        blank=False,
    )
    first_name = models.CharField(
        max_length=MAX_CHAR_LENGTH,
        blank=True,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=MAX_CHAR_LENGTH,
        blank=True,
        verbose_name='Фамилия',
    )
    bio = models.TextField(
        blank=True,
        verbose_name='Биография',
    )
    role = models.CharField(
        max_length=len(max(Role.values, key=len)),
        choices=Role.choices,
        default=Role.USER,
        verbose_name='Роли',
    )

    @property
    def is_user(self):
        return self.role == Role.USER

    @property
    def is_admin(self):
        return self.role == Role.ADMIN or self.is_staff

    @property
    def is_moderator(self):
        return self.role == Role.MODERATOR

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return self.username


class NameAndSlugAbstractModel(models.Model):
    name = models.CharField(max_length=256, verbose_name='Название')
    slug = models.SlugField(
        max_length=50,
        unique=True,
    )

    class Meta:
        abstract = True
        ordering = ('name',)

    def __str__(self):
        return self.name


class Category(NameAndSlugAbstractModel):
    class Meta(NameAndSlugAbstractModel.Meta):
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'


class Genre(NameAndSlugAbstractModel):
    class Meta(NameAndSlugAbstractModel.Meta):
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'


class Title(models.Model):
    name = models.CharField(
        max_length=256,
        verbose_name='название',
    )
    year = models.SmallIntegerField(
        validators=(validate_year,), verbose_name='Год выпуска'
    )
    description = models.TextField(verbose_name='Описание', blank=True)
    category = models.ForeignKey(
        Category,
        related_name='title',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    genre = models.ManyToManyField(
        Genre,
        through='GenreTitle',
        related_name='title',
        blank=True,
    )

    class Meta:
        verbose_name = 'Произведения'
        verbose_name_plural = 'Произведении'
        ordering = ('name',)

    def __str__(self):
        return self.name


class AuthorTextPubDateAbstractModel(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='%(class)ss'
    )
    text = models.TextField()
    pub_date = models.DateTimeField(
        'Дата ревью',
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        abstract = True
        ordering = ('-pub_date',)

    def __str__(self):
        return AUTHOR_TEXT_PUBDATE.format(
            self.author.username, self.text, self.pub_date
        )


class Review(AuthorTextPubDateAbstractModel):
    title = models.ForeignKey(
        Title, on_delete=models.CASCADE, related_name='reviews'
    )
    score = models.IntegerField(
        'Оценка',
        default=0,
        validators=[MaxValueValidator(10), MinValueValidator(1)],
    )

    class Meta(AuthorTextPubDateAbstractModel.Meta):
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        constraints = [
            models.UniqueConstraint(
                name='unique_review', fields=['author', 'title']
            )
        ]

    def __str__(self):
        return REVIEW.format(super(), self.title.name, self.score)


class Comment(AuthorTextPubDateAbstractModel):
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name='comments'
    )

    class Meta(AuthorTextPubDateAbstractModel.Meta):
        verbose_name = 'Коментария'
        verbose_name_plural = 'Коментарии'

    def __str__(self):
        return COMMENT.format(super(), self.review.text)


class GenreTitle(models.Model):
    title_id = models.ForeignKey(Title, on_delete=models.CASCADE)
    genre_id = models.ForeignKey(Genre, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.title} {self.genre}'
