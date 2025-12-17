from django.db import connection
from django.shortcuts import render, redirect
from user.models import Users
from .utils import *
from .forms import *
from django.contrib import messages
from django.http import HttpResponse
import csv
import plotly.graph_objects as go


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

    title, table, content, detail_info, form, dashboard = main_func(request, paragraph, formatted_search_query)

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
        'search_query': search_query,
        'dashboard': dashboard,
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
    for rus_point, menu_dict in dictionary.items():
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
                        continue
        menu[rus_point] = tmp_dict
    unavailable_tables = list(set(all_tables) - set(available_tables))
    return available_tables_with_accesses, unavailable_tables, menu


def main_func(request, paragraph, search_query):
    detail_info = {}
    content = ''
    table = False
    form = None
    dashboard = None

    if paragraph == 'homepage':
        title = 'Главная страница'
        content = 'Добро пожаловать в IT-School'
    elif paragraph in various:
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
    elif paragraph in reference:
        if paragraph == 'content':
            table = True
            title = reference[paragraph]
            detail_info = directory_info
        elif paragraph == 'about':
            title = reference[paragraph]
            content = '''IT-School – это комплексная информационная система для управления образовательным проектом,
            организуемым на базе ВУЗа для школьников. Система предназначена для автоматизации процессов организации
            интенсивного обучения по современным IT-направлениям.'''
    elif paragraph in analytics:
        if paragraph == 'action_diagram':
            pass
        #     return action_diagram(request, paragraph)
        elif paragraph == 'dashboard':
            title = analytics[paragraph]
            return make_dashboard(request, title)
    else:
        table = True
        model = get_model(paragraph)
        if model:
            title = model._meta.verbose_name_plural
            content, detail_info = get_detail_info(model, search_query)

    return title, table, content, detail_info, form, dashboard


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
                    temp_field_value = getattr(related_obj, temp_model_field.name, None)
                    if not str(temp_field_value) in item.__str__():
                        temp[verbose_name] = temp_field_value
            elif not field.auto_created:
                verbose_name = item._meta.get_field(field.name).verbose_name
                field_value = filter_date(item, field.name)

                if not str(field_value) in item.__str__() and field_value:
                    temp[verbose_name] = field_value
        detail_info[item.id] = temp
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
        Action_Logging.objects.create(
            action='delete',
            table_name=paragraph,
        )
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
    id_user = request.session.get('id_user')
    id_role = request.session.get('id_role')

    if not id_user:
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
            Action_Logging.objects.create(
                action='add',
                table_name=paragraph,
            )
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
    id_user = request.session.get('id_user')
    id_role = request.session.get('id_role')

    if not id_user:
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
                Action_Logging.objects.create(
                    action='update',
                    table_name=paragraph,
                )
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
    for i in range(len(request)):
        if request[i] == request_sign:
            return request[i+1]
    return ''


def create_action_chart(request, queryset):
    db_data = queryset

    if not db_data.exists():
        messages.info(request, 'Данные для диаграммы "Журнал действий" отсутствуют!')

    dates = [value.datetime.date() for value in db_data]
    sorted_dates = sorted(set(dates))

    data_for_chart = {}
    data_for_chart['date'] = sorted_dates

    added = []
    updated = []
    deleted = []
    for date in sorted_dates:
        added_count = 0
        updated_count = 0
        deleted_count = 0

        for value in db_data:
            date_from_value = value.datetime.date()
            if date_from_value == date:
                if value.action == 'add':
                    added_count += 1
                elif value.action == 'update':
                    updated_count += 1
                elif value.action == 'delete':
                    deleted_count += 1
        added.append(added_count)
        updated.append(updated_count)
        deleted.append(deleted_count)

    data_for_chart['added'] = added
    data_for_chart['updated'] = updated
    data_for_chart['deleted'] = deleted

    return data_for_chart

    rus_lang = {
        'date': 'Дата',
        'added': 'Добавлено',
        'updated': 'Изменено',
        'deleted': 'Удалено',
    }

    fig = go.Figure()

    categories = [
        ('added', '#4CAF50', rus_lang['added']),
        ('updated', "#E3EA27", rus_lang['updated']),
        ('deleted', "#F63D30", rus_lang['deleted'])
    ]

    for eng_key, color, rus_name in categories:
        fig.add_trace(go.Bar(
            x=data_for_chart['date'],
            y=data_for_chart[eng_key],
            name=rus_name,
            marker_color=color,
        ))

    fig.update_layout(
        barmode='group',
        margin=dict(l=20, r=20, t=40, b=40),
        height=300,
        width=500,
        title={
            'text': 'Журнал действий',
            'y': 0.975,
            'x': 0.1,
            'xanchor': 'center',
            'yanchor': 'top'
        },
    )

    chart = fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'responsive': True
        }
    )

    return chart


def action_diagram(request, filter_form):
    queryset = Action_Logging.objects.all()

    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')
        table_name = filter_form.cleaned_data.get('table_name')

        if start_date:
            queryset = queryset.filter(datetime__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(datetime__date__lte=end_date)
        if table_name:
            queryset = queryset.filter(table_name=table_name)

    chart = create_action_chart(request, queryset)
    return chart


def create_track_occupancy_chart(request, queryset):
    db_data = queryset

    if not db_data.exists():
        messages.info(request, 'Данные для диаграммы "Распределение участников по трекам" отсутствуют!')

    tracks_names = []
    tracks_names.extend([data.title for data in db_data])

    tracks_occupied = []
    tracks_occupied.extend([data.occupied for data in db_data])

    return tracks_names, tracks_occupied
    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=tracks_names,
        values=tracks_occupied,
        hole=0.7,
        textposition='outside',
    ))

    fig.update_layout(
        title={
            'text': 'Распределение участников по трекам',
            'y': 0.975,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin=dict(l=20, r=20, t=40, b=40),
        height=300,
    )

    chart = fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'responsive': True
        }
    )

    return chart


def chart_of_track_occupancy(request):
    queryset = Tracks.objects.filter(occupied__gt=0)
    tracks_names, tracks_occupied = create_track_occupancy_chart(request, queryset)
    return tracks_names, tracks_occupied


def create_user_registration_dynamics_chart(request, queryset):
    db_data = queryset

    if not db_data.exists():
        messages.info(request, 'Данные для диаграммы "Динамика регистрации пользователей" отсутствуют!')

    data_dict = {}
    for data in db_data:
        if data.created_at not in data_dict.keys():
            data_dict[data.created_at] = 1
        else:
            data_dict[data.created_at] += 1

    sorted_dates = sorted(data_dict.keys())
    counts = [data_dict[date] for date in sorted_dates]

    return sorted_dates, counts
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=sorted_dates,
        y=counts,
    ))

    fig.update_layout(
        title={
            'text': 'Динамика регистрации пользователей',
            'y': 0.975,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        margin=dict(l=20, r=20, t=40, b=40),
        height=300,
    )

    chart = fig.to_html(
        full_html=False,
        include_plotlyjs='cdn',
        config={
            'displayModeBar': True,
            'displaylogo': False,
            'responsive': True
        }
    )

    return chart


def user_registration_dynamics_chart(request, filter_form):
    queryset = Users.objects.all()

    if filter_form.is_valid():
        start_date = filter_form.cleaned_data.get('start_date')
        end_date = filter_form.cleaned_data.get('end_date')

        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)

    sorted_dates, counts = create_user_registration_dynamics_chart(request, queryset)
    return sorted_dates, counts


def make_dashboard(request, title):
    from django.apps import apps
    from plotly.subplots import make_subplots
    dashboard = []

    all_models = apps.get_models()
    all_tables = []
    all_tables.extend(model._meta.db_table for model in all_models)

    tables = []
    for table in all_tables:
        model_name = get_model(table)
        if model_name:
            if model_name == 'Админ зона':
                tables.append(Roles)
            else:
                tables.append(model_name)

    filter_form = ChartFilterForm(request.GET or None, tables=tables)

    data_for_chart = action_diagram(request, filter_form)
    tracks_names, tracks_occupied = chart_of_track_occupancy(request)
    sorted_dates, counts = user_registration_dynamics_chart(request, filter_form)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Журнал действий',
                       'Динамика регистрации пользователей', 'Распределение участников по трекам'),
        specs=[[{"colspan": 2}, None],
               [{"type": "scatter"}, {"type": "pie"}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.15,
    )

    fig.add_trace(
        go.Bar(x=data_for_chart['date'], y=data_for_chart['added'], name='Добавлено', marker_color='#4CAF50'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=data_for_chart['date'], y=data_for_chart['updated'], name='Изменено', marker_color='#E3EA27'),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=data_for_chart['date'], y=data_for_chart['deleted'], name='Удалено', marker_color='#F63D30'),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=sorted_dates, y=counts, name='Линия', marker_color="#327AFF"),
        row=2, col=1
    )

    fig.add_trace(
        go.Pie(labels=tracks_names, values=tracks_occupied, hole=0.7, textposition='outside'),
        row=2, col=2
    )

    fig.update_layout(
        height=600,
        showlegend=True,
        title_font_size=24,
        margin=dict(l=20, r=20, t=50, b=40),
        legend=dict(
            title="<b>Легенды</b>",
            title_font_size=12,
            font=dict(size=10),
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="center",
            x=1.2,
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='#CCC',
            borderwidth=1,
            itemwidth=30,
            tracegroupgap=20,
            itemclick=False,
            groupclick="toggleitem"
        ),
    )

    dashboard = [fig.to_html(full_html=False,
                             include_plotlyjs='cdn',
                             config={
                                 'displayModeBar': True,
                                 'displaylogo': False,
                                 'responsive': True
                                 })]

    return title, '', '', '', filter_form, dashboard
