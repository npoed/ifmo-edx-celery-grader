# coding=utf-8

from celery import Task
from celery.states import SUCCESS, FAILURE, STARTED
from courseware.models import StudentModule
from ifmo_celery_grader.models import GraderTask
from opaque_keys.edx.keys import CourseKey, UsageKey

import json


class GraderTaskBase(Task):
    """
    Основной базовый класс оценивающего задания. Используется в ряде модулей
    XBlock, требующиъ отложенной или асинхронной проверки.
    """

    abstract = True

    def run(self, *args, **kwargs):
        """
        Исполняемый код, который будет вызываться worker'ом при обработке
        задания.

        Требуется наличие следующих параметров:

        Словарь `grader_payload` содержит нагрузку для оценивающей программы,
        например, входные параметры генератора заданий, данные варианта и так
        далее, то есть позволяют идентифицировать само задание, без привязки к
        пользователю.

        Словарь `system_payload` содержит данные для служебного пользователя.
        Они никак не должны влиять на процесс оценивания, однако могут
        ссылаться на внетреннее устройство подсистем, например, записи в БД,
        связанные с пользователем.

        Объект `student_input` содержит пользовательский ввод. Он не
        подразумевает идентификацию пользователя (для этого можно
        воспользоваться словарём `system_payload`), а лишь содержит ответ
        пользователя на задание. Это единственный объект, который передаётся
        оценивающей подсистеме "как есть" без какой либо обработки.

        :param args:
        :param kwargs:

        :return:
        """

        # Получаем связанные данные
        grader_payload = kwargs.get('grader_payload')
        system_payload = kwargs.get('system_payload')
        student_input = kwargs.get('student_input')

        # Получим соотвествующую заданию запись в БД и обновим текущий статус
        # задания
        task = GraderTask.objects.get(task_id=system_payload.get('task_id'))
        task.task_state = STARTED
        task.save()

        # Проводим оценивание на основе нагрузки для оценивающей подсистемы и
        # пользовательского ввода
        try:
            return self.grade(student_input, grader_payload)
        except NotImplementedError:
            pass

        return

    def on_success(self, retval, task_id, args, kwargs):
        """
        Вызывается в случае, если оценивание (основной рабочий процесс) не
        вызвало ошибок.

        :param retval:
        :param task_id:
        :param args:
        :param kwargs:

        :return:
        """

        # Получаем связанные данные
        grader_payload = kwargs.get('grader_payload')
        system_payload = kwargs.get('system_payload')
        student_input = kwargs.get('student_input')

        # Получим соотвествующую заданию запись в БД и обновим текущий статус
        # задания
        task = GraderTask.objects.get(task_id=system_payload.get('task_id'))
        task.task_state = SUCCESS
        task.task_output = retval
        task.save_now()

        # Будем вписывать баллы за выполнение задания прямо в модуль, хотя
        # стоит рассмотреть более детально способы, как по-другому сохранять
        # баллы, чтобы они правильно воспринимались платформой. Очевидно, что
        # способ с сигналами тут не работает, потому что worker'ы вообще
        # работают обособленно, хотя это стоит проверить отдельно.
        course_key = CourseKey.from_string(system_payload.get('course_id'))
        usage_key = UsageKey.from_string(system_payload.get('module_id'))
        module = StudentModule.objects.get(student_id=system_payload.get('user_id'),
                                           course_id=course_key,
                                           module_state_key=usage_key)

        # Создаём системную нагрузку сверх уже существующей системной нагрузки.
        # Возможно, стоило бы "пропатчить" уже существующую `system_payload`,
        # но будем плодить ещё сущности.
        system = {
            'task': task,
            'module': module,
        }

        # Насколько я помню, неотловленное исключение в `on_success` не
        # приводит к вызову `on_failure`. Возможно, стоит сделать это руками
        # самостоятельно, чтобы зафиксировать факт ошибки.
        try:
            self.grade_success(student_input, grader_payload, system_payload, system, retval)
        except NotImplementedError:
            pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        Вызывается в случае, если оценивание (основной рабочий процесс) привёл к ошибке.

        :param retval:
        :param task_id:
        :param args:
        :param kwargs:

        :return:
        """
        task = GraderTask.objects.get(task_id=task_id)
        task.task_state = FAILURE
        task.task_output = exc.message
        task.save()

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """
        Вызывается после выполнения основного рабочего процесса вне зависимости от ошибки.

        :param retval:
        :param task_id:
        :param args:
        :param kwargs:

        :return:
        """

        system_payload = kwargs.get('system_payload')

        # Получаем связанный модуль
        course_key = CourseKey.from_string(system_payload.get('course_id'))
        usage_key = UsageKey.from_string(system_payload.get('module_id'))
        module = StudentModule.objects.get(student_id=system_payload.get('user_id'),
                                           course_id=course_key,
                                           module_state_key=usage_key)

        # Сбрасываем приязанное к модулю (и XBlock'у) задание
        state = json.loads(module.state)
        state['celery_task_id'] = None
        module.state = json.dumps(state)
        module.save()

    def grade(self, student_input, grader_payload):
        """
        Вызывается основным рабочим процессом.

        :param student_input: Пользовательский ввод
        :param grader_payload: Нагрузка грэйдера

        :return: Результат оценивания
        """
        raise NotImplementedError()

    def grade_success(self, student_input, grader_payload, system_payload, system, response):
        """
        Вызывается в том случае, когда оцениваните прошло успешно.

        Сохранение результата оценивания сейчас возлагается целиком на
        программиста, реализующего оценивающую подсистему. Для сохранения
        результатов оценивания извлекается пользовательский модуль, чтобы
        была возможность записать результат прямо в него.

        В будущем, разумеется, следует избавиться от такого хака, и не давать
        наследующимся подсистемам писать в модуль, но сейчас это необходимо,
        так как помимо баллов необходимо записывать связанную информацию, как,
        например, историю пользовательских ответов, в случае, когда речь идёт
        о внешних системах (AcademicNT, HTMLAcademy).

        Более того, на данный момент протоколом не определено, что именно
        должен возвращать метод `grade`, поэтому это может быть любой объект,
        поэтому ответственность за запись результата возлагается на того, кто
        его вернул.

        :param student_input: Пользовательский ввод
        :param grader_payload: Параметры грэйдера
        :param system_payload: Параметры системы
        :param system: Дополнительные системные параметры
        :param response: Ответ грэйдера

        :return:
        """
        raise NotImplementedError()


def submit_task_grade(task_class, task, countdown=0):
    """
    Постановка задания в очередь.

    Задание не создаётся, а ставится в очередь уже существующее. Для создания
    задания требуется воспользоваться методом `reserve_task`.

    :param task_class: Класс задания, подкласс `Task`
    :param task: Экземпляр задания
    :param countdown: Интервал в секундах, через который должно выполнится
                      задание

    :return: `task`
    """

    task_data = {
        'student_input': task.student_input,
        'grader_payload': task.grader_payload,
        'system_payload': task.system_payload,
    }
    task_class().apply_async(task_id=task.task_id, kwargs=task_data, countdown=countdown, add_to_parent=False)

    return task


def reserve_task(xblock=None, save=False, grader_payload=None, system_payload=None, student_input=None, task_type=None):
    """
    Резервация задания.

    Создаётся сущность в базе данных, которой присваивается уникальный
    идентификатор для дальнейшего использования.

    На данный момент `task_type` не несёт большой смысловой нагрузки и служит
    скорее для отладочных целей. Каждая подсистема сама определяет, какие
    значения она может принимать.

    Задание только создаётся, но не ставится в очередь на выполнение. Для
    постановки в очередь требуется воспользоваться методом `submit_task_grade`.

    :param xblock: XBlock, который хочет зарезервировать задание
    :param save: Требуется ли сохранить XBlock после присваивании задания
    :param grader_payload: Нагрузка грэйдера
    :param system_payload: Системная нагрузка
    :param student_input: Пользовательский ввод
    :param task_type: Тип задания
    :return:
    """

    # Создаём запись в базе
    task = GraderTask.create(grader_payload=grader_payload, student_input=student_input, task_type=task_type,
                             system_payload=system_payload)

    # Уникальный идентификатор присваивается в конструкторе, поэтому нужно
    # дополнительно извлечь его и приписать в "нагрузку".
    system_payload['task_id'] = task.task_id
    task.system_payload = system_payload

    # То, что мы делаем, это фактически insert+update. Посмотреть, как можно
    # этого избежать
    task.save_now()

    # Небольшой хак: если задание было зарезервировано в обработчике XBlock, то
    # ему в атрибут мы запишем вновь созданное задание. Хотя, возможно, нам
    # вообще не нужно хранить ссылку на задание в XBlocke, потому как их может
    # быть и несколько.
    # Да и вообще, не всё ли равно блоку, какое задание в очереди?
    if xblock is not None:
        if hasattr(xblock, 'celery_task_id'):
            xblock.celery_task_id = task.task_id
        if save and hasattr(xblock, 'save_now'):
            xblock.save_now()

    # Возвращаем созданное задание
    return task