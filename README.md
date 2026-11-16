# Меридиан · Турагентство · Вариант 8

Практические работы 7–9. Елеков Олег Андреевич, группа ИСдо-44.

Django-проект на моделях работы 5 и макетах туристического журнала работы 6.

## Запуск

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 127.0.0.1:8008 --insecure
```

На Windows окружение активируется командой `.venv\Scripts\activate`.

База, пользовательские изображения, .env и виртуальное окружение исключены из Git. Демонстрационные данные создаются командой seed_demo.
