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
        cls.GROUP_URL = '/group/test-slug/'
        cls.PROFILE_URL = '/profile/Rin/'
        cls.DETAIL_POST_URL = '/posts/1/'
        cls.EDIT_URL = '/posts/1/edit/'
        cls.CREATE_URL = '/create/'
        cls.LOGIN_URL = '/auth/login/'
        cls.ADD_COMMENT_URL = f'/posts/1/comment/'
        cls.FOLLOW_INDEX_URL = '/follow/'
        cls.PROFILE_FOLLOW_URL = f'/profile/Rin/follow/'
        cls.PROFILE_UNFOLLOW_URL = f'/profile/Rin/unfollow/'
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
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user)
        self.autorized_client = Client()
        self.autorized_client.force_login(self.user2)

    def test_url_autorized_client(self):
        addres_list = [
            self.INDEX_URL, self.GROUP_URL, self.PROFILE_URL,
            self.DETAIL_POST_URL, self.CREATE_URL, self.FOLLOW_INDEX_URL
        ]
        for addres in addres_list:
            with self.subTest(addres == addres):
                response = self.autorized_client.get(addres)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_autorized_client(self):
        response = self.autorized_client.get(self.EDIT_URL)
        self.assertRedirects(response, self.DETAIL_POST_URL)

    def test_post_edit_url_author_client(self):
        response = self.author_client.get(self.EDIT_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        
    def test_redirect_url_quest_client(self):
        url_list = (
            self.CREATE_URL, self.EDIT_URL, self.ADD_COMMENT_URL,
            self.FOLLOW_INDEX_URL, self.PROFILE_FOLLOW_URL,
            self.PROFILE_UNFOLLOW_URL
        )
        for url in url_list:
            response = self.guest_client.get(url, follow=True)
            self.assertRedirects(
                response, (f'{self.LOGIN_URL}?next={url}'))
        
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
            self.FOLLOW_INDEX_URL: 'posts/follow.html',
            self.UNEXISTING: 'core/404.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
