from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post, Comment


User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='коментарий'
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        self.assertEqual(str(self.post),
                         self.post.text[:settings.LIMIT_CHAR_STR])
        self.assertEqual(str(self.group), self.group.title)

    def test_comment_model_correct_object_names(self):
        self.assertEqual(str(self.comment), self.comment.text)

    def test_models_verbose_name(self):
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name, value)

    def test_comment_model_verbose_name(self):
        field_verboses = {
            'text': 'Текст комментария',
            'created': 'Дата коментария'
        }
        for field, value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.comment._meta.get_field(field).verbose_name, value)

    def test_models_help_text(self):
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост'
        }
        for field, value in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(self.post._meta.get_field(field).help_text,
                                 value)

    def test_comment_model_help_text(self):
        field_help_text = {
            'text': 'Введите текст',
        }
        self.assertEqual(self.comment._meta.get_field('text').help_text,
                         field_help_text['text'])
