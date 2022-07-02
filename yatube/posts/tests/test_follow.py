from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Post, User


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth_2')
        cls.author_1 = User.objects.create_user(username='author_1')
        cls.author_2 = User.objects.create_user(username='author_2')
        cls.post = Post.objects.create(
            author=cls.author_1,
            text='Пост - 1'
        )
        # создаем подписку
        Follow.objects.get_or_create(user=cls.user, author=cls.author_1)

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    def test_follow_auth_user_context(self):
        # посмотрим на кого мы подписаны
        response = self.authorized_client.get(reverse(
            'posts:follow_index')
        )
        response = response.context['foll_list'].all().first()
        all = Post.objects.all().first()
        self.assertEqual(response.text, all.text)
        self.assertEqual(response.author, all.author)

    def test_unfollow_auth_user_context(self):
        # тест отписки
        # посмотрим на кого мы подписаны
        response = self.authorized_client.get(reverse(
            'posts:follow_index')
        )
        response = response.context['foll_list'].all().first()
        all = Post.objects.all().first()
        self.assertEqual(response.text, all.text)
        self.assertEqual(response.author, all.author)
        # отпишемся
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.author_1})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=self.author_1
            ).exists()
        )

    def test_follow_new_user(self):
        self.user_3 = User.objects.create_user(username='auth_3')
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(self.user_3)
        Follow.objects.get_or_create(user=self.user_3, author=self.author_2)
        self.post = Post.objects.create(
            author=self.author_2,
            text='Пост - 2'
        )
        print(f'---1---{self.post.text}')
        response = self.authorized_client_3.get(reverse(
            'posts:follow_index')
        )
        response = response.context['page_obj'][0]
        self.assertEqual(response.text, self.post.text)

    def test_follow_new_user_null(self):
        self.user_3 = User.objects.create_user(username='auth_3')
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(self.user_3)
        self.post = Post.objects.create(
            author=self.author_2,
            text='Пост - 2'
        )
        print(f'---1---{self.post.text}')
        response = self.authorized_client_3.get(reverse(
            'posts:follow_index')
        )
        response = response.context['foll_list'].all().count()
        print(f'---3---{response}')
        self.assertEqual(response, 0)

    def test_follow_subscription(self):
        # проверка что увеличивается кол-во подписок
        follow_count = Follow.objects.count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author_2})
        )
        self.assertEqual(Follow.objects.all().count(), follow_count + 1)
        object_one = Follow.objects.all().last()
        self.assertEqual(object_one.user, self.user)
        self.assertEqual(object_one.author, self.author_2)

    def test_unfollow_orm(self):
        # проверка кол-ва подписок после отписки
        Follow.objects.get_or_create(user=self.user_2, author=self.author_2)
        follow_count = Follow.objects.count()
        object_one = Follow.objects.all().last()
        self.assertEqual(object_one.user, self.user_2)
        self.assertEqual(object_one.author, self.author_2)
        self.authorized_client_2.get(
            reverse('posts:profile_unfollow', kwargs={
                'username': self.author_2})
        )
        self.assertEqual(Follow.objects.all().count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_2,
                author=self.author_2
            ).exists()
        )
