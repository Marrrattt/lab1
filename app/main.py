"""Лабораторная 1: безопасные параметры подключения к PostgreSQL."""

import getpass
import json
from pathlib import Path
import sys

import psycopg

CONFIG_PATH = Path(__file__).with_name("config.json")


def load_config(path=CONFIG_PATH):
    # Путь относительно программы, а не текущей папки терминала.
    with path.open(encoding="utf-8-sig") as file:
        config = json.load(file)
    expected = {"host", "port", "dbname", "connect_timeout"}
    if not isinstance(config, dict) or set(config) != expected:
        raise ValueError("В config.json нужны только host, port, dbname, connect_timeout.")
    for key in ("host", "dbname"):
        if not isinstance(config[key], str) or not config[key] or "\0" in config[key]:
            raise ValueError(f"Некорректное поле {key}.")
    for key, maximum in (("port", 65535), ("connect_timeout", 60)):
        if type(config[key]) is not int or not 1 <= config[key] <= maximum:
            raise ValueError(f"Поле {key} должно быть целым числом от 1 до {maximum}.")
    return config


def connection_params(config, username, password):
    if not username or not password:
        raise ValueError("Логин и пароль не должны быть пустыми.")
    if "\0" in username or "\0" in password:
        raise ValueError("Нулевой символ недопустим в логине и пароле.")
    # Не склеиваем DSN или URL. Драйвер сам экранирует значения параметров.
    return {**config, "user": username, "password": password}


def fetch_version(config, username, password):
    with psycopg.connect(**connection_params(config, username, password)) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION();")
            return cursor.fetchone()[0]


def main():
    try:
        config = load_config()
        username = input("Логин PostgreSQL: ")
        password = getpass.getpass("Пароль PostgreSQL (ввод скрыт): ")
        version = fetch_version(config, username, password)
    except (OSError, ValueError) as error:
        print(f"Ошибка настроек или ввода: {error}", file=sys.stderr)
        return 1
    except psycopg.OperationalError:
        print("Не удалось подключиться. Проверьте логин, пароль, config.json и запуск БД.", file=sys.stderr)
        return 1
    except psycopg.Error:
        print("Ошибка выполнения запроса PostgreSQL.", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("\nВвод отменён.", file=sys.stderr)
        return 1
    print("Подключение успешно. Результат SELECT VERSION():")
    print(version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
