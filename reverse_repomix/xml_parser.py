#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import base64
import os
import json
import re
from pathlib import Path

class RepomixXmlParser:
    """Парсер для XML-файлов созданных repomix."""
    
    def __init__(self, xml_file, verbose=False):
        """
        Инициализация парсера.
        
        :param xml_file: Путь к XML файлу
        :param verbose: Включить подробный вывод
        """
        self.xml_file = xml_file
        self.verbose = verbose
        self.root = None
        self.metadata = {}
        self.format_type = "unknown"  # Формат файла: "project", "repomix", "unknown"
        self.file_paths = []
        
    def parse(self):
        """Разбирает XML файл."""
        try:
            # Сначала попробуем прочитать файл как обычный XML
            try:
                tree = ET.parse(self.xml_file)
                self.root = tree.getroot()
                
                # Определяем формат XML (original/project или repomix)
                if self.root.tag == 'project':
                    self.format_type = "project"
                    # Извлекаем метаданные проекта, если они есть
                    metadata_elem = self.root.find('./metadata')
                    if metadata_elem is not None:
                        for child in metadata_elem:
                            self.metadata[child.tag] = child.text
                elif self.root.tag == 'repomix':
                    self.format_type = "repomix"
                    # Извлекаем метаданные из формата repomix
                    file_summary = self.root.find('./file_summary')
                    if file_summary is not None:
                        for elem in file_summary:
                            if elem.tag != 'additional_info':
                                self.metadata[elem.tag] = elem.text
                else:
                    # Пробуем найти файлы в любом формате
                    if len(self.root.findall('.//file')) > 0:
                        self.format_type = "files_only"
            except ET.ParseError:
                # Если не удалось разобрать как XML, попробуем прочитать как текст и выделить файлы
                self.format_type = "plain_text"
                self._parse_plain_text()
                    
            if self.verbose:
                print(f"Формат XML файла: {self.format_type}")
                print(f"Метаданные проекта: {self.metadata}")
                
            return True
        except Exception as e:
            print(f"Ошибка при разборе XML файла: {e}")
            return False
    
    def _parse_plain_text(self):
        """Парсинг файла в текстовом формате с тегами."""
        try:
            with open(self.xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Извлекаем метаданные
            summary_match = re.search(r'<file_summary>(.*?)</file_summary>', content, re.DOTALL)
            if summary_match:
                summary = summary_match.group(1)
                
                # Извлекаем различные поля из сводки
                purpose_match = re.search(r'<purpose>(.*?)</purpose>', summary, re.DOTALL)
                if purpose_match:
                    self.metadata['purpose'] = purpose_match.group(1).strip()
                    
                notes_match = re.search(r'<notes>(.*?)</notes>', summary, re.DOTALL)
                if notes_match:
                    self.metadata['notes'] = notes_match.group(1).strip()
                
                # Другие метаданные при необходимости
                
            # Извлекаем все файлы с помощью регулярных выражений
            file_matches = re.finditer(r'<file path="([^"]+)">(.*?)</file>', content, re.DOTALL)
            for match in file_matches:
                path = match.group(1)
                content = match.group(2)
                self.file_paths.append((path, content))
                
            # Извлекаем структуру директорий
            dir_structure_match = re.search(r'<directory_structure>(.*?)</directory_structure>', content, re.DOTALL)
            if dir_structure_match:
                self.metadata['directory_structure'] = dir_structure_match.group(1).strip()
                
        except Exception as e:
            print(f"Ошибка при обработке текстового файла: {e}")
            
    def extract_files(self, output_dir):
        """
        Извлекает все файлы из XML в указанную директорию.
        
        :param output_dir: Выходная директория
        :return: Количество восстановленных файлов
        """
        if self.root is None and not self.file_paths and self.format_type != "plain_text":
            if not self.parse():
                return 0
                
        file_count = 0
        
        # Обработка в зависимости от формата
        if self.format_type == "plain_text":
            file_count = self._extract_files_from_plain_text(output_dir)
        else:
            # Определяем xpath для поиска файлов в зависимости от формата
            xpath = ".//file"
            if self.format_type == "project":
                xpath = ".//files/file"
            elif self.format_type == "repomix":
                xpath = ".//files/file"
            
            # Перебираем все элементы file в XML
            for file_elem in self.root.findall(xpath):
                try:
                    # Получаем атрибуты файла
                    if self.format_type == "repomix":
                        # В формате repomix path - это атрибут
                        file_path = file_elem.get('@_path') or file_elem.get('path')
                        content = file_elem.text
                    else:
                        # В других форматах path - это атрибут, а содержимое - текст элемента
                        file_path = file_elem.get('path')
                        content = file_elem.text
                    
                    if self._process_file(file_path, content, output_dir, file_elem):
                        file_count += 1
                
                except Exception as e:
                    print(f"Ошибка при обработке файла: {e}")
        
        return file_count
    
    def _extract_files_from_plain_text(self, output_dir):
        """Извлекает файлы из текстового формата."""
        file_count = 0
        
        for file_path, content in self.file_paths:
            try:
                if self._process_file(file_path, content, output_dir):
                    file_count += 1
            except Exception as e:
                print(f"Ошибка при обработке файла {file_path}: {e}")
                
        return file_count
    
    def _process_file(self, file_path, content, output_dir, file_elem=None):
        """Обрабатывает отдельный файл и сохраняет его в выходную директорию."""
        if not file_path:
            if self.verbose:
                print("Предупреждение: файл без пути")
            return False
            
        # Проверяем, не являются ли это специальным файлом, который нужно пропустить
        if file_path.startswith('.git/'):
            if self.verbose:
                print(f"Пропускаем служебный файл: {file_path}")
            return False
            
        # Полный путь к файлу
        full_path = os.path.join(output_dir, file_path)
        
        # Создаем родительские директории
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Получаем дополнительные атрибуты
        file_type = ""
        file_size = ""
        file_mode = ""
        binary = False
        encoding = "utf-8"
        
        if file_elem is not None:
            # Получаем атрибуты из элемента XML
            file_type = file_elem.get('type', '')
            file_size = file_elem.get('size', '')
            file_mode = file_elem.get('mode', '')
            binary = file_elem.get('binary', 'false').lower() == 'true'
            encoding = file_elem.get('encoding', 'base64' if binary else 'utf-8')
        
        # Очищаем содержимое от начальных/конечных пробелов
        if content:
            content = content.strip()
        else:
            content = ""
        
        # Декодируем содержимое
        if encoding.lower() == 'base64':
            try:
                # Удаляем лишние пробелы и переносы строк для правильного декодирования base64
                content = re.sub(r'\s+', '', content)
                file_content = base64.b64decode(content)
                mode = 'wb'  # Бинарный режим для base64
            except Exception as e:
                print(f"Ошибка декодирования base64 для {file_path}: {e}")
                return False
        else:
            # Предполагаем, что это текстовый файл
            file_content = content.encode('utf-8')
            mode = 'wb'
        
        # Записываем содержимое в файл
        with open(full_path, mode) as f:
            f.write(file_content)
        
        # Если есть информация о правах доступа, устанавливаем их
        if file_mode and os.name != 'nt':  # Только для Unix-подобных систем
            try:
                mode_value = int(file_mode, 8)
                os.chmod(full_path, mode_value)
            except:
                if self.verbose:
                    print(f"Не удалось установить права доступа для {file_path}")
        
        if self.verbose:
            print(f"Восстановлен файл: {file_path} ({file_type}, {file_size} байт)")
        
        return True
            
    def get_project_structure(self):
        """
        Возвращает структуру проекта в виде словаря.
        
        :return: Словарь с иерархией файлов и директорий
        """
        if self.root is None and not self.file_paths:
            if not self.parse():
                return {}
        
        structure = {}
        
        if self.format_type == "plain_text":
            # Извлекаем структуру из сохраненного списка файлов
            for file_path, _ in self.file_paths:
                parts = file_path.split('/')
                current = structure
                
                # Строим иерархию директорий
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Это файл (последний элемент пути)
                        current[part] = {
                            'type': 'file',
                            'size': '',
                            'file_type': ''
                        }
                    else:  # Это директория
                        if part not in current:
                            current[part] = {}
                        current = current[part]
        else:
            # Определяем xpath для поиска файлов в зависимости от формата
            xpath = ".//file"
            if self.format_type == "project":
                xpath = ".//files/file"
            elif self.format_type == "repomix":
                xpath = ".//files/file"
            
            for file_elem in self.root.findall(xpath):
                if self.format_type == "repomix":
                    path = file_elem.get('@_path') or file_elem.get('path')
                else:
                    path = file_elem.get('path', '')
                    
                if not path:
                    continue
                    
                parts = path.split('/')
                current = structure
                
                # Строим иерархию директорий
                for i, part in enumerate(parts):
                    if i == len(parts) - 1:  # Это файл (последний элемент пути)
                        current[part] = {
                            'type': 'file',
                            'size': file_elem.get('size', ''),
                            'file_type': file_elem.get('type', '')
                        }
                    else:  # Это директория
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    
        return structure

    def save_project_structure(self, output_file):
        """
        Сохраняет структуру проекта в JSON-файл.
        
        :param output_file: Путь к файлу для сохранения
        :return: True в случае успеха, False в случае ошибки
        """
        structure = self.get_project_structure()
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(structure, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении структуры проекта: {e}")
            return False
            
    def extract_directory_structure(self):
        """
        Извлекает структуру директорий из XML.
        
        :return: Строка, представляющая структуру директорий
        """
        if self.root is None and self.format_type != "plain_text":
            if not self.parse():
                return ""
                
        # Ищем элемент структуры директорий
        dir_structure = ""
        
        if self.format_type == "plain_text":
            # Структура директорий уже должна быть в метаданных
            if 'directory_structure' in self.metadata:
                dir_structure = self.metadata['directory_structure']
        else:
            if self.format_type == "repomix":
                structure_elem = self.root.find('./directory_structure')
            else:
                structure_elem = self.root.find('./directory_structure')
                
            if structure_elem is not None and structure_elem.text:
                dir_structure = structure_elem.text.strip()
                
        return dir_structure 