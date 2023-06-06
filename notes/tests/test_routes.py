from http import HTTPStatus
from django.conf import settings
from pytils.translit import slugify
from django.test import TestCase
from django.urls import reverse

# Импортируем класс комментария.
from notes.models import Note
# Импортируем функцию для определения модели пользователя.
from django.contrib.auth import get_user_model

# Получаем модель пользователя.
User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Создаём двух пользователей с разными именами:
        cls.author = User.objects.create(username='Создатель')
        cls.reader = User.objects.create(username='Читатель')
        # # От имени одного пользователя создаём замекту:
        cls.note = Note.objects.create(
            title='Название заголовка',
            text='Пишу текст',
            slug='Svoi',
            author=cls.author)
        # cls.note = Comment.objects.create(
        #     news=cls.news,
        #     author=cls.author,
        #     text='Текст комментария'
        # ) 

#### Тест доступности страниц#####################################
    def test_pages_availability(self):
        # Создаём набор тестовых данных - кортеж кортежей.
        # Каждый вложенный кортеж содержит два элемента:
        # имя пути и позиционные аргументы для функции reverse().
        urls = (
            # Путь для главной страницы не принимает
            # никаких позиционных аргументов, 
            # поэтому вторым параметром ставим None.
            ('notes:home', None),
            # Путь для страницы заметки
            # принимает в качестве позиционного аргумента
            # slug записи; передаём его в кортеже.
            # Имена, по которым доступны нужные страницы, берём в головном файле yanews/urls.py.
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        # Итерируемся по внешнему кортежу 
        # и распаковываем содержимое вложенных кортежей:
        for name, args in urls:
            with self.subTest(name=name):
                # Передаём имя и позиционный аргумент в reverse()
                # и получаем адрес страницы для GET-запроса:
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    # Тест, что только автор может удалить/отредактировать/увидеть свою заметку           
    def test_availability_for_edit_and_delete(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            for name in ('notes:edit', 'notes:delete', 'notes:detail'):  
                with self.subTest(user=user, name=name):        
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

#######тестирование редиректа###################################
    def test_redirect_for_anonymous_client(self):
        # Сохраняем адрес страницы логина:
        login_url = reverse('users:login')
        # В цикле перебираем имена страниц, с которых ожидаем редирект:
        for name in ('notes:edit', 'notes:delete', 'notes:detail','notes:list'):
            with self.subTest(name=name):
                # Получаем адрес страницы редактирования или удаления комментария:
                if name != 'notes:list':
                    url = reverse(name, args=(self.note.slug,))
                # Получаем ожидаемый адрес страницы логина, 
                # на который будет перенаправлен пользователь.
                # Учитываем, что в адресе будет параметр next, в котором передаётся
                # адрес страницы, с которой пользователь был переадресован.
                else:
                    url = reverse(name)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                # Проверяем, что редирект приведёт именно на указанную ссылку.
                self.assertRedirects(response, redirect_url) 

    # Тест, что только автор может увидеть список всех своих заметок          
    def test_availability_for_list(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.OK),
        )
        for user, status in users_statuses:
            # Логиним пользователя в клиенте:
            self.client.force_login(user)
            # Для каждой пары "пользователь - ожидаемый ответ"
            # перебираем имена тестируемых страниц:
            # for name in ('notes:edit', 'notes:delete', 'notes:detail'):  
            with self.subTest(user=user):        
                url = reverse('notes:list')
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)        
        

            
