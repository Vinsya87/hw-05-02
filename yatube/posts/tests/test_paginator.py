import math

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.posts = []
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='one',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа2',
            slug='two',
            description='Тестовое описание2',
        )

        for i in range(0, 25):
            cls.posts.append(Post(
                author=cls.user,
                text='Текст',
                group=cls.group
            ))
        Post.objects.bulk_create(cls.posts)
        cls.post_final = Post.objects.create(
            author=cls.user,
            text='Пост для 3 задания',
            group=cls.group_2
        )
        cls.posts_count = Post.objects.count()
        # всего постов в группе group
        cls.posts_count_group = cls.group.posts.count()
        # смотрим колво стр в пагинаторе
        cls.amount_page = math.ceil(cls.posts_count / settings.PER_PAGE)
        # колво постов на последней стр
        cls.residual = cls.posts_count % settings.PER_PAGE
        # колво постов на последней стр group
        cls.residual_group = cls.posts_count_group % settings.PER_PAGE

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_index(self):
        """5. проверка списка постов в пагинаторе."""

        templates_page = [
            reverse('posts:index'),
            reverse('posts:profile', kwargs={'username': self.user})
        ]
        for reverse_name in templates_page:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                len(response.context['page_obj'])
                self.assertEqual(len(
                    response.context['page_obj']), settings.PER_PAGE)
                response = self.authorized_client.get(
                    (reverse_name) + f'?page={self.amount_page}')
                self.assertEqual(len(
                    response.context['page_obj']), self.residual)

    def test_first_page_contains_ten_group_posts(self):
        """6. проверка списка постов в пагинаторе group_posts."""
        response = self.client.get(reverse(
            'posts:group_posts', kwargs={'slug': self.group.slug})
        )
        # Проверка: количество постов на первой странице.
        self.assertEqual(len(response.context['page_obj']), settings.PER_PAGE)
        response = self.client.get(reverse(
            'posts:group_posts', kwargs={
                'slug': self.group.slug}) + f'?page={self.amount_page}'
        )
        # тест: количество постов на послед. странице group.
        self.assertEqual(len(
            response.context['page_obj']), self.residual_group)

    def test_posts_uses_correct_context_first_page(self):
        """8-1.Проверка, шаблонов, что передается корректный context"""
        templates_page = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group_2.slug}),
            reverse('posts:profile', kwargs={'username': self.user})
        ]
        for reverse_name in templates_page:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context['page_obj'][0].text, self.post_final.text)

    def test_posts_group_list_uses_correct_context_first_page(self):
        """9. Проверка, шаблон(group_list) пост не попал post_final."""
        response = self.guest_client.get(
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}))
        self.assertNotEqual(
            response.context['page_obj'][0].text, self.post_final.text)
