from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post


User = get_user_model()


class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Rin')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.rin_client = Client()
        self.rin_client.force_login(self.user)

    def test_create_post(self):
        new_post = {
            'text': 'Новый пост',
            'group': self.group.pk
        }
        self.rin_client.post(
            reverse('posts:post_create'), data=new_post, follow=True)
        post = Post.objects.first()
        self.assertEqual(post.text, new_post['text'])
        self.assertEqual(post.group.slug, self.group.slug)
        self.assertEqual(post.author, self.user)

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
