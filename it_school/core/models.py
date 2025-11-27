from datetime import datetime, date, timedelta
from django.db import models
from .validators import *


class FullName(models.Model):
    first_name = models.CharField('Имя', max_length=25, validators=[name_validator])
    last_name = models.CharField('Фамилия', max_length=25, validators=[name_validator])
    patronymic = models.CharField('Отчество', max_length=25, blank=True, null=True, validators=[name_validator])

    class Meta:
        abstract = True
        ordering = ['last_name', 'first_name', 'patronymic']

    def __str__(self):
        if self.patronymic:
            return f"{self.last_name} {self.first_name} {self.patronymic}"
        return f"{self.last_name} {self.first_name}"


class Roles(models.Model):
    title = models.CharField('Роль', max_length=150, unique=True)

    class Meta:
        db_table = 'roles'
        verbose_name = 'Роль'
        verbose_name_plural = 'Роли'
        ordering = ['title']

    def __str__(self):
        return self.title


class Menu(models.Model):
    title = models.CharField('Пункт меню', max_length=150, unique=True)

    class Meta:
        db_table = 'menu'
        verbose_name = 'Меню'
        verbose_name_plural = 'Меню'
        ordering = ['title']

    def __str__(self):
        return self.title


class Accesses(models.Model):
    read_info = models.BooleanField('Просмотр')
    edit_info = models.BooleanField('Изменение')
    write_info = models.BooleanField('Добавление')
    delete_info = models.BooleanField('Удаление')
    id_menu = models.ForeignKey(Menu, verbose_name='Пункт меню', null=True, on_delete=models.CASCADE, db_column='id_menu')
    id_role = models.ForeignKey(Roles, verbose_name='Роль', null=True, on_delete=models.CASCADE, db_column='id_role')

    class Meta:
        db_table = 'accesses'
        unique_together = ['id_role', 'id_menu']
        verbose_name = 'Права доступа'
        verbose_name_plural = 'Права доступа'


class Audiences(models.Model):
    audience_number = models.CharField('Номер аудитории', max_length=10, unique=True)
    capacity = models.PositiveIntegerField('Вместимость аудитории', validators=[audience_capacity_validator])

    class Meta:
        db_table = 'audiences'
        verbose_name = 'Аудитория'
        verbose_name_plural = 'Аудитории'
        ordering = ['audience_number']

    def __str__(self):
        return self.audience_number


class Classes(models.Model):
    title = models.CharField('Название занятия', max_length=150)
    lesson_link = models.URLField('Ссылка на занятие', max_length=500)

    class Meta:
        db_table = 'classes'
        unique_together = ['title', 'lesson_link']
        verbose_name = 'Занятие'
        verbose_name_plural = 'Занятия'
        ordering = ['title']

    def __str__(self):
        return self.title


class Tracks(models.Model):
    title = models.CharField('Название трека', max_length=200, unique=True, validators=[title_validator])
    capacity = models.PositiveIntegerField('Вместимость трека', validators=[track_capacity_validator])
    occupied = models.PositiveIntegerField('Занятость трека', default=0)

    class Meta:
        db_table = 'tracks'
        verbose_name = 'Трек'
        verbose_name_plural = 'Треки'
        ordering = ['title']

    def __str__(self):
        return self.title


class Classes_Schedule(models.Model):
    id_track = models.ForeignKey(Tracks, verbose_name='Трек', null=True, on_delete=models.SET_NULL, db_column='id_track')
    id_lesson = models.ForeignKey(Classes, verbose_name='Занятие', null=True, on_delete=models.SET_NULL, db_column='id_lesson')
    id_audience = models.ForeignKey(Audiences, verbose_name='Аудитория', null=True, on_delete=models.SET_NULL, db_column='id_audience')
    lesson_date = models.DateField('Дата')
    start_time = models.TimeField('Время начала')
    end_time = models.TimeField('Время окончания')

    class Meta:
        db_table = 'classes_schedule'
        verbose_name = 'Расписание занятий'
        verbose_name_plural = 'Расписания занятий'
        ordering = ['lesson_date', 'start_time', 'end_time']

    def russian_date(self, date):
        """Дата в формате '15 октября 2025 г.'"""

        months = {
            1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
            5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
            9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря'
        }

        return f"{date.day} {months[date.month]} {date.year} г."

    def get_short_time(self, time_obj):
        return time_obj.strftime("%#H:%M")

    def get_time_range(self):
        return f"{self.get_short_time(self.start_time)} – {self.get_short_time(self.end_time)}"

    def __str__(self):
        return f"{self.russian_date(self.lesson_date)} {self.get_time_range()}"

    def clean(self):
        super().clean()
        errors = {}

        if self.lesson_date and self.lesson_date <= date.today():
            errors['lesson_date'] = f'Дата занятия должна быть позже {self.russian_date(date.today())}'

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors['end_time'] = 'Время окончания должно быть позже времени начала'

        if self.start_time and self.end_time:
            start_datetime = datetime.combine(date.today(), self.start_time)
            end_datetime = datetime.combine(date.today(), self.end_time)
            time_difference = end_datetime - start_datetime
            duration = timedelta(hours=1, minutes=30)
            if time_difference != duration:
                errors['end_time'] = 'Продолжительность занятия должна быть 1 час 30 минут'

        if self.lesson_date and self.start_time and self.end_time:
            conflicting_schedules = Classes_Schedule.objects.filter(
                lesson_date=self.lesson_date,
                id_audience=self.id_audience,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )

            if self.pk:
                conflicting_schedules = conflicting_schedules.exclude(pk=self.pk)

            if conflicting_schedules.exists():
                errors['id_audience'] = f'Аудитория {self.id_audience} занята c {self.get_time_range()}'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Specialties(models.Model):
    title = models.CharField('Специальность', max_length=150, unique=True)

    class Meta:
        db_table = 'specialties'
        verbose_name = 'Специальность'
        verbose_name_plural = 'Специальности'
        ordering = ['title']

    def __str__(self):
        return self.title


class Study_Groups(models.Model):
    title = models.CharField('Группа', max_length=25, unique=True)

    class Meta:
        db_table = 'study_groups'
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ['title']

    def __str__(self):
        return self.title


class Faculties(models.Model):
    title = models.CharField('Факультет', max_length=200, unique=True)

    class Meta:
        db_table = 'faculties'
        verbose_name = 'Факультет'
        verbose_name_plural = 'Факультеты'
        ordering = ['title']

    def __str__(self):
        return self.title


class Volunteers(FullName):
    class Course_Number(models.TextChoices):
        FIRST = '1', '1'
        SECOND = '2', '2'
        THIRD = '3', '3'
        FOURTH = '4', '4'
        FIFTH = '5', '5'
        SIXTH = '6', '6'
        SEVENTH = '7', '7'
        EIGHTH = '8', '8'

    course = models.CharField(
        'Курс',
        max_length=1,
        choices=Course_Number.choices
    )

    id_faculty = models.ForeignKey(Faculties, verbose_name='Факультет', null=True, on_delete=models.SET_NULL, db_column='id_faculty')
    id_speciality = models.ForeignKey(Specialties, verbose_name='Специальность', null=True, on_delete=models.SET_NULL, db_column='id_speciality')
    id_group = models.ForeignKey(Study_Groups, verbose_name='Группа', null=True, on_delete=models.SET_NULL, db_column='id_group')

    class Meta:
        db_table = 'volunteers'
        verbose_name = 'Волонтёр'
        verbose_name_plural = 'Волонтёры'


class Teachers(FullName):
    class Meta:
        db_table = 'teachers'
        verbose_name = 'Преподаватель'
        verbose_name_plural = 'Преподаватели'


class Job_Titles(models.Model):
    title = models.CharField('Должность', max_length=200, unique=True)

    class Meta:
        db_table = 'job_titles'
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'
        ordering = ['title']

    def __str__(self):
        return self.title


class Academic_Degrees(models.Model):
    title = models.CharField('Учёная степень', max_length=200, unique=True)

    class Meta:
        db_table = 'academic_degrees'
        verbose_name = 'Учёная степень'
        verbose_name_plural = 'Учёные степени'
        ordering = ['title']

    def __str__(self):
        return self.title


class Place_Works(models.Model):
    title = models.CharField('Место работы', max_length=200, unique=True)

    class Meta:
        db_table = 'place_works'
        verbose_name = 'Место работы'
        verbose_name_plural = 'Места работы'
        ordering = ['title']

    def __str__(self):
        return self.title


class Academic_Titles(models.Model):
    title = models.CharField('Учёное звание', max_length=200, unique=True)

    class Meta:
        db_table = 'academic_titles'
        verbose_name = 'Учёное звание'
        verbose_name_plural = 'Учёные звания'
        ordering = ['title']

    def __str__(self):
        return self.title


class Teachers_Job_Titles(models.Model):
    id_teacher = models.ForeignKey(Teachers, verbose_name='Преподаватель', on_delete=models.CASCADE, db_column='id_teacher')
    id_job_title = models.ForeignKey(Job_Titles, verbose_name='Должность', on_delete=models.CASCADE, db_column='id_job_title')

    class Meta:
        db_table = 'teachers_job_titles'
        unique_together = ['id_teacher', 'id_job_title']
        verbose_name = 'Должность преподавателя'
        verbose_name_plural = 'Должности преподавателей'
        ordering = ['id_teacher']

    def __str__(self):
        return f'{self.id_teacher}'


class Teachers_Academic_Degrees(models.Model):
    id_teacher = models.ForeignKey(Teachers, verbose_name='Преподаватель', on_delete=models.CASCADE, db_column='id_teacher')
    id_academic_degree = models.ForeignKey(Academic_Degrees, verbose_name='Учёная степень', on_delete=models.CASCADE, db_column='id_academic_degree')

    class Meta:
        db_table = 'teachers_academic_degrees'
        unique_together = ['id_teacher', 'id_academic_degree']
        verbose_name = 'Учёная степень преподавателя'
        verbose_name_plural = 'Учёные степени преподавателей'
        ordering = ['id_teacher']

    def __str__(self):
        return f'{self.id_teacher}'


class Teachers_Place_Works(models.Model):
    id_teacher = models.ForeignKey(Teachers, verbose_name='Преподаватель', on_delete=models.CASCADE, db_column='id_teacher')
    id_place_work = models.ForeignKey(Place_Works, verbose_name='Место работы', on_delete=models.CASCADE, db_column='id_place_work')

    class Meta:
        db_table = 'teachers_place_works'
        unique_together = ['id_teacher', 'id_place_work']
        verbose_name = 'Место работы преподавателя'
        verbose_name_plural = 'Места работы преподавателей'
        ordering = ['id_teacher']

    def __str__(self):
        return f'{self.id_teacher}'


class Teachers_Academic_Titles(models.Model):
    id_teacher = models.ForeignKey(Teachers, verbose_name='Преподаватель', on_delete=models.CASCADE, db_column='id_teacher')
    id_academic_title = models.ForeignKey(Academic_Titles, verbose_name='Учёное звание', on_delete=models.CASCADE, db_column='id_academic_title')

    class Meta:
        db_table = 'teachers_academic_titles'
        unique_together = ['id_teacher', 'id_academic_title']
        verbose_name = 'Учёное звание преподавателя'
        verbose_name_plural = 'Учёные звания преподавателей'
        ordering = ['id_teacher']

    def __str__(self):
        return f'{self.id_teacher}'


class Cities(models.Model):
    title = models.CharField('Город', max_length=200, unique=True)

    class Meta:
        db_table = 'cities'
        verbose_name = 'Город'
        verbose_name_plural = 'Города'
        ordering = ['title']

    def __str__(self):
        return self.title


class Educational_Institutions(models.Model):
    title = models.CharField('Учебное заведение', max_length=200, unique=True)

    class Meta:
        db_table = 'educational_institutions'
        verbose_name = 'Учебное заведение'
        verbose_name_plural = 'Учебные заведения'
        ordering = ['title']

    def __str__(self):
        return self.title


class Participants(FullName):
    class Class_Number(models.TextChoices):
        FIRST = '1', '1'
        SECOND = '2', '2'
        THIRD = '3', '3'
        FOURTH = '4', '4'
        FIFTH = '5', '5'
        SIXTH = '6', '6'
        SEVENTH = '7', '7'
        EIGHTH = '8', '8'
        NINE = '9', '9'
        TEN = '10', '10'
        ELEVEN = '11', '11'

    class_number = models.CharField(
        'Класс',
        max_length=2,
        choices=Class_Number.choices
    )

    id_city = models.ForeignKey(Cities, verbose_name='Город', null=True, on_delete=models.SET_NULL, db_column='id_city')
    id_educational_institution = models.ForeignKey(Educational_Institutions, verbose_name='Учебное заведение', null=True, on_delete=models.SET_NULL, db_column='id_educational_institution')
    phone_number = models.CharField('Номер телефона', max_length=22, unique=True, validators=[phone_number_validator])
    email = models.EmailField('Почта', max_length=150, unique=True)
    link_copy_consent = models.URLField('Ссылка на согласие на обработку персональных данных', max_length=500, unique=True)
    diploma = models.URLField('Ссылка на диплом', null=True, max_length=500, blank=True)

    class Meta:
        db_table = 'participants'
        verbose_name = 'Участник'
        verbose_name_plural = 'Участники'


class Visits(models.Model):
    class VisitStatus(models.TextChoices):
        PRESENT = '+', 'Присутствовал'
        ABSENT = '-', 'Отсутствовал'

    id_participant = models.ForeignKey(Participants, verbose_name='Участник', on_delete=models.CASCADE, db_column='id_participant')
    id_class = models.ForeignKey(Classes, verbose_name='Занятие', on_delete=models.CASCADE, db_column='id_class')
    visit = models.CharField(
        'Посещение',
        max_length=1,
        choices=VisitStatus.choices
    )

    class Meta:
        db_table = 'visits'
        unique_together = ['id_class', 'id_participant']
        verbose_name = 'Посещение'
        verbose_name_plural = 'Посещения'
        ordering = ['id_participant']

    def __str__(self):
        return f'{self.id_participant}'


class Participants_Tracks(models.Model):
    id_participant = models.ForeignKey(Participants, verbose_name='Участник', unique=True, on_delete=models.CASCADE, db_column='id_participant')
    id_track = models.ForeignKey(Tracks, verbose_name='Трек', on_delete=models.CASCADE, db_column='id_track')

    class Meta:
        db_table = 'participants_tracks'
        verbose_name = 'Трек участника'
        verbose_name_plural = 'Треки участников'
        ordering = ['id_participant']

    def __str__(self):
        return f'{self.id_participant}'


class Volunteer_Tracks(models.Model):
    id_volunteer = models.ForeignKey(Volunteers, verbose_name='Волонтёр', on_delete=models.CASCADE, db_column='id_volunteer')
    id_track = models.ForeignKey(Tracks, verbose_name='Трек', on_delete=models.CASCADE, db_column='id_track')

    class Meta:
        db_table = 'volunteer_tracks'
        unique_together = ['id_volunteer', 'id_track']
        verbose_name = 'Трек волонтёра'
        verbose_name_plural = 'Треки волонтёров'
        ordering = ['id_volunteer']

    def __str__(self):
        return f'{self.id_volunteer}'


class Teacher_Tracks(models.Model):
    id_teacher = models.ForeignKey(Teachers, verbose_name='Преподаватель', on_delete=models.CASCADE, db_column='id_teacher')
    id_track = models.ForeignKey(Tracks, verbose_name='Трек', on_delete=models.CASCADE, db_column='id_track')

    class Meta:
        db_table = 'teacher_tracks'
        unique_together = ['id_teacher', 'id_track']
        verbose_name = 'Трек преподавателя'
        verbose_name_plural = 'Треки преподавателей'
        ordering = ['id_teacher']

    def __str__(self):
        return f'{self.id_teacher}'


class Teacher_Schedules(models.Model):
    id_teacher = models.ForeignKey(Teachers, verbose_name='Преподаватель', on_delete=models.CASCADE, db_column='id_teacher')
    id_class_schedule = models.ForeignKey(Classes_Schedule, verbose_name='Расписание занятия', on_delete=models.CASCADE, unique=True, db_column='id_class_schedule')

    class Meta:
        db_table = 'teacher_schedules'
        unique_together = ['id_teacher', 'id_class_schedule']
        verbose_name = 'Расписание преподавателя'
        verbose_name_plural = 'Расписание преподавателей'
        ordering = ['id_teacher']

    def __str__(self):
        return f'{self.id_teacher}'
