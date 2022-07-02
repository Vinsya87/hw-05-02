import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Тестовый комент'
        )
        cls.login_url = reverse('login')
        cls.edit_url = reverse('posts:post_edit', kwargs={
            'post_id': f'{int(cls.post.id)}'})
        cls.create_url = reverse('posts:post_create')
        cls.comment_url = reverse('posts:add_comment', kwargs={
            'post_id': f'{int(cls.post.id)}'}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с прекрасными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество коментов в post
        comment_count = Comment.objects.count()
        # Подготавливаем данные для передачи в форму
        form_data = {
            'text': 'Тестовый комент 2'
        }
        # Отправили POST запрос
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': f'{int(self.post.id)}'}),
            data=form_data,
            follow=True
        )
        # Проверили редирект
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': f'{int(self.post.id)}'}))
        last_comment = Comment.objects.all().last()
        # Проверяем, увеличилось ли число коментов
        self.assertEqual(Comment.objects.count(), comment_count + 1)

        self.assertEqual(form_data['text'], last_comment.text)
        # Проверяем, что создался комент с нашим текстом
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        self.assertEqual(
            response.context['comments'][1].text, last_comment.text)

    def test_not_create_comment_guest_client(self):
        """Не зареган не создает коммент."""
        # Подсчитаем количество коментов в post
        comment_count = Comment.objects.count()
        # Подготавливаем данные для передачи в форму
        form_data = {
            'text': 'Тестовый комент 2'
        }
        # Отправили POST запрос
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={
                'post_id': f'{int(self.post.id)}'}),
            data=form_data,
            follow=True
        )
        # Проверили редирект
        self.assertRedirects(
            response, f'{self.login_url}?next={self.comment_url}')
        # Проверяем, увеличилось ли число коментов
        self.assertEqual(Comment.objects.count(), comment_count)

    def test_create_post_context_pages_img(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в post
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small-2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        # Подготавливаем данные для передачи в форму
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user}))
        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count + 1)
        last_post = Post.objects.all().first()
        self.assertEqual(form_data['text'], last_post.text)
        self.assertEqual(form_data['group'], self.group.pk)
        # сразу проверка img в создом посте на всех страницах
        templates_page = [
            reverse('posts:index'),
            reverse('posts:group_posts', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user}),
        ]
        for reverse_name in templates_page:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    response.context['page_obj'][0].image, last_post.image)
        # проверка post_detail на наличие img
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={
                'post_id': f'{int(last_post.id)}'}))
        self.assertEqual(
            response.context['posts'].image, last_post.image)
        # Проверяем, что создалась запись с нашим текстом

    def test_post_edit(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Редактирование',
            'group': self.group.pk
        }
        # для себя, выбор какой пост менять
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={
                'post_id': f'{int(self.post.id)}'}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={
                'post_id': f'{int(self.post.id)}'}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(self.post.author, self.user)
        last_post = Post.objects.all().first()
        self.assertEqual(form_data['text'], last_post.text)
        self.assertEqual(self.group, self.group)

        # Проверяем редиректы для неавторизованного пользователя
    def test_post_list_url_redirect_anonymous_post_create(self):
        """при попытке создать пост,
        не создается и будет редирект на логин..
        """
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small2.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, не увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response, f'{self.login_url}?next={self.create_url}')

    def test_post_list_url_redirect_anonymous_post_edit(self):
        """при попытке редактировать пост,
        не создается и будет редирект на логин.."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Редактирование',
            'group': self.group.pk
        }

        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={
                    'post_id': f'{int(self.post.id)}'}),
            data=form_data,
            follow=True
        )
        # Проверяем, не увеличилось ли число постов
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(
            response, f'{self.login_url}?next={self.edit_url}')
