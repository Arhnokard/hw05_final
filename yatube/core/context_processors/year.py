import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    date_now = datetime.datetime.now()
    return {
        'year': date_now.year
    }
