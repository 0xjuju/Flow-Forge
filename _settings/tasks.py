from celery import shared_task


# For tests
@shared_task
def add(x, y):
    return x + y



