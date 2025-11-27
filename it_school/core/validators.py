from django.core.exceptions import ValidationError


def track_capacity_validator(capacity):
    min_capacity = 50
    max_capacity = 1000
    if capacity < min_capacity:
        raise ValidationError(f'Вместимость не может быть меньше {min_capacity} человек.')
    elif capacity > max_capacity:
        raise ValidationError(f'Вместимость не может быть больше {max_capacity} человек.')


def audience_capacity_validator(capacity):
    min_capacity = 15
    max_capacity = 200
    if capacity < min_capacity:
        raise ValidationError(f'Вместимость не может быть меньше {min_capacity} человек.')
    elif capacity > max_capacity:
        raise ValidationError(f'Вместимость не может быть больше {max_capacity} человек.')


def title_validator(title):
    min_length = 5
    title = title.strip()

    if len(title) < min_length:
        raise ValidationError(f'Название должно содержать минимум {min_length} символа')


def phone_number_validator(phone_number):
    if len(phone_number) >= 11:
        print(phone_number[:2])
        if (phone_number[:2] == '+7' and len(phone_number) != 12) or (phone_number[0] == '8' and len(phone_number) != 11):
            raise ValidationError(f'Введите корректный номер телефона.')
    else:
        raise ValidationError(f'Номер телефона должен содержать 11 или более символов.')


def name_validator(name):
    for char in name:
        if char in [' ', '-']:
            continue
        if not char.isalpha():
            raise ValidationError(f'Поле не может содержать иные символы, кроме букв, пробела и "-".')
