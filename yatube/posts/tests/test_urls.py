from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='one',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая группа',
        )
        cls.login_url = reverse('login')
        cls.create_url = reverse('posts:post_create')
        cls.group_posts_url = reverse(
            'posts:group_posts', kwargs={'slug': cls.group.slug})
        cls.profile_url = reverse(
            'posts:profile', kwargs={'username': cls.user})
        cls.post_detail_url = reverse('posts:post_detail', kwargs={
            'post_id': f'{int(cls.post.id)}'})
        cls.edit_url = reverse('posts:post_edit', kwargs={
            'post_id': f'{int(cls.post.id)}'})

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованый клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_static(self):
        """Проверяем статичные страницы."""
        # Отправляем запрос через client,
        # созданный в setUp()
        templates_url_names = [
            '/',
            '/about/author/',
            '/about/tech/'
        ]
        for url in templates_url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'{self.group_posts_url}',
            'posts/profile.html': f'{self.profile_url}',
            'posts/post_detail.html': f'{self.post_detail_url}',
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    # Проверяем доступность страниц для автора поста
    def test_page_authorized_client(self):
        """доступность страниц для авторизованного пользователя v2."""
        response = self.authorized_client.get(
            f'{self.edit_url}')
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_page_authorized_client(self):
        """доступность страниц для авторизованного пользователя v2."""
        templates_url_names = {
            'posts/follow.html': '/follow/',
            'posts/create_post.html': f'{self.edit_url}'
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_list_url_unexisting_404(self):
        """проверка стр которой нет тест 404."""
        response = self.authorized_client.get('/nonepage/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_post_list_url_exists_at_desired_lotion(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

        # Проверяем доступность страниц для авторизованного пользователя
        # (сделал для себя)
    def test_post_list_url_exists_at_desired_location(self):
        """доступность страниц для авторизованного пользователя."""
        templates_url_names = {
            'posts/create_post.html': '/create/'
        }
        for template, url in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    # Проверяем редиректы для неавторизованного пользователя
    def test_post_list_url_redirect_anonymous_on_admin_login(self):
        """Страница '/create/' перенаправит анонимного пользователя
        на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, f'{self.login_url}?next={self.create_url}')
