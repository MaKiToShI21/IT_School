from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from core.models import *


class Users(models.Model):
    email = models.EmailField('Почта', max_length=150, unique=True)
    password = models.CharField('Пароль')
    created_at = models.DateField('Дата регистрации', auto_now_add=True)

    id_role = models.ForeignKey(
        Roles,
        verbose_name='Роль',
        db_column='id_role',
        default=2,
        on_delete=models.PROTECT,
    )

    def __str__(self):
        return self.email

    def set_password(self, password):
        self.password = make_password(password)

    def check_password(self, password):
        return check_password(password, self.password)

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
