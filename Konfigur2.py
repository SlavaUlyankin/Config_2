import json
import sys
import os
import urllib.request
import urllib.parse
from xml.etree import ElementTree as ET

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

    if config["max_depth"] < 0:
        raise ValueError("max_depth не может быть отрицательным")
    if config["repo_mode"] not in ("remote", "local"):
        raise ValueError("repo_mode должен быть 'remote' или 'local'")


def fetch_package_dependencies(package_name: str, version: str, base_url: str) -> list:
    """
    Запрашивает прямые зависимости пакета из NuGet v2 API.
    Возвращает список словарей: [{"name": "...", "version": "...", "target": "..."}]
    """
    
    safe_name = urllib.parse.quote(package_name, safe='')
    safe_version = urllib.parse.quote(version, safe='')

    
    query = f"Id eq '{safe_name}' and Version eq '{safe_version}'"
    encoded_query = urllib.parse.quote(query, safe='')
    url = f"{base_url.rstrip('/')}/Packages()?$filter={encoded_query}"

    try:
        with urllib.request.urlopen(url) as response:
            xml_data = response.read()
    except Exception as e:
        raise RuntimeError(f"Не удалось загрузить данные пакета из {url}: {e}")

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError as e:
        raise RuntimeError(f"Не удалось распарсить XML-ответ: {e}")

   
    ns = {'d': 'http://schemas.microsoft.com/ado/2007/08/dataservices'}

    dependencies_entries = root.findall('.//d:Dependencies', ns)
    if not dependencies_entries:
        return []  

    deps_text = dependencies_entries[0].text
    if not deps_text or not deps_text.strip():
        return []  

    
    dependencies = []
    for dep in deps_text.split('|'):
        parts = dep.split(':', 2) 
        if len(parts) < 2:
            continue  
        name = parts[0]
        version_req = parts[1]
        target = parts[2] if len(parts) > 2 else ""
        dependencies.append({
            "name": name,
            "version": version_req,
            "target": target
        })

    return dependencies

def print_direct_dependencies(dependencies: list) -> None:
    if not dependencies:
        print("Прямые зависимости отсутствуют.")
        return

    print("Прямые зависимости:")
    for dep in dependencies:
        line = f"• {dep['name']} ({dep['version']})"
        if dep['target']:
            line += f" [целевая платформа: {dep['target']}]"
        print(line)

def main():
    config_path = "config.json"

    try:
        config = load_config(config_path)
        validate_config(config)
        
        if config["repo_mode"] == "remote":
            deps = fetch_package_dependencies(
                package_name=config["package_name"],
                version=config["package_version"],
                base_url=config["repository_url"]
            )
            print_direct_dependencies(deps)
        else:
            raise NotImplementedError("Локальный режим не поддерживается")

        
    except (FileNotFoundError, ValueError, KeyError, TypeError) as e:
        print(f" Ошибка конфигурации: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f" Непредвиденная ошибка: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
