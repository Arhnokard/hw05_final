from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post


User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.INDEX_URL = '/'
        cls.CREATE_URL = '/create/'
        cls.LOGIN_URL = '/auth/login/'
        cls.UNEXISTING = '/unexisting/'
        cls.user = User.objects.create_user(username='Rin')
        cls.user2 = User.objects.create_user(username='Varian')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост'
        )

    def setUp(self):
        self.GROUP_URL = f'/group/{self.group.slug}/'
        self.PROFILE_URL = f'/profile/{self.user}/'
        self.DETAIL_POST_URL = f'/posts/{self.post.pk}/'
        self.EDIT_URL = f'/posts/{self.post.pk}/edit/'
        self.ADD_COMMENT_URL = f'/posts/{self.post.pk}/comment/'
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.autorized_client = Client()
        self.autorized_client.force_login(self.user2)

    def test_url_autorized_client(self):
        addres_list = [
            self.INDEX_URL, self.GROUP_URL, self.PROFILE_URL,
            self.DETAIL_POST_URL, self.CREATE_URL
        ]
        for addres in addres_list:
            with self.subTest(addres == addres):
                response = self.autorized_client.get(addres)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_guest_client(self):
        response = self.guest_client.get(self.EDIT_URL)
        self.assertRedirects(
            response, (f'{self.LOGIN_URL}?next={self.EDIT_URL}')
        )

    def test_post_edit_url_autorized_client(self):
        response = self.autorized_client.get(self.EDIT_URL)
        self.assertRedirects(response, self.DETAIL_POST_URL)

    def test_post_edit_url_author_client(self):
        response = self.author_client.get(self.EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_guest_client(self):
        response = self.guest_client.get(self.CREATE_URL, follow=True)
        self.assertRedirects(
            response, (f'{self.LOGIN_URL}?next={self.CREATE_URL}'))

    def test_unexisting_url_guest_client(self):
        response = self.guest_client.get(self.UNEXISTING)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            self.INDEX_URL: 'posts/index.html',
            self.GROUP_URL: 'posts/group_list.html',
            self.PROFILE_URL: 'posts/profile.html',
            self.DETAIL_POST_URL: 'posts/post_detail.html',
            self.CREATE_URL: 'posts/create_post.html',
            self.EDIT_URL: 'posts/create_post.html',
            self.UNEXISTING: 'core/404.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_add_comment_quest_client(self):
        comment = {
            'text': 'комментарий'
        }
        response = self.guest_client.post(self.ADD_COMMENT_URL,
                                          data=comment, follow=True)
        self.assertRedirects(
            response, (f'{self.LOGIN_URL}?next={self.ADD_COMMENT_URL}')
        )

    def test_add_comment_author_client(self):
        comment = {
            'text': 'комментарий'
        }
        response = self.author_client.post(self.ADD_COMMENT_URL,
                                           data=comment, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
