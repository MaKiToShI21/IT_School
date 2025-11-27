from django.urls import path

from . import views

app_name = 'homepage'

urlpatterns = [
    path('', views.content, name='index'),
    path('<str:paragraph>/', views.content, name='content'),
    path('<str:paragraph>/add/', views.add_item, name='add_item'),
    path('<str:paragraph>/edit/<int:item_id>', views.edit_item, name='edit_item'),
]
