from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class CachePagesTests(TestCase):
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
            text='Текст',
            group=cls.group
        )

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_posts_20_sec(self):
        """Проверяем работу cache страница index"""
        # получим контент сначала
        response = self.authorized_client.get(reverse('posts:index'))
        content = response.content
        # Удаляем запись
        self.post.delete()
        # Проверяем, что запись пока видно на странице
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response.content, content)
        # Очистка кэша
        cache.clear()
        # Проверяем, что удалённую запись НЕ видно на странице
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(response.content, content)
