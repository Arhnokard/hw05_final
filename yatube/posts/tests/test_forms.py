import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, Comment


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.LOGIN_URL = '/auth/login/'
        cls.ADD_COMMENT_URL = f'/posts/1/comment/'
        cls.user = User.objects.create(username='Rin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.rin_client = Client()
        self.rin_client.force_login(self.user)

    def test_create_post(self):
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Новый пост',
            'group': self.group.pk,
            'image': uploaded
        }
        self.rin_client.post(
            reverse('posts:post_create'), data=form_data, follow=True)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.slug, self.group.slug)
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image, self.post.image)

    def test_edit_post(self):
        original_post = self.post
        edit_dict = {
            'text': 'Редактированый пост',
            'group': self.group.pk
        }
        self.rin_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': original_post.pk}),
            data=edit_dict, follow=True)
        edit_post = Post.objects.get(pk=original_post.pk)
        self.assertEqual(edit_post.text, edit_dict['text'])
        self.assertEqual(edit_post.group.slug, self.group.slug)
        self.assertEqual(edit_post.author, self.user)

    def test_guest_client_non_create_post(self):
        new_post = {
            'text': 'Новый пост',
            'group': self.group.pk
        }
        response = self.guest_client.post(
            reverse('posts:post_create'), data=new_post, follow=True)
        self.assertRedirects(response, '%s?next=%s' %
                             (reverse('users:login'),
                              reverse('posts:post_create')))

    def test_add_comment_quest_client(self):
        comment = {
            'text': 'комментарий'
        }
        self.guest_client.post(self.ADD_COMMENT_URL,data=comment, follow=True)
        self.assertFalse(Comment.objects.filter(
                         text=comment['text']).exists())

    def test_add_comment_author_client(self):
        comment = {
            'text': 'комментарий'
        }
        self.rin_client.post(self.ADD_COMMENT_URL,data=comment, follow=True)
        self.assertTrue(Comment.objects.filter(text=comment['text']).exists())
