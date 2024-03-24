from django.urls import path

from . import views

app_name= "encyclopedia"
urlpatterns = [
    path("", views.index, name="index"),
    path("wiki/<str:title>/", views.dynamic_wiki, name="wiki"),
    path("add/", views.add, name="add"),
    path("random/", views.random_wiki, name="random"),
    path("wiki/<str:title>/edit", views.edit, name="edit"),
]
