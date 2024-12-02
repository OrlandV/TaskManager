"""
Консольный менеджер задач
"""
import argparse
import os
import json
import dateutil.parser as date_parser
import csv

VERSION = '1.0 20241202'
TASKS_CSV = 'tasks.csv'  # Путь к CSV-файлу с задачами.
TASKS_JSON = 'tasks.json'  # Путь к JSON-файлу с задачами.
HEADS = dict(id='ID', title='Название', description='Описание', category='Категория', due_date='Срок выполнения',
             priority='Приоритет', status='Статус')  # Словарь заголовков столбцов таблицы.
PRIORITIES = ('Низкий', 'Средний', 'Высокий')  # Ограниченный набор приоритетов.
STATUSES = ('Не выполнена', 'Выполнена')  # Ограниченный набор статусов.


class Task:
    """
    Задача.
    """
    index = 0  # Текущий индекс (ID задачи).

    def __init__(self, title: str, description: str, category: str, due_date: str, priority: int, id: int = 0,
                 status: bool = False):
        """
        Задача.
        :param title: Название задачи.
        :param description: Описание задачи.
        :param category: Категория задачи.
        :param due_date: Срок выполнения задачи. Формат гггг-мм-дд.
        :param priority: Приоритет задачи: 0 — низкий, 1 — средний, 2 — высокий.
        :param id: ID задачи, импортируемой из файла, при инициализации менеджера задач.
        :param status: Статус задачи.
        """
        if id:
            self.id = id
            if id > Task.index:
                Task.index = id
        else:
            Task.index += 1
            self.id = Task.index
        self.title = title
        self.description = description
        self.category = category
        self.due_date = due_date
        self.priority = PRIORITIES[priority]
        self.status = status

    def __contains__(self, item) -> bool:
        """
        Поиск текста в задаче (в названии или в описании).
        :param item: Искомый текст.
        :return: True, если найден. Иначе False.
        """
        return item.lower() in self.title.lower() or item.lower() in self.description.lower()


class TaskManager:
    """
    Менеджер задач.
    """
    tasks = []  # Список задач.

    def __init__(self):
        self.parser = self._get_parser()  # Парсер консольной команды.
        self.result = ''  # Текст (строка) для вывода в консоль.
        # Длины строк-ячеек.
        self.name_length = dict(id=2, title=8, description=8, category=9, due_date=15, priority=9, status=12)
        self._load_tasks()

    # @staticmethod
    def _get_parser(self) -> argparse.ArgumentParser:
        """
        Создание парсера консольной команды.
        :return: Парсер командной строки.
        """
        parser = argparse.ArgumentParser(prog='TaskManager.py', description=f'Менеджер задач (версия {VERSION})')
        subparsers = parser.add_subparsers(help='Команды:')

        parser_add = subparsers.add_parser('add', help='Добавление задачи одной командой.')
        parser_add.add_argument('title', help='Название задачи.')
        parser_add.add_argument('description', help='Описание задачи.')
        parser_add.add_argument('category', help='Категория задачи.')
        parser_add.add_argument('due_date', help='Срок выполнения задачи (дата).')
        parser_add.add_argument(
            'priority',
            type=int,
            choices=(0, 1, 2),
            help=f'Приоритет задачи (число): 0 — {PRIORITIES[0]}, 1 — {PRIORITIES[1]}, 2 — {PRIORITIES[2]}.'
        )
        parser_add.set_defaults(func=self.add)

        parser_add_inter = subparsers.add_parser('add_inter', help='Добавление задачи в интерактивном режиме.')
        parser_add_inter.set_defaults(func=self.add_inter)

        parser_completed = subparsers.add_parser('completed', help='Отметка задачи как выполненной.')
        parser_completed.add_argument('id', nargs='*', type=int, help='Список ID задач, разделённых пробелом.')
        parser_completed.set_defaults(func=self.completed)

        parser_cur = subparsers.add_parser('current', help='Вывод всех текущих задач.')
        parser_cur.set_defaults(func=self.current)

        parser_del = subparsers.add_parser('del', help='Удаление задачи.')
        group_del = parser_del.add_mutually_exclusive_group(required=True)
        group_del.add_argument('-c', '--category', nargs='*', help='Список категорий задач, разделённых пробелом.')
        group_del.add_argument('-i', '--id', nargs='*', type=int, help='Список ID задач, разделённых пробелом.')
        parser_del.set_defaults(func=self.delete)

        parser_edit = subparsers.add_parser('edit', help='Редактирование задачи одной командой.')
        parser_edit.add_argument('id', type=int, help='ID задачи.')
        parser_edit.add_argument('title', help='Название задачи.')
        parser_edit.add_argument('description', help='Описание задачи.')
        parser_edit.add_argument('category', help='Категория задачи.')
        parser_edit.add_argument('due_date', help='Срок выполнения задачи (дата).')
        parser_edit.add_argument(
            'priority',
            type=int,
            choices=(0, 1, 2),
            help=f'Приоритет задачи (число): 0 — {PRIORITIES[0]}, 1 — {PRIORITIES[1]}, 2 — {PRIORITIES[2]}.'
        )
        parser_edit.add_argument('status', type=int, choices=(0, 1),
                                 help=f'Статус задачи (число): 0 — {STATUSES[0]}, 1 — {STATUSES[1]}.')
        parser_edit.set_defaults(func=self.edit)

        parser_edit_inter = subparsers.add_parser('edit_inter', help='Редактирование задачи в интерактивном режиме.')
        parser_edit_inter.add_argument('id', type=int, help='ID задачи.')
        parser_edit_inter.set_defaults(func=self.edit_inter)

        parser_csv = subparsers.add_parser('csv', help='Экспорт списка задач в CSV-файл.')
        parser_csv.set_defaults(func=self.export_csv)

        parser_search = subparsers.add_parser('search', help='Поиск задачи.')
        parser_search.add_argument('-c', '--category', help='Категория задачи.')
        parser_search.add_argument(
            '-i', '--inner',
            action='store_true',
            help='Активатор режима INNER, когда поиск задачи производится с учётом каждого указанного параметра. '
                 'Если активатор опущен, то в результат поиска попадают задачи, '
                 'соответствующие хотя бы одному из параметров поиска.'
        )
        parser_search.add_argument(
            '-s', '--status',
            type=int,
            choices=(0, 1),
            help=f'Статус задачи для поиска (search) (число): 0 — {STATUSES[0]}, 1 — {STATUSES[1]}.'
        )
        parser_search.add_argument('-t', '--text', help='Фрагмент названия задачи или её описания.')
        parser_search.set_defaults(func=self.search)

        parser.add_argument('--version', action='version', version=VERSION)
        return parser

    def _load_tasks(self):
        """
        Загрузка списка задач из JSON-файла.
        """
        if os.path.exists(TASKS_JSON):
            with open(TASKS_JSON, 'r', encoding='utf8') as file:
                temp = json.load(file)
            if temp:
                temp = sorted(temp, key=lambda d: d['id'])  # Сортировка по ID.
                for task in temp:
                    p = task['priority']
                    if not isinstance(p, int) or (isinstance(p, str) and not p.isdigit()):
                        if p == PRIORITIES[2]:
                            task['priority'] = 2
                        elif p == PRIORITIES[1]:
                            task['priority'] = 1
                        elif p == PRIORITIES[0]:
                            task['priority'] = 0
                    elif isinstance(p, str) and p.isdigit():
                        task['priority'] = int(p)
                    s = task['status']
                    if not isinstance(s, bool) or not isinstance(s, int) or (isinstance(s, str) and not s.isdigit()):
                        if s == STATUSES[1]:
                            task['status'] = True
                        else:
                            task['status'] = False
                    self.tasks.append(Task(**task))

    def _set_name_length(self, task: Task):
        """
        Установка новых длин строк-ячеек, если в новой строке таблицы они больше ранее установленных.
        :param task: Объект Task, выводимый в строку таблицы, ячейки которой будут сравниваться
            с ранее установленными длинами.
        """
        for key, item in vars(task).items():
            if key == 'id':
                x = len(f'{item}')
            elif key == 'status':
                x = len(STATUSES[item])
            elif key == 'priority':
                continue
            else:
                x = len(item)
            if self.name_length[key] < x:
                self.name_length[key] = x

    def _set_result(self, data: list[Task], caption: str = '', ignor: tuple = ()):
        """
        Формирование текста для вывода в консоль.
        :param data: Данные для вывода (список задач (Task)).
        :param caption: Заголовок.
        :param ignor: Кортеж игнорируемых столбцов при выводе таблицы. None — выводить все столбцы.
            Столбец ID выводится всегда.
        """
        # Ширина таблицы.
        width = sum(i for k, i in self.name_length.items() if k not in ignor)
        width += 3 * (len(self.name_length) - len(ignor) - 1) + 1
        # Заголовок таблицы.
        self.result += f'{'-' * width}\n'
        self.result += f'{caption:^{width}}\n'
        self.result += f'{'—' * width}\n'
        # Заголовки столбцов таблицы.
        self.result += f'{HEADS['id']:^{self.name_length['id']}}'
        for key, item in self.name_length.items():
            if key != 'id' and key not in ignor:
                self.result += f' | {HEADS[key]:^{item}}'
        self.result += f'\n{'—' * width}'
        # Данные.
        # al — выравнивание в ячейках.
        al = dict(title='<', description='<', category='^', due_date='^', priority='^', status='^')
        for task in data:
            self.result += f'\n{task.id:>{self.name_length['id']}} '
            for cell in ('title', 'description', 'category', 'due_date', 'priority', 'status'):
                if cell not in ignor:
                    c = STATUSES[task.status] if cell == 'status' else getattr(task, cell)
                    self.result += f'| {c:{al[cell]}{self.name_length[cell]}} '
        self.result += f'\n{'—' * width}'

    def _save_json(self):
        """
        Сохранение списка задач в JSON-файл.
        """
        with open(TASKS_JSON, 'w') as file:
            json.dump([vars(task) for task in self.tasks], file, indent=4)

    def add(self, args: argparse.Namespace) -> str:
        """
        Добавление задачи одной командой.
        :param args: Аргументы из командной строки (title, description, category, due_date, priority).
        :return: Отчёт.
        """
        try:
            date = date_parser.parse(args.due_date).strftime('%Y-%m-%d')
        except ValueError:
            return 'Ошибка в введённых данных! Проверьте дату срока выполнения.\n'
        else:
            self.tasks.append(Task(args.title, args.description, args.category, date, args.priority))
            cnt = len(self.tasks)
            return f'Задача «{args.title}» добавлена. Присвоен ID {self.tasks[cnt - 1].id}.\n'

    def add_inter(self, args: argparse.Namespace) -> str:
        """
        Добавление задачи в интерактивном режиме.
        :param args: Аргументы из командной строки.
        :return: Отчёт.
        """
        cnc = False  # Флаг отмены.
        task = {}
        print('Добавление задачи\nВведите соответствующие данные или команду cancel для отмены добавления задачи.')
        for head in ('title', 'description', 'category', 'due_date', 'priority'):
            if head == 'due_date':
                while True:
                    task[head] = input(f'{HEADS[head]} (дата): ')
                    if task[head] == 'cancel':
                        cnc = True
                        break
                    try:
                        task[head] = date_parser.parse(task[head]).strftime('%Y-%m-%d')
                    except ValueError:
                        print('Ошибка!')
                    else:
                        break
            elif head == 'priority':
                s = 'Введите целое число от 0 до 2:\n'
                for n, p in enumerate(PRIORITIES):
                    s += f'{n} — {p}\n'
                while True:
                    task[head] = input(f'{s}{HEADS[head]}: ')
                    if task[head] == 'cancel':
                        cnc = True
                        break
                    try:
                        task[head] = int(task[head])
                        if task[head] not in (0, 1, 2):
                            raise ValueError
                    except ValueError:
                        print('Ошибка!')
                    else:
                        break
            else:
                while True:
                    task[head] = input(f'{HEADS[head]}: ')
                    if len(task[head]):
                        break
                    print('Ошибка!')
            if cnc or task[head] == 'cancel':
                return 'Добавление задачи отменено.'
        self.tasks.append(Task(**task))
        cnt = len(self.tasks)
        return f'Задача «{task['title']}» добавлена. Присвоен ID {self.tasks[cnt - 1].id}.\n'

    def completed(self, args: argparse.Namespace) -> str:
        """
        Отметка задачи как выполненной.
        :param args: Аргументы из командной строки (id).
        :return: Отчёт.
        """
        res = ''
        for i in args.id:
            for t in range(len(self.tasks)):
                if self.tasks[t].id == i:
                    self.tasks[t].status = True
                    res += f'Задача «{self.tasks[t].title}» отмечена как «{STATUSES[1]}».\n'
                    break
            else:
                res += f'Задача с ID {i} не найдена.\n'
        return res

    def current(self, args: argparse.Namespace) -> str:
        """
        Вывод всех текущих задач.
        :return: Таблица текстом.
        """
        data = []  # Будущий результат поиска.
        for task in self.tasks:
            if not task.status:
                data.append(task)
                self._set_name_length(task)
        self._set_result(data, 'Текущие задачи', ('status',))
        return self.result

    def delete(self, args: argparse.Namespace) -> str:
        """
        Удаление задачи по ID или категории.
        :param args: Аргументы из командной строки (category, id (списки)).
        :return: Отчёт.
        """
        res = ''
        deli = []  # Список индексов удаляемых задач из списка задач.
        if args.id:
            for i in args.id:
                for t in range(len(self.tasks)):
                    if self.tasks[t].id == i:
                        deli.append(t)
                        res += f'Задача «{self.tasks[t].title}» удалена. (ID {i}.)\n'
                        break
                else:
                    res += f'Задача с ID {i} не найдена.\n'
        else:
            for i in args.category:
                c = False  # Флаг обнаружения задачи с категорией.
                for t in range(len(self.tasks)):
                    if self.tasks[t].category.lower() == i.lower():
                        c = True
                        deli.append(t)
                        res += f'Задача «{self.tasks[t].title}» удалена. (Категория «{self.tasks[t].category}».)\n'
                if not c:
                    res += f'Задача с категорией «{i}» не найдена.\n'
        for i in deli:
            self.tasks.pop(i)
        return res

    def edit(self, args: argparse.Namespace) -> str:
        """
        Редактирование задачи одной командой.
        :param args: Аргументы из командной строки (id, title, description, category, due_date, priority, status).
        :return: Отчёт.
        """
        for task in self.tasks:
            if task.id == args.id:
                try:
                    date = date_parser.parse(args.due_date).strftime('%Y-%m-%d')
                    status = bool(args.status)
                except ValueError:
                    return 'Ошибка в введённых данных! Проверьте дату срока выполнения и статус.\n'
                else:
                    task.title = args.title
                    task.description = args.description
                    task.category = args.category
                    task.due_date = date
                    task.priority = PRIORITIES[args.priority]
                    task.status = bool(status)
                    return f'Задача с ID {args.id} изменена.\n'
        return f'Задача с ID {args.id} не найдена.\n'

    def edit_inter(self, args: argparse.Namespace):
        """
        Редактирование задачи в интерактивном режиме.
        :param args: Аргументы из командной строки (id).
        """
        for task in self.tasks:
            if task.id == args.id:
                cnc = False  # Флаг отмены.
                print('Редактирование задачи')
                print('Введите соответствующие данные или команду cancel для отмены редактирования задачи.')
                for head in ('title', 'description', 'category', 'due_date', 'priority', 'status'):
                    print(f'{HEADS[head]}{' (дата)' if head == 'due_date' else ''}: {getattr(task, head)}')
                    if head == 'priority':
                        s = 'Введите целое число от 0 до 2:'
                        for n, p in enumerate(PRIORITIES):
                            s += f'\n{n} — {p}'
                        print(s)
                    elif head == 'status':
                        s = 'Введите 0 или 1:'
                        for n, p in enumerate(STATUSES):
                            s += f'\n{n} — {p}'
                        print(s)
                    t = input('Заменить на: ')
                    if t == 'cancel':
                        cnc = True
                    if head == 'due_date':
                        while True:
                            try:
                                t = date_parser.parse(t).strftime('%Y-%m-%d')
                            except ValueError:
                                t = input(f'Ошибка!\n{getattr(task, head)} заменить на: ')
                                if t == 'cancel':
                                    cnc = True
                                    break
                            else:
                                break
                    elif head == 'priority':
                        while True:
                            try:
                                t = int(t)
                                if t not in (0, 1, 2):
                                    raise ValueError
                            except ValueError:
                                t = input('Ошибка!\nЗаменить на: ')
                                if t == 'cancel':
                                    cnc = True
                                    break
                            else:
                                t = PRIORITIES[t]
                                break
                    elif head == 'status':
                        while True:
                            try:
                                t = bool(t)
                            except ValueError:
                                t = input('Ошибка!\nЗаменить на: ')
                                if t == 'cancel':
                                    cnc = True
                                    break
                            else:
                                break
                    else:
                        while True:
                            if len(t):
                                break
                            t = input('Ошибка!\nЗаменить на: ')
                            if t == 'cancel':
                                cnc = True
                                break
                    if cnc:
                        return 'Редактирование задачи отменено.'
                    setattr(task, head, t)
                break
        return f'Задача с ID {args.id} не найдена.\n'

    def search(self, args: argparse.Namespace) -> str:
        """
        Поиск задачи по переданному фрагменту названия, фрагменту описания, категории или статусу.
        :param args: Аргументы из командной строки (category, status, text).
        :return: Таблица текстом или отчёт об отрицательном результате.
        """
        res = []
        for task in self.tasks:
            if args.inner:
                if args.text and args.text not in task:
                    continue
                elif args.category and args.category not in task.category:
                    continue
                elif args.status is not None and (bool(args.status) != task.status):
                    continue
                else:
                    res.append(task)
                    self._set_name_length(task)
            elif (
                (args.text and args.text in task) or
                (args.category and args.category in task.category) or
                (args.status is not None and (bool(args.status) == task.status))
            ):
                res.append(task)
                self._set_name_length(task)
        if len(res):
            self._set_result(res, 'Результат поиска')
            return self.result
        else:
            return 'Нет задач, соответствующих параметрам поиска.\n'

    def export_csv(self, args: argparse.Namespace) -> str:
        """
        Сохранение списка задач в CSV-файл.
        :return: Отчёт.
        """
        fn = ('id', 'title', 'description', 'category', 'due_date', 'priority', 'status')
        with open(TASKS_CSV, 'w', encoding='utf8') as file:
            csv_writer = csv.DictWriter(file, fn, lineterminator='\n')
            csv_writer.writeheader()
            csv_writer.writerows(vars(task) for task in self.tasks)
        return f'Смотрите файл {TASKS_CSV}.'

    def run(self):
        """
        Запуск парсера команды, выполнение команды и сохранение изменений списка задач в JSON-файле.
        """
        try:
            args = self.parser.parse_args()
        except:
            pass
            # Можно вывести сообщение об ошибке (отсутствует обязательный позиционный аргумент (команда)),
            # но оно выведется и при выводе справки (--help) или версии (--version).
        else:
            print(args.func(args))
            self._save_json()


if __name__ == '__main__':
    tm = TaskManager()
    tm.run()
