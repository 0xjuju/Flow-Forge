
from blockchain import views
from django.urls import path

urlpatterns = [
    path("events/", views.process_blockchain_events, name="blockchain_events"),
]




