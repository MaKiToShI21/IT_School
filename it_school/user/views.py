from .forms import LoginForm, RegistrationForm, RestorePasswordForm, ChangePasswordForm
from django.shortcuts import render, redirect
from .models import Users


def login(request):
    form = LoginForm(request.POST or None)

    if form.is_valid():
        email = form.cleaned_data['email']
        user = Users.objects.get(email=email)
        request.session['id_user'] = user.id
        request.session['id_role'] = user.id_role_id
        request.session['user_email'] = user.email
        request.session['user_role'] = user.id_role.title
        return redirect('homepage:index')

    template_name = 'user/login.html'
    title = 'Авторизация'
    context = {
        'title': title,
        'form': form,
    }

    return render(request, template_name, context)


def logout(request):
    request.session.flush()
    return redirect('user:login')


def registration(request):
    form = RegistrationForm(request.POST or None)

    if form.is_valid():
        user = form.save()
        request.session['user_id'] = user.id
        request.session['user_email'] = user.email
        request.session['id_role'] = user.id_role_id
        return redirect('homepage:index')

    template_name = 'user/registration.html'
    title = 'Регистрация'
    context = {
        'title': title,
        'form': form,
    }

    return render(request, template_name, context)


def restore_password(request):
    form = RestorePasswordForm(request.POST or None)

    if form.is_valid():
        return redirect('user:login')

    template_name = 'user/restore_password.html'
    title = 'Восстановление пароля'
    context = {
        'title': title,
        'form': form,
    }

    return render(request, template_name, context)


def change_password(request):
    if 'id_user' not in request.session:
        return redirect('user:login')
    try:
        user = Users.objects.get(id=request.session['id_user'])
    except Users.DoesNotExist:
        return redirect('user:login')

    form = ChangePasswordForm(request.POST or None)
    form.set_user(user)

    if form.is_valid():
        form.save()
        return redirect('homepage:index')

    template_name = 'user/change_password.html'
    title = 'Смена пароля'
    context = {
        'title': title,
        'form': form,
        }

    return render(request, template_name, context)
