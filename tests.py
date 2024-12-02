import pytest
from TaskManager import TaskManager

TEST = (
    '-' * 112 + '\n' + ' ' * 48 + 'Результат поиска' + ' ' * 48 + '\n' + '—' * 112 + '\n' +
    'ID | Название  |               Описание                |' +
    ' Категория | Срок выполнения | Приоритет |    Статус   \n' + '—' * 112 + '\n' +
    ' 2 | Тест edit | Тест редактирования задачи «Тест add» |' +
    '   Тест    |   2024-12-12    |  Средний  |  Выполнена   \n' + '—' * 112
)


@pytest.fixture()
def get_tm():
    return TaskManager()


def test_current(get_tm):
    args = get_tm.parser.parse_args(['current'])
    assert get_tm.current(args) == (
        '-' * 128 + '\n' + ' ' * 57 + 'Текущие задачи' + ' ' * 57 + '\n' + '—' * 128 +
        '\nID |        Название        |' + ' ' * 24 + 'Описание' + ' ' * 25 +
        '| Категория | Срок выполнения | Приоритет\n' + '—' * 128 + '\n' +
        ' 1 | Изучить основы FastAPI | Пройти документацию по FastAPI и создать простой проект |' +
        ' Обучение  |   2024-12-10    |  Высокий  \n' + '—' * 128
    )


def test_add(get_tm):
    args = get_tm.parser.parse_args(['add', 'Тест add', 'Тест добавления задачи', 'Тест', '2024-12-10', 0])
    assert get_tm.add(args) == 'Задача «Тест add» добавлена. Присвоен ID 2.\n'


def test_add_err(get_tm):
    args = get_tm.parser.parse_args(['add', 'Тест add', 'Тест добавления задачи', 'Тест', 'day', 0])
    assert get_tm.add(args) == 'Ошибка в введённых данных! Проверьте дату срока выполнения.\n'


def test_completed(get_tm):
    args = get_tm.parser.parse_args(['completed', '2'])
    assert get_tm.completed(args) == 'Задача «Тест add» отмечена как «Выполнена».\n'


def test_completed_err(get_tm):
    args = get_tm.parser.parse_args(['completed', '10000'])
    assert get_tm.completed(args) == 'Задача с ID 10000 не найдена.\n'


def test_edit(get_tm):
    args = get_tm.parser.parse_args([
        'edit', '2', 'Тест edit', 'Тест редактирования задачи «Тест add»', 'Тест', '2024-12-12', '1', '1'
    ])
    assert get_tm.edit(args) == 'Задача с ID 2 изменена.\n'


def test_edit_err_id(get_tm):
    args = get_tm.parser.parse_args([
        'edit', '10000', 'Тест edit', 'Тест редактирования задачи «Тест add»', 'Тест', '2024-12-12', '1', '1'
    ])
    assert get_tm.edit(args) == 'Задача с ID 10000 не найдена.\n'


def test_edit_err(get_tm):
    args = get_tm.parser.parse_args([
        'edit', '2', 'Тест edit', 'Тест редактирования задачи «Тест add»', 'Тест', 'day', '1', '1'
    ])
    assert get_tm.edit(args) == 'Ошибка в введённых данных! Проверьте дату срока выполнения и статус.\n'


def test_search_text(get_tm):
    args = get_tm.parser.parse_args(['search', '-t', 'Тест'])
    assert get_tm.search(args) == TEST


def test_search_category(get_tm):
    args = get_tm.parser.parse_args(['search', '-c', 'Тест'])
    assert get_tm.search(args) == TEST


def test_search_status(get_tm):
    args = get_tm.parser.parse_args(['search', '-s', '1'])
    assert get_tm.search(args) == TEST


def test_search_inner(get_tm):
    args = get_tm.parser.parse_args(['search', '-t', 'Тест', '-c', 'Тест', '-s', '1', '-i'])
    assert get_tm.search(args) == TEST


def test_search_no(get_tm):
    args = get_tm.parser.parse_args(['search', '-t', '"-v-"'])
    assert get_tm.search(args) == 'Нет задач, соответствующих параметрам поиска.\n'


def test_del_id(get_tm):
    args = get_tm.parser.parse_args(['del', '-i', '10000', '1'])
    assert get_tm.delete(args) == 'Задача с ID 10000 не найдена.\nЗадача «Изучить основы FastAPI» удалена. (ID 1.)\n'


def test_del_category(get_tm):
    args = get_tm.parser.parse_args(['del', '-c', ' -v- ', 'Тест'])
    assert get_tm.delete(args) == ('Задача с категорией « -v- » не найдена.\n'
                                   'Задача «Тест edit» удалена. (Категория «Тест».)\n')
