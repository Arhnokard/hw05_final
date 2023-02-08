import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
User = get_user_model()


def get_request(client, url):
    return client.get(url)
    
    
def post_request(client, url, data):
    client.post(url, data=data, follow=True)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.INDEX_URL = '/'
        cls.CREATE_URL = '/create/'
        cls.FOLLOW_INDEX_URL = '/follow/'
        cls.small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='Rin')
        cls.user2 = User.objects.create_user(username='Nikolay')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа №2',
            slug='test-slug-2',
            description='Тестовое описание 2',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.GROUP_URL = f'/group/{self.group.slug}/'
        self.PROFILE_URL = f'/profile/{self.user}/'
        self.DETAIL_POST_URL = f'/posts/{self.post.pk}/'
        self.EDIT_URL = f'/posts/{self.post.pk}/edit/'
        self.ADD_COMMENT_URL = f'/posts/{self.post.pk}/comment/'
        self.PROFILE_FOLLOW_URL = f'/profile/{self.user.username}/follow/'
        self.PROFILE_UNFOLLOW_URL = f'/profile/{self.user.username}/unfollow/'
        self.rin_client = Client()
        self.rin_client.force_login(self.user)
        self.nikolay_client = Client()
        self.nikolay_client.force_login(self.user2)

    def test_views_uses_correct_template(self):
        templates_namespace = {
            self.INDEX_URL: 'posts/index.html',
            self.GROUP_URL: 'posts/group_list.html',
            self.PROFILE_URL: 'posts/profile.html',
            self.DETAIL_POST_URL: 'posts/post_detail.html',
            self.CREATE_URL: 'posts/create_post.html',
            self.EDIT_URL: 'posts/create_post.html'
        }
        for reverse_name, templates in templates_namespace.items():
            with self.subTest(reverse_name=reverse_name):
                response = get_request(self.rin_client, reverse_name)
                self.assertTemplateUsed(response, templates)

    def helper_context(self, page_obj):
        self.assertEqual(page_obj.text, self.post.text)
        self.assertEqual(page_obj.group.title, self.group.title)
        self.assertEqual(page_obj.group.slug, self.group.slug)
        self.assertEqual(page_obj.group.description, self.group.description)
        self.assertEqual(page_obj.author, self.post.author)
        self.assertEqual(page_obj.image.name, self.post.image )

    def helper_form_context(self, response):
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)

    def test_correct_context(self):
        adres_url = (self.INDEX_URL, self.GROUP_URL, self.PROFILE_URL,)
        for url in adres_url:
            response = get_request(self.rin_client, url)
            self.helper_context(response.context['page_obj'][0])

    def test_correct_form_context(self):
        adres_url = (self.CREATE_URL, self.EDIT_URL)
        for url in adres_url:
            response = get_request(self.rin_client, url)
            self.helper_form_context(response)

    def test_post_detail_correct_context(self):
        response = get_request(self.rin_client, self.DETAIL_POST_URL)
        post = response.context['post']
        self.assertEqual(post.pk, self.post.pk)
        self.helper_context(post)

    def test_new_post(self):
        all_post_count = Post.objects.count()
        group_count = self.post.group.posts.count()
        group2_count = self.group2.posts.count()
        author_post_count = self.post.author.posts.count()
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        new_post = {
            'text': 'Новый пост',
            'group': self.group2.pk,
            'image': uploaded
        }
        post_request(self.rin_client, self.CREATE_URL, new_post)
        self.assertEqual(Post.objects.count(), all_post_count + 1)
        self.assertEqual(self.post.group.posts.count(), group_count)
        self.assertEqual(self.post.author.posts.count(),
                         author_post_count + 1)
        self.assertEqual(self.group2.posts.count(), group2_count + 1)

    def test_add_comment(self):
        comment = {
            'text': 'комментарий'
        }
        post_request(self.rin_client, self.ADD_COMMENT_URL,comment)
        response = get_request(self.rin_client, self.DETAIL_POST_URL)
        self.assertEqual(
            response.context['comments'][0].text, comment['text']
        )

    def test_profile_follow_unfollow(self):
        start_follower = Follow.objects.count()
        get_request(self.nikolay_client, self.PROFILE_FOLLOW_URL)
        self.assertNotEqual(start_follower, Follow.objects.count())
        get_request(self.nikolay_client, self.PROFILE_UNFOLLOW_URL)
        self.assertEqual(start_follower, Follow.objects.count())

    def test_follow_index(self):
        response = get_request(self.nikolay_client, self.FOLLOW_INDEX_URL)
        count_follow_posts = len(response.context['page_obj'])
        cache.clear()
        get_request(self.nikolay_client, self.PROFILE_FOLLOW_URL)
        response = get_request(self.nikolay_client, self.FOLLOW_INDEX_URL)
        self.assertNotEqual(count_follow_posts,
                            len(response.context['page_obj']))
        cache.clear()
        response = get_request(self.rin_client, self.FOLLOW_INDEX_URL)
        self.assertEqual(count_follow_posts,
                         len(response.context['page_obj']))


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.INDEX_REVERSE = reverse('posts:index')
        cls.user = User.objects.create_user(username='Platon')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug2',
            description='Тестовое описание',
        )
        post_list = []
        for _ in range(13):
            post_list.append(Post(text='Тестовый пост',
                                  author=cls.user, group=cls.group))
        cls.posts = Post.objects.bulk_create(post_list)

    def setUp(self):
        self.GROUP_REVERSE = reverse('posts:group_posts',
                                     kwargs={'slug': self.group.slug})
        self.PROFILE_REVERSE = reverse(
            'posts:profile', kwargs={'username': self.user})
        self.platon_client = Client()
        self.platon_client.force_login(self.user)

    def test_paginator_contains_correct_page(self):
        number_last_page = Post.objects.count() // settings.POSTS_PER_PAGE
        if (Post.objects.count() % settings.POSTS_PER_PAGE) > 0:
            number_last_page += 1
        addres = {
            self.INDEX_REVERSE,
            self.GROUP_REVERSE,
            self.PROFILE_REVERSE
        }
        for url in addres:
            with self.subTest(url=url):
                response = get_request(self.platon_client, url)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_PER_PAGE)
                response = get_request(self.platon_client,
                                       url + f'?page={number_last_page}')
                self.assertEqual(len(response.context['page_obj']),
                                 Post.objects.count() %
                                 settings.POSTS_PER_PAGE)


class TestCache(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.INDEX_REVERSE = reverse('posts:index')
        cls.user = User.objects.create_user(username='Piton')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug2',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.piton_client = Client()
        self.piton_client.force_login(self.user)

    def test_cache(self):
        content_before = get_request(self.piton_client,
                                     self.INDEX_REVERSE).content
        self.post.delete()
        content_after = get_request(self.piton_client,
                                    self.INDEX_REVERSE).content
        self.assertEqual(content_before, content_after)
