import argparse
import sys
import xml.etree.ElementTree as ET
import urllib.request
import re

class CLI_App:
    def __init__(self, config_path):
        self.params = self.load_config(config_path)
        self.validate_params()
    
    def load_config(self, config_path):
        """Загрузка и парсинг XML конфигурации"""
        try:
            tree = ET.parse(config_path)
            root = tree.getroot()
            return {
                'package_name': root.findtext("package_name"),
                'repo_url': root.findtext("repo_url"),
                'test_mode': root.findtext("test_mode"),
                'version': root.findtext("version"),
                'max_depth': int(root.findtext("max_depth"))
            }
        except FileNotFoundError:
            raise Exception(f"Файл конфигурации '{config_path}' не найден.")
        except Exception as e:
            raise Exception(f"Ошибка чтения конфигурации: {e}")
    
    def validate_params(self):
        """Базовая валидация параметров"""
        test_mode = self.params['test_mode'].strip().lower()
        if test_mode not in {"true", "false", "0", "1"}:
            raise Exception("Параметр 'test_mode' должен быть 'true', 'false', '0' или '1'.")
        
        if self.params['max_depth'] < 1:
            raise Exception("Параметр 'max_depth' должен быть >= 1.")
    
    def fetch_cargo_toml(self, repo_url, version):
        """Загрузка Cargo.toml из GitHub репозитория"""
        if "github.com" not in repo_url:
            raise Exception("Поддерживаются только GitHub репозитории")
        
        match = re.search(r'github\.com/([^/]+/[^/]+)', repo_url)
        if not match:
            raise Exception(f"Некорректный GitHub URL: {repo_url}")
        
        repo_path = match.group(1).rstrip('/')
        
        for tag in (version, f"v{version}"):
            url = f"https://raw.githubusercontent.com/{repo_path}/{tag}/Cargo.toml"
            try:
                with urllib.request.urlopen(url, timeout=10) as resp:
                    if resp.status == 200:
                        return resp.read().decode('utf-8')
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise Exception(f"Ошибка HTTP {e.code}")
        
        raise Exception(f"Не удалось найти Cargo.toml для версии {version}")
    
    def extract_all_dependencies(self, cargo_toml):
        """Извлечение ВСЕХ зависимостей из Cargo.toml"""
        deps = []
        in_dep_section = False
        
        for line in cargo_toml.split('\n'):
            line = line.split('#')[0].strip()
            
            # Проверяем любую секцию зависимостей
            if any(line.startswith(s) for s in ['[dependencies', '[dev-dependencies', '[build-dependencies']):
                in_dep_section = True
                continue
            elif line.startswith('['):
                in_dep_section = False
                continue
            
            if in_dep_section and '=' in line:
                name, value = map(str.strip, line.split('=', 1))
                
                # Ищем версию
                version = None
                match = re.search(r'"([^"]+)"', value)
                if match:
                    version = re.sub(r'^[~^>=<!]*', '', match.group(1))
                elif '{' in value:
                    match = re.search(r'version\s*=\s*"([^"]+)"', value)
                    if match:
                        version = re.sub(r'^[~^>=<!]*', '', match.group(1))
                
                if version and name:
                    deps.append((name, version))
        
        return deps
    
    def show_dependencies(self):
        """Вывод всех прямых зависимостей"""
        pkg = self.params['package_name']
        repo = self.params['repo_url']
        ver = self.params['version']
        
        print(f"=== Зависимости пакета {pkg} версии {ver} ===")
        print(f"Репозиторий: {repo}")
        
        try:
            cargo_toml = self.fetch_cargo_toml(repo, ver)
            dependencies = self.extract_all_dependencies(cargo_toml)
            
            if not dependencies:
                print("\nНет зависимостей.")
                return
            
            print("\nПрямые зависимости:")
            print("-" * 50)
            for name, version in sorted(dependencies):
                print(f"{name} = {version}")
            print("-" * 50)
            print(f"Всего: {len(dependencies)} зависимостей")
            
        except Exception as e:
            print(f"\nОшибка: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Анализ зависимостей Rust пакетов (этап 2)"
    )
    parser.add_argument(
        "--config", "-c", default="config.xml",
        help="Путь к XML файлу конфигурации"
    )
    args = parser.parse_args()
    
    try:
        app = CLI_App(args.config)
        app.show_dependencies()
    except Exception as e:
        print(f"[ОШИБКА] {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()