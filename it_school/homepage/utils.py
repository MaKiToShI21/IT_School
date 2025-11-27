from core.models import *


directories = {'tracks': Tracks,
               'teachers': Teachers,
               'job_title': Job_Titles,
               'academic_degrees': Academic_Degrees,
               'place_works': Place_Works,
               'academic_titles': Academic_Titles,
               'specialties': Specialties,
               'study_groups': Study_Groups,
               'faculties': Faculties,
               'cities': Cities,
               'educational_institutions': Educational_Institutions,
               'audiences': Audiences,
               'classes': Classes,
               }

associations = {'teacher_tracks': Teacher_Tracks,
                'volunteer_tracks': Volunteer_Tracks,
                'participants_tracks': Participants_Tracks,
                'teacher_schedules': Teacher_Schedules,
                'teachers_job_titles': Teachers_Job_Titles,
                'teachers_academic_degrees': Teachers_Academic_Degrees,
                'teachers_academic_titles': Teachers_Academic_Titles,
                'teachers_place_works': Teachers_Place_Works,
                'classes_schedule': Classes_Schedule,
                'visits': Visits,
                }

groups = {'volunteers': Volunteers,
          'participants': Participants,
          }

various = {'change_password': 'Смена пароля', 'documents': 'Документы', 'admin_zone': 'Админ зона', } # 1) 'settings': 'Настройки',

reference = {'content': 'Содержание', 'about': 'О программе'}

dict = {'Справочник': directories, 'Ассоциации': associations, 'Группы': groups, 'Разное': various, 'Справка': reference}

directory_info = {
    'Справочник': 'Этот раздел представляет основные справочники системы, содержащие нормативно-справочную информацию предметной области. Справочники используются как базовые данные для работы всей системы, они никак не зависят от других записей. Соответствующие роли могут добавлять, изменять и удалять информацию.',
    'Ассоциации': 'Этот раздел представляет собой отношения между основными записями системы. Соответствующие роли могут добавлять, изменять и удалять информацию.',
    'Группы': 'Основные группы пользователей системы - волонтеры и участники. Содержат персональные данные и информацию для организационного сопровождения.',
    'Разное': 'Этот раздел содержит сервисные и административные функции системы.',
    'Справка': 'Информационно-справочный раздел системы с документацией и информацией о программе.',
}


def get_model(paragraph):
    for _, item in dict.items():
        if paragraph in item:
            return item.get(paragraph)
    else:
        return False
