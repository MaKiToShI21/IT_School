from django.db import connection
from django.shortcuts import render, redirect
from user.models import Users
from .utils import *
from .forms import *
from django.contrib import messages
from django.http import HttpResponse
import csv


def content(request, paragraph='homepage'):
    id_user = request.session.get('id_user')
    id_role = request.session.get('id_role')

    if not id_user:
        return redirect('user:login')

    search_query = ''
    if 'search' in request.GET:
        search_query = request.GET.get('search', '')

    formatted_search_query = search_query.strip().lower()

    available_tables_with_accesses, unavailable_tables, menu = get_menu(id_role)

    if request.method == 'POST':
        return handle_actions(request, paragraph, available_tables_with_accesses, unavailable_tables)

    has_access = False

    for _, points_array in menu.items():
        for paragraph_key, points in points_array.items():
            for _, accesses in points.items():
                if paragraph_key == paragraph and accesses[0] or paragraph == 'homepage':
                    has_access = True
                    break

    if not has_access:
        return redirect('homepage:index')

    title, table, content, detail_info, form = main_func(request, paragraph, formatted_search_query)

    template_name = 'homepage/index.html'
    context = {
        'title': title,
        'menu': menu,
        'directories': directories,
        'associations': associations,
        'groups': groups,
        'various': various,
        'table': table,
        'paragraph': paragraph,
        'content': content,
        'detail_info': detail_info,
        'form': form,
        'search_query': search_query
    }

    return render(request, template_name, context)


def filter_date(item, field):
    if field == 'lesson_date':
        return item.russian_date(getattr(item, field))
    elif field == 'start_time':
        return item.get_short_time(getattr(item, field))
    elif field == 'end_time':
        return item.get_short_time(getattr(item, field))
    else:
        return getattr(item, field)


def get_select_related_args(foreign_key_fields):
    select_related_args = []
    for fk_field in foreign_key_fields:
        related_model = fk_field.related_model
        nested_fk_fields = [f for f in related_model._meta.fields if isinstance(f, models.ForeignKey)]
        if nested_fk_fields:
            for nested_fk in nested_fk_fields:
                select_related_args.append(f"{fk_field.name}__{nested_fk.name}")
        else:
            select_related_args.append(fk_field.name)

    return select_related_args


def get_menu(id_role):
    menu = {}

    accesses = Accesses.objects.select_related('id_menu', 'id_role').filter(id_role=id_role)
    available_tables = []
    available_tables_with_accesses = {}
    all_tables = ['users', 'accesses', 'menu', 'roles']
    for rus_point, menu_dict in dict.items():
        tmp_dict = {}
        for key, value in menu_dict.items():
            for access in accesses:
                role_accesses = {}
                if not isinstance(value, str):
                    if str(value._meta.verbose_name_plural) == str(access.id_menu):
                        accesses_array = [
                            access.read_info,
                            access.write_info,
                            access.edit_info,
                            access.delete_info
                            ]
                        role_accesses[access.id_menu] = accesses_array
                        tmp_dict[key] = role_accesses
                        available_tables.append(value._meta.db_table)
                        available_tables_with_accesses[value._meta.db_table] = accesses_array
                        continue
                    else:
                        all_tables.append(value._meta.db_table)
                else:
                    if value == str(access.id_menu):
                        role_accesses[access.id_menu] = [
                            access.read_info,
                            access.write_info,
                            access.edit_info,
                            access.delete_info
                            ]
                        tmp_dict[key] = role_accesses
                        # available_tables.append(value._meta.db_table)
                        continue
        menu[rus_point] = tmp_dict
    unavailable_tables = list(set(all_tables) - set(available_tables))

    return available_tables_with_accesses, unavailable_tables, menu


def main_func(request, paragraph, search_query):
    detail_info = {}
    content = ''
    table = False
    form = None

    if paragraph == 'homepage':
        title = 'Главная страница'
        content = 'Добро пожаловать в IT-School'
    elif paragraph in various or paragraph in reference:
        if paragraph == 'settings':
            title = various[paragraph]
        elif paragraph == 'admin_zone':
            table = True
            title = various[paragraph]
            content, detail_info = get_detail_info(Users, search_query)
            email = request.session.get('user_email')
            content = content.exclude(email=email)
        elif paragraph == 'documents':
            title = various[paragraph]
            last_sql_request = request.session.get('last_sql_request', '')
            form = DocumentsForm(initial={'sql_request': last_sql_request})
        elif paragraph == 'content':
            table = True
            title = reference[paragraph]
            detail_info = directory_info
        elif paragraph == 'about':
            title = reference[paragraph]
            content = '''IT-School – это комплексная информационная система для управления образовательным проектом,
            организуемым на базе ВУЗа для школьников. Система предназначена для автоматизации процессов организации
            интенсивного обучения по современным IT-направлениям.'''
    else:
        table = True
        model = get_model(paragraph)
        if model:
            title = model._meta.verbose_name_plural
            content, detail_info = get_detail_info(model, search_query)

    return title, table, content, detail_info, form


def get_detail_info(model, search_query):
    detail_info = {}
    model_fields = [f for f in model._meta.fields if not f.auto_created and not str(f.name) == 'password']
    foreign_key_fields = [f for f in model._meta.get_fields() if isinstance(f, models.ForeignKey)]
    select_related_args = get_select_related_args(foreign_key_fields)
    content = model.objects.select_related(*select_related_args)

    related_used_objects = {}
    for item in content:
        if search_query:
            if search_query not in str(item).lower():
                content = content.exclude(id=item.id)
                continue
        temp = {}
        i = 0
        if isinstance(model_fields[0], models.ForeignKey):
            i = 1

        for field in model_fields[i:]:
            if isinstance(field, models.ForeignKey):
                related_obj = getattr(item, field.name)
                temp_model = field.related_model
                if not temp_model in related_used_objects.keys():
                    temp_model_fields = [f for f in temp_model._meta.fields if not f.auto_created]
                    related_used_objects[temp_model] = temp_model_fields
                else:
                    temp_model_fields = related_used_objects[temp_model]
                for temp_model_field in temp_model_fields:
                    verbose_name = temp_model._meta.get_field(temp_model_field.name).verbose_name
                    temp_field_value = getattr(related_obj, temp_model_field.name)
                    if not str(temp_field_value) in item.__str__():
                        temp[verbose_name] = temp_field_value
            elif not field.auto_created:
                verbose_name = item._meta.get_field(field.name).verbose_name
                field_value = filter_date(item, field.name)

                if not str(field_value) in item.__str__() and field_value:
                    temp[verbose_name] = field_value
        detail_info[item.id] = temp
    print(detail_info)
    return content, detail_info


def handle_actions(request, paragraph, available_tables_with_accesses, unavailable_tables):
    action = request.POST.get('action')
    selected_item_id = request.POST.get('selected_item_id')
    model = get_model(paragraph)

    if not model:
        return redirect('homepage:content')

    if action == 'add':
        return redirect('homepage:add_item', paragraph)
    elif action == 'edit':
        if not selected_item_id:
            messages.warning(request, 'Выберите запись для изменения')
            return redirect('homepage:content', paragraph)
        return redirect('homepage:edit_item', paragraph=paragraph, item_id=selected_item_id)
    elif action == 'delete':
        if not selected_item_id:
            messages.warning(request, 'Выберите запись для удаления')
            return redirect('homepage:content', paragraph)
        item = model.objects.get(id=selected_item_id)
        item.delete()
        messages.success(request, 'Успешное удаление записи')
    elif action in ['execute', 'export']:
        sql_request = request.POST.get('sql_request', '')
        request.session['last_sql_request'] = sql_request
        form = DocumentsForm(request.POST)
        if form.is_valid():
            if action == 'execute':
                return execute_sql_request(request, sql_request, available_tables_with_accesses, unavailable_tables)
            elif action == 'export':
                return export_request_data(request)
        else:
            for _, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')

    return redirect('homepage:content', paragraph)


def add_item(request, paragraph):
    user_id = request.session.get('user_id')
    id_role = request.session.get('id_role')

    if not user_id:
        return redirect('user:login')

    _, _, menu = get_menu(id_role)
    model = get_model(paragraph)

    if not model:
        return redirect('homepage:content')

    title = model._meta.verbose_name

    if request.method == 'POST':
        created_form = create_form(model, data=request.POST)
        if created_form.is_valid():
            messages.success(request, f'Успешное добавление новой записи!')
            created_form.save()
            return redirect('homepage:content', paragraph)
    else:
        created_form = create_form(model)

    template_name = 'homepage/index.html'
    context = {
        'title': f'Добавление {title}',
        'menu': menu,
        'paragraph': paragraph,
        'created_form': created_form,
        'table': False,
    }
    return render(request, template_name, context)


def edit_item(request, paragraph, item_id):
    user_id = request.session.get('user_id')
    id_role = request.session.get('id_role')

    if not user_id:
        return redirect('user:login')

    _, _, menu = get_menu(id_role)
    if paragraph == 'admin_zone':
        model = Users
    else:
        model = get_model(paragraph)

    if not model:
        return redirect('homepage:content')

    title = model._meta.verbose_name

    item = model.objects.get(id=item_id)
    if request.method == 'POST':
        created_form = create_form(model, item, request.POST)
        if created_form.has_changed():
            if created_form.is_valid():
                created_form.save()
                messages.success(request, f'Успешное изменение записи "{item}"!')
                return redirect('homepage:content', paragraph)
        else:
            messages.info(request, 'Изменений не обнаружено')
            return redirect('homepage:content', paragraph)
    else:
        created_form = create_form(model, item)

    template_name = 'homepage/index.html'
    context = {
        'title': f'Изменение {title}',
        'menu': menu,
        'paragraph': paragraph,
        'created_form': created_form,
    }

    return render(request, template_name, context)


def execute_sql_request(request, sql_request, available_tables_with_accesses, unavailable_tables):
    if 'sql_results' in request.session:
        del request.session['sql_results']
    with connection.cursor() as cursor:
        for table in unavailable_tables:
            if table in sql_request:
                messages.error(request, f'У вас нет прав доступа к таблице: {table}')
                return redirect('homepage:content', paragraph='documents')
        sql_upper = sql_request.upper().strip()
        splitted_sql_request = sql_upper.split(';')

        for sql_request in splitted_sql_request:
            stripped_request = sql_request.strip()
            if not stripped_request:
                continue
            splitted_request = sql_request.split()

            if splitted_request[0] == 'SELECT':
                try:
                    cursor.execute(sql_request)
                    results = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]

                    serializable_data = []
                    for row in results:
                        serializable_row = []
                        for cell in row:
                            if cell is None:
                                serializable_row.append(None)
                            else:
                                serializable_row.append(str(cell))
                        serializable_data.append(serializable_row)

                    request.session['sql_results'] = {
                        'columns': columns,
                        'data': serializable_data
                        }
                except Exception as e:
                    messages.error(request, f'Ошибка SQL: {str(e).split('ОШИБКА:')[-1].split('\n')[0].strip()}')
            elif splitted_request[0] == 'UPDATE':
                table_name = get_table_name(splitted_request, 'UPDATE').lower()
                table_accesses = available_tables_with_accesses.get(table_name)
                if table_accesses:
                    if (table_accesses[1]):
                        try:
                            cursor.execute(sql_request)
                            messages.success(request, f'Изменено {cursor.rowcount} записей в таблице {table_name}')
                        except Exception as e:
                            messages.error(request, f'Ошибка SQL: {str(e).split('ОШИБКА:')[-1].split('\n')[0].strip()}')
                    else:
                        messages.error(request, f'Не достаточно прав, чтобы изменять таблицу: {table_name}')
                else:
                    messages.error(request, 'Таблица не найдена')

            elif splitted_request[0] == 'INSERT':
                if 'INTO' in sql_request:
                    table_name = get_table_name(splitted_request, 'INTO').lower()
                else:
                    table_name = get_table_name(splitted_request, 'INSERT').lower()
                table_accesses = available_tables_with_accesses.get(table_name)
                if table_accesses:
                    if table_accesses[2]:
                        try:
                            cursor.execute(sql_request)
                            messages.success(request, f'Добавлено {cursor.rowcount} записей в таблицу {table_name}')
                        except Exception as e:
                            messages.error(request, f'Ошибка SQL: {str(e).split('ОШИБКА:')[-1].split('\n')[0].strip()}')
                    else:
                        messages.error(request, f'Не достаточно прав, чтобы добавлять данные в таблицу: {table_name}')
                else:
                    messages.error(request, 'Таблица не найдена')
            elif splitted_request[0] == 'DELETE':
                table_name = get_table_name(splitted_request, 'FROM').lower()
                table_accesses = available_tables_with_accesses.get(table_name)
                if table_accesses:
                    if table_accesses[3]:
                        try:
                            cursor.execute(sql_request)
                            messages.success(request, f'Удалено {cursor.rowcount} записей из таблицы {table_name}')
                            print(f'Удалено {cursor.rowcount} записей из таблицы {table_name}')
                        except Exception as e:
                            messages.error(request, f'Ошибка SQL: {str(e).split('ОШИБКА:')[-1].split('\n')[0].strip()}')
                    else:
                        messages.error(request, f'Не достаточно прав, чтобы удалять данные из таблицы: {table_name}')
                else:
                    messages.error(request, 'Таблица не найдена')
            else:
                messages.error(request, 'Неверный SQL запрос')

    return redirect('homepage:content', paragraph='documents')


def export_request_data(request):
    sql_results = request.session.get('sql_results')

    if not sql_results:
        messages.error(request, 'Нет данных для экспорта')
        return redirect('homepage:content', paragraph='documents')

    columns = sql_results.get('columns', [])
    data = sql_results.get('data', [])

    response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    writer = csv.writer(response, delimiter=';')

    writer.writerow(columns)

    for row in data:
        writer.writerow(row)

    return response


def get_table_name(request, request_sign):
    print(request, request_sign)
    for i in range(len(request)):
        if request[i] == request_sign:
            return request[i+1]
    return ''
