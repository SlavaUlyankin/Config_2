import json
import sys
import os


def load_config(config_path: str) -> dict:
    """Загружает конфигурацию из JSON-файла."""
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"Конфигурационный файл не найден: {config_path}")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Некорректный JSON в файле {config_path}: {e}")


def validate_config(config: dict) -> None:
    """Проверяет наличие и корректность всех обязательных параметров."""
    required_keys = {
        "package_name": str,
        "repository_url": str,
        "repo_mode": str,
        "output_file": str,
        "max_depth": int,
        "filter_substring": str,
    }

    for key, expected_type in required_keys.items():
        if key not in config:
            raise KeyError(f"Отсутствует обязательный параметр: {key}")
        if not isinstance(config[key], expected_type):
            raise TypeError(
                f"Параметр '{key}' должен быть типа {expected_type.__name__}, "
                f"получено: {type(config[key]).__name__}"
            )

    # Дополнительные проверки
    if config["max_depth"] < 0:
        raise ValueError("max_depth не может быть отрицательным")
    if config["repo_mode"] not in ("remote", "local"):
        raise ValueError("repo_mode должен быть 'remote' или 'local'")


def print_config(config: dict) -> None:
    """Выводит все параметры конфигурации в формате ключ-значение."""
    print("Загруженные параметры конфигурации:")
    for key, value in config.items():
        print(f"{key}: {value}")


def main():
    config_path = "config.json"

    try:
        config = load_config(config_path)
        validate_config(config)
        print_config(config)
        print("\n Конфигурация успешно загружена и проверена.")
    except (FileNotFoundError, ValueError, KeyError, TypeError) as e:
        print(f" Ошибка конфигурации: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f" Непредвиденная ошибка: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
