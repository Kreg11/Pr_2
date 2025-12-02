import argparse
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

class CLI_App:
    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.params = {}
        self.load_xml_config()
        self.validate_params()

    def load_xml_config(self):
        """Загрузка и парсинг XML конфигурационного файла"""
        if not self.config_path.exists():
            raise Exception(f"Файл конфигурации '{self.config_path}' не найден.")

        try:
            tree = ET.parse(self.config_path)
            root = tree.getroot()
            
            # Извлекаем параметры из XML
            self.params["package_name"] = root.findtext("package_name")
            self.params["repo_url"] = root.findtext("repo_url")
            self.params["test_mode"] = root.findtext("test_mode")
            self.params["version"] = root.findtext("version")
            self.params["max_depth"] = root.findtext("max_depth")
            
        except ET.ParseError as e:
            raise Exception(f"Ошибка парсинга XML: {e}")
        except Exception as e:
            raise Exception(f"Ошибка чтения конфигурации: {e}")

    def validate_params(self):
        required_fields = [
            "package_name",
            "repo_url", 
            "test_mode",
            "version",
            "max_depth"
        ]

        # Проверка наличия всех обязательных параметров
        for field in required_fields:
            if field not in self.params or self.params[field] is None:
                raise Exception(f"Отсутствует обязательный параметр: '{field}'")

        # Валидация имени пакета
        if not isinstance(self.params["package_name"], str) or not self.params["package_name"].strip():
            raise Exception("Параметр 'package_name' должен быть непустой строкой.")

        # Валидация URL/пути репозитория
        if not isinstance(self.params["repo_url"], str) or not self.params["repo_url"].strip():
            raise Exception("Параметр 'repo_url' должен быть непустой строкой.")
        
        # Валидация режима тестирования
        test_mode_str = self.params["test_mode"].strip().lower()
        if test_mode_str not in ["true", "false", "0", "1"]:
            raise Exception("Параметр 'test_mode' должен быть 'true', 'false', '0' или '1'.")
        
        # Конвертация в булево значение
        self.params["test_mode"] = test_mode_str in ["true", "1"]

        # Валидация версии
        if not isinstance(self.params["version"], str) or not self.params["version"].strip():
            raise Exception("Параметр 'version' должен быть непустой строкой.")

        # Валидация максимальной глубины
        try:
            self.params["max_depth"] = int(self.params["max_depth"])
            if self.params["max_depth"] < 1:
                raise ValueError("max_depth должен быть >= 1")
        except ValueError as e:
            raise Exception(f"Параметр 'max_depth' должен быть целым числом >= 1. Ошибка: {e}")

    def print_params(self):
        """Вывод параметров в формате ключ-значение"""
        print("=== Настройки приложения ===")
        print(f"Имя анализируемого пакета: {self.params['package_name']}")
        print(f"URL/путь репозитория: {self.params['repo_url']}")
        print(f"Режим работы с тестовым репозиторием: {self.params['test_mode']}")
        print(f"Версия пакета: {self.params['version']}")
        print(f"Максимальная глубина анализа: {self.params['max_depth']}")
        print("============================")


def main():
    parser = argparse.ArgumentParser(
        description="CLI-приложение для анализа зависимостей (этап 1: минимальный прототип с XML-конфигурацией)."
    )
    parser.add_argument(
        "--config", 
        "-c", 
        default="config.xml", 
        help="Путь к XML файлу конфигурации (по умолчанию: config.xml)"
    )
    args = parser.parse_args()

    try:
        cli = CLI_App(args.config)
        cli.print_params()
    except Exception as e:
        print(f"[ОШИБКА КОНФИГУРАЦИИ] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()