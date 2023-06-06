from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

# Импортируем из файла с формами список стоп-слов и предупреждение формы.
# Загляните в news/forms.py, разберитесь с их назначением.
from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    # Текст  понадобится в нескольких местах кода, 
    # поэтому запишем его в атрибуты класса
    NOTE_TEXT = 'Text note created'
    NOTE_TITLE = 'Заголовок создания'

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователя и клиент, логинимся в клиенте.
        cls.author = User.objects.create(username='Создатель')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)
        # Адрес страницы .
        cls.url = reverse('notes:add')
        # Данные для POST-запроса при создании заметки.
        cls.form_data = {
            'text': cls.NOTE_TEXT,
            'title': cls.NOTE_TITLE}

    def test_anonymous_user_cant_create_note(self):
        # Совершаем запрос от анонимного клиента, в POST-запросе отправляем
        # предварительно подготовленные данные формы с текстом.     
        self.client.post(self.url, data=self.form_data)
        # Считаем количество Note.
        note_count = Note.objects.count()
        # Ожидаем, что читатель ни создал ни одного поста.
        self.assertEqual(note_count, 0)

    def test_user_can_create_note(self):
        # Совершаем запрос через авторизованный клиент.
        self.auth_client.post(self.url, data=self.form_data)
        # Считаем количество постов.
        note_count = Note.objects.count()
        # Убеждаемся, что заметка создалась.
        self.assertEqual(note_count, 1)
        # Получаем объект заметки из базы.
        note = Note.objects.get()
        # Проверяем, что все атрибуты  совпадают с ожидаемыми.
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.author, self.author)

#     def test_user_cant_use_bad_words(self):
#         # Формируем данные для отправки формы; текст включает
#         # первое слово из списка стоп-слов.
#         bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
#         # Отправляем запрос через авторизованный клиент.
#         response = self.auth_client.post(self.url, data=bad_words_data)
#         # Проверяем, есть ли в ответе ошибка формы.
#         self.assertFormError(
#             response,
#             form='form',
#             field='text',
#             errors=WARNING
#         )
#         # Дополнительно убедимся, что комментарий не был создан.
#         comments_count = Comment.objects.count()
#         self.assertEqual(comments_count, 0)

##  В отдельном классе проверяем удаление/редактирование ##################################
class TestNoteEditDelete(TestCase):
    # Тексты не нужно дополнительно создавать 
    NOTE_TEXT = 'Текст исходный'
    NEW_NOTE_TEXT = 'Обновлённый текст'

    @classmethod
    def setUpTestData(cls):
        # Создаём пользователей и клиент, логинимся в клиенте.
        cls.author = User.objects.create(username='Создатель')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader = User.objects.create(username='Еще один')
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)
        # Создаём заметку.
        cls.note = Note.objects.create(
            title='Заголовок',
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug='kukushka')
        # Сохраняем slug заметки во временную переменную
        note_slug = cls.note.slug
        # Формируем адреса, которые понадобятся для тестов.
        # cls.url = reverse('notes:detail', args=(note_slug,))  # Адрес заметки.
        cls.url_done = reverse('notes:success')  # Адрес успеха
        cls.edit_url = reverse('notes:edit', args=(note_slug,))  # URL для редактирования.
        cls.delete_url = reverse('notes:delete', args=(note_slug,))  # URL для удаления.
        # Формируем данные для POST-запроса по обновлению комментария.
        cls.form_data = {'text': cls.NEW_NOTE_TEXT}

    def test_author_can_delete_note(self):
        # От имени автора комментария отправляем DELETE-запрос на удаление.
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл к разделу успеха.
        # Заодно проверим статус-коды ответов.
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, self.url_done)       
        # Считаем количество заметок в системе.
        note_count = Note.objects.count()
        # Ожидаем ноль  в системе.
        self.assertEqual(note_count, 0) 

    def test_user_cant_delete_note_of_another_user(self):
        # Выполняем запрос на удаление от пользователя-читателя.
        response = self.reader_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что комментарий по-прежнему на месте.
        note_count = Note.objects.count()
        self.assertEqual(note_count, 1) 

    def test_author_can_edit_note(self):
        # Выполняем запрос на редактирование от имени автора комментария.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        # # Проверяем, что сработал редирект.
        print(response.status_code)
        self.assertRedirects(response, self.url_done)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        print(self.note.text)
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        # Выполняем запрос на редактирование от имени другого пользователя.
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Обновляем объект комментария.
        self.note.refresh_from_db()
        # Проверяем, что текст остался тем же, что и был.
        self.assertEqual(self.note.text, self.NOTE_TEXT)