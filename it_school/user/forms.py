from .models import Users
from django import forms
from django.core.exceptions import ValidationError


class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Введите ваш email'
        }),
        )

    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Введите ваш пароль'
        }),
        )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            email = email.lower().strip()
            cleaned_data['email'] = email
            try:
                user = Users.objects.get(email=email)

                if not user.check_password(password):
                    self.add_error(None, 'Неверный Email или пароль.')

            except Users.DoesNotExist:
                self.add_error(None, 'Неверный Email или пароль.')

        return cleaned_data


class RestorePasswordForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Введите ваш email'
        })
        )

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if email:
            email = email.lower().strip()

        if not Users.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким Email не найден.')

        return email


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Создайте надежный пароль',
        })
    )
    confirmed_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Повторите ваш пароль',
        })
    )

    class Meta:
        model = Users
        fields = ['email', 'password']

        widgets = {
            'email': forms.EmailInput(attrs={
                'placeholder': 'Введите ваш email'
                }),
            'password': forms.PasswordInput(attrs={
                'placeholder': 'Введите пароль'
                }),
        }

    def clean(self):
        cleaned_data = super().clean()
        email = self.cleaned_data.get('email')
        password = cleaned_data.get('password')
        confirmed_password = cleaned_data.get('confirmed_password')

        if email:
            email = email.lower().strip()
            cleaned_data['email'] = email

            if Users.objects.filter(email=email).exists():
                self.add_error('email', 'Пользователь с таким Email уже существует.')

        if password:
            if len(password) < 6:
                self.add_error('password', 'Пароль должен содержать минимум 6 символов!')
            elif password.isdigit():
                self.add_error('password', 'Пароль не должен состоять только из цифр!')

        if password and confirmed_password:
            if password != confirmed_password:
                self.add_error('confirmed_password', 'Пароли не совпадают!')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])

        if commit:
            user.save()

        return user


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Введите текущий пароль',
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Создайте новый пароль',
        })
    )
    confirmed_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Повторите новый пароль',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def set_user(self, user):
        self.user = user

    def clean(self):
        cleaned_data = super().clean()

        old_password = self.cleaned_data.get('old_password')
        new_password = self.cleaned_data.get('new_password')
        confirmed_password = self.cleaned_data.get('confirmed_password')

        if not self.user.check_password(old_password):
            self.add_error('old_password', 'Текущий пароль введен неверно!')

        if len(new_password) < 6:
            self.add_error('new_password', 'Пароль должен содержать минимум 6 символов!')

        elif new_password.isdigit():
            self.add_error('new_password', 'Пароль не должен состоять только из цифр!')

        if new_password and confirmed_password and new_password != confirmed_password:
            self.add_error('confirmed_password', 'Новые пароли не совпадают!')

        if old_password and new_password and old_password == new_password:
            self.add_error('confirmed_password', 'Новый пароль должен отличаться от старого!')

        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save()
        return self.user
