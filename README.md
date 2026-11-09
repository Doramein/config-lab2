# Инструмент визуализации графа зависимостей (Alpine Linux apk)

Практическая работа №2 по дисциплине «Конфигурационное управление».
**Вариант №20**.

## 1. Общее описание
Проект представляет собой CLI-приложение для анализа и визуализации графа
зависимостей пакетов пакетного менеджера **Alpine Linux (`apk`)**.
Инструмент извлекает зависимости напрямую из индекса пакетов репозитория
без использования сторонних библиотек и пакетных менеджеров, строит транзитивный
граф зависимостей и формирует графическое представление.

## 2. Описание функций и настроек

Конфигурация задается в формате **XML** (`config.xml`).

Параметры конфигурации:
- `package_name`: Имя анализируемого пакета (например, `curl`).
- `repo_url`: URL-адрес репозитория Alpine Linux или путь к тестовому файлу.
- `test_mode`: Режим работы с тестовым репозиторием (`true` / `false`).
- `package_version`: Требуемая версия пакета (например, `8.11.1-r0`).
- `output_file`: Имя генерируемого файла диаграммы (например, `graph.svg`).
- `max_depth`: Максимальная глубина анализа транзитивных зависимостей (целое число >= 1).
- `filter_substring`: Подстрока для исключения пакетов из анализа (например, `so:`).

Пример `config.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<config>
    <package_name>curl</package_name>
    <repo_url>https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64</repo_url>
    <test_mode>false</test_mode>
    <package_version>8.11.1-r0</package_version>
    <output_file>graph.svg</output_file>
    <max_depth>3</max_depth>
    <filter_substring>so:</filter_substring>
</config>
```

## 3. Описание команд для сборки проекта и запуска тестов

Проект разработан на языке Python 3 и не требует сторонних зависимостей.

### Запуск приложения:
- На Windows:
  ```cmd
  run.bat --config config.xml --stage 1
  ```
- На Linux/macOS:
  ```bash
  chmod +x run.sh
  ./run.sh --config config.xml --stage 1
  ```
- Или напрямую через Python:
  ```bash
  python -m src.main --config config.xml --stage 1
  ```

### Запуск тестов:
```bash
python -m unittest discover -s tests -v
```

Тесты проверяют:
- Корректность разбора конфигурационного файла XML.
- Обработку ошибок для всех параметров (отсутствие тегов, неверные типы, пустые значения).
- Соответствие правилам оформления кода (длина строк <= 80, функции <= 40 строк, docstrings).

## 4. Примеры использования

### Этап 1: Вывод настроек приложения
Запуск:
```cmd
python -m src.main --config config.xml --stage 1
```

Вывод:
```text
package_name: curl
repo_url: https://dl-cdn.alpinelinux.org/alpine/v3.20/main/x86_64
test_mode: false
package_version: 8.11.1-r0
output_file: graph.svg
max_depth: 3
filter_substring: so:
```
