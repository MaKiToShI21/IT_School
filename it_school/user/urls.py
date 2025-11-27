from django.urls import path

from . import views

app_name = 'user'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('registration/', views.registration, name='registration'),
    path('restore_password/', views.restore_password, name='restore_password'),
    path('change_password/', views.change_password, name='change_password'),
]
