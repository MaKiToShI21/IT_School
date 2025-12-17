from django import forms
from django.db import models
from django.core.exceptions import ValidationError
import re


def create_form(model, instance=None, data=None):
    exclude_fields = ['occupied', 'password'] # , 'email'
    for field in model._meta.get_fields():
        if field.auto_created:
            exclude_fields.append(field.name)
    model_form = model

    class CustomForm(forms.ModelForm):
        class Meta:
            model = model_form
            fields = '__all__'
            exclude = exclude_fields
            widgets = create_widgets(model)

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            for field_name, field in self.fields.items():
                try:
                    model_field = model._meta.get_field(field_name)

                    if getattr(model_field, 'unique', False):
                        if isinstance(model_field, models.ForeignKey):
                            field.error_messages['unique'] = f'{field.label} уже занят.'
                        else:
                            field.error_messages['unique'] = f'{field.label} с таким значением уже существует.'

                    if field.required:
                        field.error_messages['required'] = f'Поле "{field.label}" обязательно для заполнения.'
                except:
                    continue

    return CustomForm(instance=instance, data=data)


def create_widgets(model):
    widgets = {}
    model_fields = [f for f in model._meta.fields if not f.auto_created]

    for field in model_fields:
        field_type = type(field)

        if field.is_relation and isinstance(field, models.ForeignKey):
            widgets[field.name] = forms.Select(attrs={
                'class': 'select',
            })
        elif field_type in [models.DateField]:
            widgets[field.name] = forms.DateInput(attrs={
                'type': 'date',
                'style': 'width: auto; min-width: 150px;'
            }, format='%Y-%m-%d')
        elif field_type in [models.TimeField]:
            widgets[field.name] = forms.TimeInput(attrs={
                'type': 'time',
                'style': 'width: auto; min-width: 130px;'
            })
        elif hasattr(field, 'choices') and field.choices:
            widgets[field.name] = forms.Select(attrs={
                'class': 'select',
            })
        elif field_type in [models.IntegerField, models.PositiveIntegerField,
                           models.DecimalField, models.FloatField]:
            widgets[field.name] = forms.NumberInput(attrs={
                'placeholder': f'Введите {field.verbose_name.lower()}',
                'step': 'any' if field_type in [models.DecimalField, models.FloatField] else '1',
                'style': 'width: auto; min-width: 270px;'
            })
        elif field_type in [models.EmailField]:
            widgets[field.name] = forms.EmailInput(attrs={
                'placeholder': f'Введите {field.verbose_name.lower()}',
                'style': 'width: auto; min-width: 500px;',
            })
        elif field_type in [models.URLField]:
            widgets[field.name] = forms.URLInput(attrs={
                'placeholder': f'Введите {field.verbose_name.lower()}',
                'style': 'width: auto; min-width: 500px;'
            })
        else:
            widgets[field.name] = forms.TextInput(attrs={
                'placeholder': f'Введите {field.verbose_name.lower()}',
                'style': 'width: auto; min-width: 500px;'
            })

    return widgets


class DocumentsForm(forms.Form):
    sql_request = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Введите ваш SQL запрос',
        'class': 'textarea'
        }),
        )

    def clean_sql_request(self):
        sql_request = self.cleaned_data.get('sql_request', '')

        if sql_request.count(';') > 15:
            raise ValidationError("Запрещено выполнять более 15 SQL запросов за раз")

        upper_sql_request = sql_request.upper()

        sql_clean = re.sub(r'/\*.*?\*/', '', upper_sql_request)
        sql_clean = re.sub(r'--[^\n]*', '', sql_clean)

        ban_commands = [
            'DROP', 'ALTER', 'TRUNCATE', 'CREATE',
            'EXEC', 'SHUTDOWN', 'GRANT', 'REVOKE',
            'BACKUP', 'RESTORE', 'DENY'
            ]

        for command in ban_commands :
            if re.search(r'\b' + command + r'\b', sql_clean):
                raise ValidationError(f'Обнаружена запрещенная команда "{command}" в SQL запросе')

        return sql_request


class ChartFilterForm(forms.Form):
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'style': 'width: auto; min-width: 150px;'})
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'style': 'width: auto; min-width: 150px;'})
    )

    table_name = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select'})
    )

    track_name = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={'class': 'select'})
    )

    def __init__(self, *args, **kwargs):
        tables = kwargs.pop('tables', [])
        super().__init__(*args, **kwargs)

        table_choices = [('', 'Все таблицы')]
        for table in tables:
            if table._meta.db_table == 'roles':
                table_choices.append(('admin_zone', 'Админ зона'))
            else:
                table_choices.append((table._meta.db_table, table._meta.verbose_name_plural))
        table_choices.sort(key=lambda x: x[0] if x[0] == '' else x[1])
        self.fields['table_name'].choices = table_choices
