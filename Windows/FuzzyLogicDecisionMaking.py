from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QCheckBox, QPushButton, QScrollArea,
                            QLabel, QLineEdit, QGroupBox, QSizePolicy, QDialog,
                            QGridLayout, QFrame, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QSpinBox, QDoubleSpinBox, QMessageBox,
                            QFileDialog, QButtonGroup, QRadioButton, QComboBox)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QIcon
import pandas as pd
import numpy as np
import csv

class FLTaskWindow(QDialog):
    COLUMN_WIDTH = 120
    ROW_HEIGHT = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Принятие решений при помощи нечеткой логики")
        self.setModal(True)
        
        # Переменные для хранения данных
        self.task_type = None
        self.num_alternatives = 0
        self.num_criteria = 0
        
        self.criteria_names = []
        self.alternative_names = []
        self.criteria_weights = {}
        
        # Данные таблицы
        self.table_data = None
        
        # Основная настройка окна
        self.setMinimumSize(900, 600)
        self.setStyleSheet("""
            QDialog {
                background: #f8f9fa;
            }
            QLabel {
                color: #2c3e50;
                font-weight: 500;
                font-size: 10px;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                background: white;
                min-height: 20px;
                max-height: 25px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
                border-color: #3498db;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
                border: none;
                border-radius: 6px;
                color: white;
                padding: 8px 16px;
                font-weight: 600;
                font-size: 11px;
                margin: 5px;
                min-width: 80px;
                max-height: 30px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2980b9, stop: 1 #2471a3);
            }
            QTableWidget {
                gridline-color: #dee2e6;
                border: 1px solid #ced4da;
                border-radius: 6px;
                background: white;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QGroupBox {
                font-weight: bold;
                color: #34495e;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                background: white;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
                font-size: 12px;
            }
        """)
        self.setWindowIcon(QIcon('icon.png'))

        # Основной layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Заголовок
        title_label = QLabel("Принятие решений при помощи нечеткой логики")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            color: white;
            padding: 10px;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 #3498db, stop: 1 #2980b9);
            border-radius: 6px;
            margin: 5px;
        """)
        main_layout.addWidget(title_label)
        
        # Создаем скроллируемую область
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Виджет для содержимого скролла
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # Таймер для обновления размеров
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_window_size)
        
        # Инициализация интерфейса
        self.current_step = 1
        self.init_step1()

    def setup_table_appearance(self, table, min_column_width=COLUMN_WIDTH, min_row_height=ROW_HEIGHT):
        """
        Настраивает внешний вид таблицы: растягивает столбцы на всю ширину
        """
        # Устанавливаем минимальную высоту строк
        vertical_header = table.verticalHeader()
        vertical_header.setDefaultSectionSize(min_row_height)
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        
        # ОТКЛЮЧАЕМ горизонтальную прокрутку
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Включаем растягивание всех столбцов на всю ширину таблицы
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Устанавливаем минимальную ширину для столбцов (чтобы не сжимались слишком сильно)
        header.setMinimumSectionSize(min_column_width)
        
        # Включаем альтернативные цвета строк для лучшей читаемости
        table.setAlternatingRowColors(True)
        
        # Отключаем выделение всей строки
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectItems)

    def deactivate_group(self, group_widget):
        """Деактивирует все элементы в группе"""
        # Деактивируем все дочерние элементы
        for child in group_widget.findChildren((QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QTableWidget, QCheckBox, QRadioButton, QComboBox)):
            child.setEnabled(False)
        
        # Также деактивируем саму группу (меняем стиль)
        group_widget.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #95a5a6;
                border: 1px solid #d5dbdb;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 15px;
                background: #f8f9fa;
                font-size: 11px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #95a5a6;
                font-size: 12px;
            }
        """)

    def init_step1(self):
        """Первый шаг: выбор типа задачи"""
        self.step1_group = QGroupBox("Шаг 1: Выбор типа задачи")
        step1_layout = QVBoxLayout(self.step1_group)
        step1_layout.setSpacing(15)
        step1_layout.setContentsMargins(15, 15, 15, 15)
        
        # Комбобокс для выбора типа задачи
        type_layout = QHBoxLayout()
        type_label = QLabel("Тип задачи:")
        type_label.setMinimumWidth(100)
        
        self.task_type_combo = QComboBox()
        self.task_type_combo.addItems([
            "Принятие решения в условиях неаддитивности критериев",
            "Принятие решения в условиях аддитивности критериев", 
            "Принятие решения на основе нечетких систем"
        ])
        self.task_type_combo.setMinimumWidth(400)
        
        type_layout.addStretch()
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.task_type_combo)
        type_layout.addStretch()
        step1_layout.addLayout(type_layout)
        
        # Кнопка Далее
        self.next_btn1 = QPushButton("Далее")
        self.next_btn1.clicked.connect(self.go_to_step2)
        step1_layout.addWidget(self.next_btn1, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step1_group)
        self.update_window_size()

    def go_to_step2(self):
        """Переход ко второму шагу"""
        # Сохраняем тип задачи
        self.task_type = self.task_type_combo.currentText()
        
        # Деактивируем первый шаг
        self.deactivate_group(self.step1_group)
        self.next_btn1.setEnabled(False)

        # Инициализируем второй шаг в зависимости от типа задачи
        if self.task_type == "Принятие решения в условиях неаддитивности критериев":
            self.init_step2()
        elif self.task_type == "Принятие решения в условиях аддитивности критериев":
            self.init_step2_additive()
        elif self.task_type == "Принятие решения на основе нечетких систем":
            self.init_step2_fuzzy_systems()
        
        self.current_step = 2
        
        # ОБНОВЛЯЕМ РАЗМЕР ОКНА
        self.schedule_resize_update()

    """Принятие решения в условиях неаддитивности критериев"""
    def init_step2(self):
        """Второй шаг: ввод количества альтернатив и критериев"""
        self.step2_group = QGroupBox("Шаг 2: Основные параметры")
        step2_layout = QGridLayout(self.step2_group)
        step2_layout.setSpacing(15)
        step2_layout.setContentsMargins(15, 15, 15, 15)
        
        # Создаем элементы ввода
        labels = [
            "Количество альтернатив:",
            "Количество критериев:"
        ]
        
        default_values = [5, 6]
        self.step2_inputs = []
        
        for i, (label_text, default_val) in enumerate(zip(labels, default_values)):
            label = QLabel(label_text)
            label.setMinimumWidth(150)
            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(20)
            spinbox.setValue(default_val)
            spinbox.setMinimumWidth(80)
            
            step2_layout.addWidget(label, 0, 2*i)
            step2_layout.addWidget(spinbox, 0, 2*i+1)
            self.step2_inputs.append(spinbox)
        
        # Кнопка Далее
        self.next_btn2 = QPushButton("Далее")
        self.next_btn2.clicked.connect(self.go_to_step3)
        step2_layout.addWidget(self.next_btn2, 1, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step2_group)
        self.update_window_size()

    def go_to_step3(self):
        """Переход к третьему шагу"""
        # Сохраняем значения
        self.num_alternatives = self.step2_inputs[0].value()
        self.num_criteria = self.step2_inputs[1].value()
        
        # Деактивируем второй шаг
        self.deactivate_group(self.step2_group)
        self.next_btn2.setEnabled(False)
        
        # Инициализируем третий шаг
        self.init_step3()
        self.current_step = 3
        
        # ОБНОВЛЯЕМ РАЗМЕР ОКНА
        self.schedule_resize_update()

    def init_step3(self):
        """Третий шаг: ввод имен альтернатив, критериев и весов"""
        self.step3_group = QGroupBox("Шаг 3: Имена альтернатив, критериев и веса")
        step3_layout = QVBoxLayout(self.step3_group)
        step3_layout.setContentsMargins(15, 15, 15, 15)
        
        # Сетка для ввода данных
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setHorizontalSpacing(20)
        
        # Заголовки столбцов
        headers = ["Критерии", "Альтернативы"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet("""
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 11px;
                background: #e8f4fc;
                padding: 5px;
                border-radius: 4px;
            """)
            if col == 0:
                grid_layout.addWidget(label, 0, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
            else:
                grid_layout.addWidget(label, 0, 3, 1, 1, Qt.AlignmentFlag.AlignCenter)
        
        # Ввод критериев с весами
        self.criteria_inputs = []
        default_weight_value = 1.0 / self.num_criteria if self.num_criteria > 0 else 0.1
        
        for i in range(self.num_criteria):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Критерий {i+1}")
            name_input.setMinimumWidth(120)
            
            weight_input = QDoubleSpinBox()
            weight_input.setRange(0.0, 1.0)
            weight_input.setSingleStep(0.01)
            weight_input.setDecimals(3)
            weight_input.setValue(default_weight_value)
            weight_input.setPrefix("Вес: ")
            weight_input.setMinimumWidth(80)
            
            grid_layout.addWidget(QLabel(f"Крит.{i+1}:"), i+1, 0)
            grid_layout.addWidget(name_input, i+1, 1)
            grid_layout.addWidget(weight_input, i+1, 2)
            self.criteria_inputs.append((name_input, weight_input))
        
        # Ввод альтернатив
        self.alternative_inputs = []
        for i in range(self.num_alternatives):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Альтернатива {i+1}")
            name_input.setMinimumWidth(120)
            
            grid_layout.addWidget(QLabel(f"Альт.{i+1}:"), i+1, 3)
            grid_layout.addWidget(name_input, i+1, 4)
            self.alternative_inputs.append(name_input)
        
        # Информация о весах
        weight_info = QLabel("Сумма всех весов критериев должна быть равна 1.0")
        weight_info.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        step3_layout.addWidget(weight_info)
        
        step3_layout.addWidget(grid_widget)
        
        # Кнопка Далее с проверкой
        self.next_btn3 = QPushButton("Далее")
        self.next_btn3.clicked.connect(self.check_and_go_to_step4)
        step3_layout.addWidget(self.next_btn3, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step3_group)
        self.update_window_size()

    def check_and_go_to_step4(self):
        """Проверка данных и переход к следующему шагу"""
        # Проверка суммы весов
        total_weight = sum(inp[1].value() for inp in self.criteria_inputs)
        if abs(total_weight - 1.0) > 0.001:
            QMessageBox.warning(self, "Ошибка", 
                               f"Сумма всех весов должна быть равна 1.0\nТекущая сумма: {total_weight:.3f}")
            return
        
        # Проверка уникальности названий альтернатив
        alternative_names = [inp.text() or f"Альтернатива {i+1}" for i, inp in enumerate(self.alternative_inputs)]
        if len(alternative_names) != len(set(alternative_names)):
            QMessageBox.warning(self, "Ошибка", "Названия альтернатив должны быть уникальными")
            return
        
        # Проверка уникальности названий критериев
        criteria_names = [inp[0].text() or f"Критерий {i+1}" for i, inp in enumerate(self.criteria_inputs)]
        if len(criteria_names) != len(set(criteria_names)):
            QMessageBox.warning(self, "Ошибка", "Названия критериев должны быть уникальными")
            return

        # Сохраняем данные
        self.criteria_names = [inp[0].text() or f"Критерий {i+1}" for i, inp in enumerate(self.criteria_inputs)]
        self.criteria_weights = {inp[0].text() or f"Критерий {i+1}": inp[1].value() for i, inp in enumerate(self.criteria_inputs)}
        self.alternative_names = [inp.text() or f"Альтернатива {i+1}" for i, inp in enumerate(self.alternative_inputs)]
        
        # Деактивируем третий шаг
        self.deactivate_group(self.step3_group)
        self.next_btn3.setEnabled(False)
        
        # Переходим к четвертому шагу
        self.init_step4()
        self.current_step = 4
        
        # ОБНОВЛЯЕМ РАЗМЕР ОКНА
        self.schedule_resize_update()

    def init_step4(self):
        """Четвертый шаг: таблица оценок альтернатив по критериям"""
        self.step4_group = QGroupBox("Шаг 4: Оценки альтернатив по критериям")
        step4_layout = QVBoxLayout(self.step4_group)
        step4_layout.setContentsMargins(15, 15, 15, 15)
        
        info_label = QLabel("Заполните таблицу оценок альтернатив по критериям. Используйте кнопку для загрузки данных из CSV файла.")
        info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        step4_layout.addWidget(info_label)
        
        # Кнопка загрузки из CSV
        load_btn_layout = QHBoxLayout()
        load_csv_btn = QPushButton("Загрузить из CSV")
        load_csv_btn.clicked.connect(lambda: self.load_table_from_csv(self.ratings_table))
        load_btn_layout.addWidget(load_csv_btn)
        load_btn_layout.addStretch()
        step4_layout.addLayout(load_btn_layout)
        
        # Создаем таблицу
        self.ratings_table = QTableWidget(self.num_criteria, self.num_alternatives)
        
        # Устанавливаем заголовки
        horizontal_headers = self.alternative_names
        vertical_headers = self.criteria_names
        self.ratings_table.setHorizontalHeaderLabels(horizontal_headers)
        self.ratings_table.setVerticalHeaderLabels(vertical_headers)
        
        # НАСТРАИВАЕМ ВНЕШНИЙ ВИД
        self.setup_table_appearance(self.ratings_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту для таблицы
        table_height = self.num_criteria * self.ROW_HEIGHT + 40
        self.ratings_table.setMinimumHeight(table_height)
        self.ratings_table.setMaximumHeight(max(table_height, 500))

        table_width = self.num_alternatives * self.COLUMN_WIDTH + 40
        self.ratings_table.setMinimumWidth(table_width)
        self.ratings_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем таблицу пустыми значениями
        for row in range(self.num_criteria):
            for col in range(self.num_alternatives):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.ratings_table.setItem(row, col, item)
        self.ratings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        step4_layout.addWidget(self.ratings_table)
        
        # Кнопка завершения
        self.finish_btn = QPushButton("Завершить ввод данных")
        self.finish_btn.clicked.connect(self.finalize_data_input)
        step4_layout.addWidget(self.finish_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step4_group)
        self.update_window_size()

    def load_table_from_csv(self, table):
        """Загрузка данных в таблицу из CSV файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            #try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    data = list(reader)
                    
                    data = data[1:]
                    for i in range(len(data)):
                        data[i] = data[i][1:]
                    
                    # Проверяем размерность данных
                    if len(data) > table.rowCount() or len(data[0]) > table.columnCount():
                        QMessageBox.warning(self, "Ошибка", 
                                          "Размер данных в файле превышает размер таблицы")
                        return
                    
                    # Заполняем таблицу данными
                    for row_idx, row_data in enumerate(data):
                        for col_idx, cell_data in enumerate(row_data):
                            if (row_idx < table.rowCount() and 
                                col_idx < table.columnCount()):
                                item = QTableWidgetItem(cell_data.strip())
                                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                                table.setItem(row_idx, col_idx, item)
                                
                QMessageBox.information(self, "Успех", "Данные успешно загружены!")

    def finalize_data_input(self):
        """Завершает ввод всех данных"""
        if not self.validate_table_data(self.ratings_table, "определенных значений"):
            return
        
        # Проверяем, что все ячейки заполнены
        for row in range(self.ratings_table.rowCount()):
            for col in range(self.ratings_table.columnCount()):
                item = self.ratings_table.item(row, col)
                if not item or not item.text().strip():
                    QMessageBox.warning(self, "Ошибка", 
                                      "Не все ячейки таблицы заполнены")
                    return
        
        # Собираем данные из таблицы
        self.collect_table_data()
        
        # Сохраняем все данные задачи
        task_data = self.save_task_data()
        
        # Передаем данные в основное окно
        if self.parent:
            self.parent.on_third_task_completed(task_data)
        
        # Деактивируем четвертый шаг
        self.deactivate_group(self.step4_group)
        self.finish_btn.setEnabled(False)
        
        # Завершаем ввод
        QMessageBox.information(self, "Успех", 
                            "Все данные успешно введены и сохранены!")
        self.accept()

    def collect_table_data(self):
        """Собирает данные из таблицы оценок"""
        self.table_data = {}
        
        for row in range(self.ratings_table.rowCount()):
            criterion_name = self.criteria_names[row]
            row_data = []
            
            for col in range(self.ratings_table.columnCount()):
                item = self.ratings_table.item(row, col)
                try:
                    # Пытаемся преобразовать в число
                    value = float(item.text()) if item else 0.0
                    row_data.append(value)
                except ValueError:
                    # Если не число, сохраняем как строку
                    row_data.append(item.text() if item else "")
            
            self.table_data[criterion_name] = row_data
        
        # Добавляем названия альтернатив
        self.table_data['Alternatives'] = self.alternative_names

    def save_task_data(self):
        """Сохраняет все данные задачи в структурированном формате"""
        task_data = {
            'task_type': self.task_type,
            'basic_parameters': {
                'num_alternatives': self.num_alternatives,
                'num_criteria': self.num_criteria
            },
            'names': {
                'criteria_names': self.criteria_names,
                'alternative_names': self.alternative_names
            },
            'weights': self.criteria_weights,
            'table_data': pd.DataFrame(self.table_data).set_index('Alternatives').T
        }
        return task_data

    """Принятие решения в условиях аддитивности критериев"""
    def init_step2_additive(self):
        """Второй шаг для аддитивной стратегии: основные параметры"""
        self.step2_group = QGroupBox("Шаг 2: Основные параметры")
        step2_layout = QGridLayout(self.step2_group)
        step2_layout.setSpacing(15)
        step2_layout.setContentsMargins(15, 15, 15, 15)
        
        # Создаем элементы ввода
        labels = [
            "Количество альтернатив:",
            "Количество критериев:",
            "Способ задания оценки:"
        ]
        
        default_values = [5, 6]
        self.step2_inputs = []
        
        for i, label_text in enumerate(labels[:2]):
            label = QLabel(label_text)
            label.setMinimumWidth(150)
            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(20)
            spinbox.setValue(default_values[i])
            spinbox.setMinimumWidth(80)
            
            step2_layout.addWidget(label, 0, 2*i)
            step2_layout.addWidget(spinbox, 0, 2*i+1)
            self.step2_inputs.append(spinbox)
        
        # Комбобокс для способа задания оценки
        evaluation_label = QLabel(labels[2])
        evaluation_label.setMinimumWidth(150)
        self.evaluation_combo = QComboBox()
        self.evaluation_combo.addItems(["Нечеткие числа", "Функции принадлежности"])
        self.evaluation_combo.setMinimumWidth(150)
        self.evaluation_combo.currentTextChanged.connect(self.on_evaluation_method_changed)
        
        step2_layout.addWidget(evaluation_label, 1, 1)
        step2_layout.addWidget(self.evaluation_combo, 1, 2)
    
        # Поля для функций принадлежности (изначально скрыты)
        self.membership_inputs = []
        membership_labels = [
            "Количество степеней соответствия:",
            "Количество степеней важности:"
        ]
        
        for i, label_text in enumerate(membership_labels):
            label = QLabel(label_text)
            label.setMinimumWidth(180)
            spinbox = QSpinBox()
            spinbox.setMinimum(2)
            spinbox.setMaximum(10)
            spinbox.setValue(3)
            spinbox.setMinimumWidth(80)
            spinbox.setVisible(False)
            label.setVisible(False)
            
            step2_layout.addWidget(label, 2, 2*i)
            step2_layout.addWidget(spinbox, 2, 2*i+1)
            self.membership_inputs.append((label, spinbox))
        
        # Кнопка Далее
        self.next_btn2 = QPushButton("Далее")
        self.next_btn2.clicked.connect(self.go_to_step3_additive)
        step2_layout.addWidget(self.next_btn2, 3, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step2_group)
        self.update_window_size()

    def on_evaluation_method_changed(self, method):
        """Обработчик изменения способа задания оценки"""
        is_membership = (method == "Функции принадлежности")
        
        # Показываем/скрываем поля для функций принадлежности
        for label, spinbox in self.membership_inputs:
            label.setVisible(is_membership)
            spinbox.setVisible(is_membership)

    def go_to_step3_additive(self):
        """Переход к третьему шагу для аддитивной стратегии"""
        # Сохраняем значения
        self.num_alternatives = self.step2_inputs[0].value()
        self.num_criteria = self.step2_inputs[1].value()
        self.evaluation_method = self.evaluation_combo.currentText()
    
        # Для функций принадлежности сохраняем дополнительные параметры
        if self.evaluation_method == "Функции принадлежности":
            self.num_compliance_degrees = self.membership_inputs[0][1].value()
            self.num_importance_degrees = self.membership_inputs[1][1].value()
        
        # Деактивируем второй шаг
        self.deactivate_group(self.step2_group)
        self.next_btn2.setEnabled(False)
        
        # Инициализируем третий шаг
        self.init_step3_additive()
        self.current_step = 3
        self.schedule_resize_update()

    def init_step3_additive(self):
        """Третий шаг для аддитивной стратегии: имена критериев и альтернатив"""
        self.step3_group = QGroupBox("Шаг 3: Имена альтернатив и критериев")
        step3_layout = QVBoxLayout(self.step3_group)
        step3_layout.setContentsMargins(15, 15, 15, 15)
        
        # Сетка для ввода данных
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setHorizontalSpacing(20)
        
        # Заголовки столбцов
        headers = ["Критерии", "Альтернативы"]
        if self.evaluation_method == "Функции принадлежности":
            headers.extend(["Степени соответствия", "Степени важности"])

        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet("""
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 11px;
                background: #e8f4fc;
                padding: 5px;
                border-radius: 4px;
            """)
            grid_layout.addWidget(label, 0, col*2, 1, 2, Qt.AlignmentFlag.AlignCenter)
        
        # Ввод критериев
        self.criteria_inputs = []
        max_rows = max(self.num_criteria, self.num_alternatives)
        if self.evaluation_method == "Функции принадлежности":
            max_rows = max(max_rows, self.num_compliance_degrees, self.num_importance_degrees)

        for i in range(self.num_criteria):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Критерий {i+1}")
            name_input.setMinimumWidth(120)
            
            grid_layout.addWidget(QLabel(f"Крит.{i+1}:"), i+1, 0)
            grid_layout.addWidget(name_input, i+1, 1)
            self.criteria_inputs.append(name_input)
        
        # Ввод альтернатив
        self.alternative_inputs = []
        for i in range(self.num_alternatives):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Альтернатива {i+1}")
            name_input.setMinimumWidth(120)
            
            grid_layout.addWidget(QLabel(f"Альт.{i+1}:"), i+1, 2)
            grid_layout.addWidget(name_input, i+1, 3)
            self.alternative_inputs.append(name_input)
    
        # Ввод степеней для функций принадлежности
        if self.evaluation_method == "Функции принадлежности":
            # Степени соответствия
            self.compliance_inputs = []
            for i in range(self.num_compliance_degrees):
                name_input = QLineEdit()
                name_input.setPlaceholderText(f"Степень соотв. {i+1}")
                name_input.setMinimumWidth(120)
                
                grid_layout.addWidget(QLabel(f"Сотв.{i+1}:"), i+1, 4)
                grid_layout.addWidget(name_input, i+1, 5)
                self.compliance_inputs.append(name_input)
            
            # Степени важности
            self.importance_inputs = []
            for i in range(self.num_importance_degrees):
                name_input = QLineEdit()
                name_input.setPlaceholderText(f"Степень важн. {i+1}")
                name_input.setMinimumWidth(120)
                
                grid_layout.addWidget(QLabel(f"Важн.{i+1}:"), i+1, 6)
                grid_layout.addWidget(name_input, i+1, 7)
                self.importance_inputs.append(name_input)
        
        step3_layout.addWidget(grid_widget)
        
        # Кнопка Далее с проверкой
        self.next_btn3 = QPushButton("Далее")
        self.next_btn3.clicked.connect(self.check_and_go_to_step4_additive)
        step3_layout.addWidget(self.next_btn3, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step3_group)
        self.update_window_size()

    def check_and_go_to_step4_additive(self):
        """Проверка данных и переход к четвертому шагу для аддитивной стратегии"""
        # Проверка уникальности названий альтернатив
        alternative_names = [inp.text() or f"Альтернатива {i+1}" for i, inp in enumerate(self.alternative_inputs)]
        if len(alternative_names) != len(set(alternative_names)):
            QMessageBox.warning(self, "Ошибка", "Названия альтернатив должны быть уникальными")
            return
        
        # Проверка уникальности названий критериев
        criteria_names = [inp.text() or f"Критерий {i+1}" for i, inp in enumerate(self.criteria_inputs)]
        if len(criteria_names) != len(set(criteria_names)):
            QMessageBox.warning(self, "Ошибка", "Названия критериев должны быть уникальными")
            return
    
        # Для функций принадлежности проверяем уникальность степеней
        if self.evaluation_method == "Функции принадлежности":
            compliance_names = [inp.text() or f"Степень соотв. {i+1}" for i, inp in enumerate(self.compliance_inputs)]
            if len(compliance_names) != len(set(compliance_names)):
                QMessageBox.warning(self, "Ошибка", "Названия степеней соответствия должны быть уникальными")
                return
            
            importance_names = [inp.text() or f"Степень важн. {i+1}" for i, inp in enumerate(self.importance_inputs)]
            if len(importance_names) != len(set(importance_names)):
                QMessageBox.warning(self, "Ошибка", "Названия степеней важности должны быть уникальными")
                return

        # Сохраняем данные
        self.criteria_names = criteria_names
        self.alternative_names = alternative_names
    
        if self.evaluation_method == "Функции принадлежности":
            self.compliance_names = compliance_names
            self.importance_names = importance_names
        
        # Деактивируем третий шаг
        self.deactivate_group(self.step3_group)
        self.next_btn3.setEnabled(False)
    
        # Переходим к следующему шагу в зависимости от метода
        if self.evaluation_method == "Функции принадлежности":
            self.init_step4_membership()
            self.current_step = 4
        else:
            self.init_step4_additive()
            self.current_step = 4
        
        self.schedule_resize_update()

    def init_step4_additive(self):
        """Четвертый шаг для аддитивной стратегии: таблицы весов и оценок"""
        self.step4_group = QGroupBox("Шаг 4: Веса критериев и оценки альтернатив")
        step4_layout = QVBoxLayout(self.step4_group)
        step4_layout.setContentsMargins(15, 15, 15, 15)
        
        # Таблица весов критериев (для обоих методов)
        weights_group = QGroupBox("Веса критериев")
        weights_layout = QVBoxLayout(weights_group)
        
        # Кнопка загрузки из CSV для весов
        weights_load_layout = QHBoxLayout()
        weights_load_btn = QPushButton("Загрузить веса из CSV")
        weights_load_layout.addWidget(weights_load_btn)
        weights_load_layout.addStretch()
        weights_layout.addLayout(weights_load_layout)
        
        # Создаем таблицу весов в зависимости от метода
        #if self.evaluation_method == "Нечеткие числа":
        #    # Для нечетких чисел: 1 строка
        self.weights_table = QTableWidget(1, self.num_criteria)
        self.weights_table.setVerticalHeaderLabels(["Веса"])
        #else:
        #    # Для функций принадлежности: 3 строки (старт, пик, конец)
        #    self.weights_table = QTableWidget(3, self.num_criteria)
        #    self.weights_table.setVerticalHeaderLabels(["Старт", "Пик", "Конец"])
        
        self.weights_table.setHorizontalHeaderLabels(self.criteria_names)
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.weights_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту
        table_height = self.weights_table.rowCount() * self.ROW_HEIGHT + 40
        self.weights_table.setMinimumHeight(table_height)
        self.weights_table.setMaximumHeight(max(table_height, 500))
        
        table_width = self.num_criteria * self.COLUMN_WIDTH + 40
        self.weights_table.setMinimumWidth(table_width)
        self.weights_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем таблицу пустыми значениями
        for row in range(self.weights_table.rowCount()):
            for col in range(self.weights_table.columnCount()):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.weights_table.setItem(row, col, item)
        self.weights_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        weights_layout.addWidget(self.weights_table)
        step4_layout.addWidget(weights_group)
        
        # Привязываем кнопку загрузки
        weights_load_btn.clicked.connect(lambda: self.load_table_from_csv(self.weights_table))
        
        # Таблицы оценок в зависимости от метода
        if self.evaluation_method == "Нечеткие числа":
            # Для нечетких чисел: одна таблица оценок
            ratings_group = QGroupBox("Оценки альтернатив по критериям")
            ratings_layout = QVBoxLayout(ratings_group)
            
            # Кнопка загрузки из CSV для оценок
            ratings_load_layout = QHBoxLayout()
            ratings_load_btn = QPushButton("Загрузить оценки из CSV")
            ratings_load_layout.addWidget(ratings_load_btn)
            ratings_load_layout.addStretch()
            ratings_layout.addLayout(ratings_load_layout)
            
            # Создаем таблицу оценок (строки - критерии, столбцы - альтернативы)
            self.ratings_table = QTableWidget(self.num_criteria, self.num_alternatives)
            self.ratings_table.setHorizontalHeaderLabels(self.alternative_names)
            self.ratings_table.setVerticalHeaderLabels(self.criteria_names)
            
            # Настраиваем внешний вид
            self.setup_table_appearance(self.ratings_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
            
            # Устанавливаем фиксированную высоту
            table_height = self.num_criteria * self.ROW_HEIGHT + 40
            self.ratings_table.setMinimumHeight(table_height)
            self.ratings_table.setMaximumHeight(max(table_height, 500))
            
            table_width = self.num_alternatives * self.COLUMN_WIDTH + 40
            self.ratings_table.setMinimumWidth(table_width)
            self.ratings_table.setMaximumWidth(max(table_width, 500))
            
            # Заполняем таблицу пустыми значениями
            for row in range(self.ratings_table.rowCount()):
                for col in range(self.ratings_table.columnCount()):
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.ratings_table.setItem(row, col, item)
            self.ratings_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            ratings_layout.addWidget(self.ratings_table)
            step4_layout.addWidget(ratings_group)
            
            # Привязываем кнопку загрузки
            ratings_load_btn.clicked.connect(lambda: self.load_table_from_csv(self.ratings_table))
            
            # Кнопка завершения для нечетких чисел
            self.finish_btn = QPushButton("Завершить сбор данных")
            self.finish_btn.clicked.connect(self.finalize_additive_data_input)
            step4_layout.addWidget(self.finish_btn, 0, Qt.AlignmentFlag.AlignCenter)
            
        #else:
        #    # Для функций принадлежности: отдельные таблицы для каждой альтернативы
        #    self.alternative_tables = []
        #    
        #    for alt_idx, alt_name in enumerate(self.alternative_names):
        #        alt_group = QGroupBox(f"Альтернатива: {alt_name}")
        #        alt_layout = QVBoxLayout(alt_group)
                
        #        # Кнопка загрузки из CSV для этой альтернативы
        #        alt_load_layout = QHBoxLayout()
        #        alt_load_btn = QPushButton(f"Загрузить данные для {alt_name} из CSV")
        #        alt_load_layout.addWidget(alt_load_btn)
        #        alt_load_layout.addStretch()
        #        alt_layout.addLayout(alt_load_layout)
                
        #        # Создаем таблицу для альтернативы (3 строки, столбцы - критерии)
        #        alt_table = QTableWidget(3, self.num_criteria)
        #        alt_table.setHorizontalHeaderLabels(self.criteria_names)
        #        alt_table.setVerticalHeaderLabels(["Старт", "Пик", "Конец"])
                
        #        # Настраиваем внешний вид
        #        self.setup_table_appearance(alt_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
                
        #        # Устанавливаем фиксированную высоту
        #        table_height = 3 * self.ROW_HEIGHT + 40
        #        alt_table.setMinimumHeight(table_height)
        #        alt_table.setMaximumHeight(max(table_height, 500))
                
        #        table_width = self.num_criteria * self.COLUMN_WIDTH + 40
        #        alt_table.setMinimumWidth(table_width)
        #        alt_table.setMaximumWidth(max(table_width, 500))
                
        #        # Заполняем таблицу пустыми значениями
        #        for row in range(alt_table.rowCount()):
        #            for col in range(alt_table.columnCount()):
        #                item = QTableWidgetItem("")
        #                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        #                alt_table.setItem(row, col, item)
        #        
        #        alt_layout.addWidget(alt_table)
        #        step4_layout.addWidget(alt_group)
        #        self.alternative_tables.append(alt_table)
        #        
        #        # Привязываем кнопку загрузки
        #        alt_load_btn.clicked.connect(lambda checked, table=alt_table: self.load_table_from_csv(table))
        #    
        #    # Кнопка Далее для функций принадлежности
        #    self.next_btn4 = QPushButton("Далее")
        #    self.next_btn4.clicked.connect(self.go_to_step5_additive)
        #    step4_layout.addWidget(self.next_btn4, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step4_group)
        self.update_window_size()

    def validate_triangular_table(self, table, table_name):
        """Проверяет треугольную таблицу на корректность"""
        for col in range(table.columnCount()):
            # Получаем значения из трех строк
            start_item = table.item(0, col)
            peak_item = table.item(1, col)
            end_item = table.item(2, col)
            
            # Проверяем, что все ячейки заполнены
            if not start_item or not start_item.text().strip():
                QMessageBox.warning(self, "Ошибка", f"Не заполнено значение 'Старт' в столбце {col+1} таблицы {table_name}")
                return False
            if not peak_item or not peak_item.text().strip():
                QMessageBox.warning(self, "Ошибка", f"Не заполнено значение 'Пик' в столбце {col+1} таблицы {table_name}")
                return False
            if not end_item or not end_item.text().strip():
                QMessageBox.warning(self, "Ошибка", f"Не заполнено значение 'Конец' в столбце {col+1} таблицы {table_name}")
                return False
            
            try:
                # Преобразуем в числа
                start_val = float(start_item.text())
                peak_val = float(peak_item.text())
                end_val = float(end_item.text())
                
                # Проверяем условие: старт <= пик <= конец
                if start_val > peak_val:
                    QMessageBox.warning(self, "Ошибка", 
                                    f"В таблице {table_name}, столбец {col+1}: 'Старт' ({start_val}) > 'Пик' ({peak_val})")
                    return False
                if peak_val > end_val:
                    QMessageBox.warning(self, "Ошибка", 
                                    f"В таблице {table_name}, столбец {col+1}: 'Пик' ({peak_val}) > 'Конец' ({end_val})")
                    return False
                    
            except ValueError:
                QMessageBox.warning(self, "Ошибка", 
                                f"В таблице {table_name}, столбец {col+1}: значения должны быть числами")
                return False
        
        return True

    def collect_triangular_table_data(self, table, column_names):
        """Собирает данные из треугольной таблицы"""
        data = {}
        for col in range(table.columnCount()):
            col_name = column_names[col]
            start_val = float(table.item(0, col).text())
            peak_val = float(table.item(1, col).text())
            end_val = float(table.item(2, col).text())
            data[col_name] = {
                'start': start_val,
                'peak': peak_val,
                'end': end_val
            }
        return data

    def finalize_additive_data_input(self):
        """Завершает ввод данных для аддитивной стратегии (Нечеткие числа)"""        
        if not self.validate_table_data(self.weights_table, "весов критериев"):
            return
        
        if not self.validate_table_data(self.ratings_table, "значений принадлежности"):
            return
        
        # Проверяем, что все ячейки заполнены
        for row in range(self.weights_table.rowCount()):
            for col in range(self.weights_table.columnCount()):
                item = self.weights_table.item(row, col)
                if not item or not item.text().strip():
                    QMessageBox.warning(self, "Ошибка", "Не все веса критериев заполнены")
                    return
        
        for row in range(self.ratings_table.rowCount()):
            for col in range(self.ratings_table.columnCount()):
                item = self.ratings_table.item(row, col)
                if not item or not item.text().strip():
                    QMessageBox.warning(self, "Ошибка", "Не все оценки альтернатив заполнены")
                    return
        
        # Собираем данные из таблиц
        self.collect_additive_table_data()
        
        # Сохраняем все данные задачи
        task_data = self.save_additive_task_data()
        
        # Передаем данные в основное окно
        if self.parent:
            self.parent.on_third_task_completed(task_data)
        
        # Деактивируем четвертый шаг
        self.deactivate_group(self.step4_group)
        self.finish_btn.setEnabled(False)
        
        # Завершаем ввод
        QMessageBox.information(self, "Успех", "Все данные успешно введены и сохранены!")
        self.accept()

    def collect_additive_table_data(self):
        """Собирает данные из таблиц для аддитивной стратегии"""
        if self.evaluation_method == "Нечеткие числа":
            # Данные таблицы весов
            self.weights_table_data = {}
            for col in range(self.weights_table.columnCount()):
                criterion_name = self.criteria_names[col]
                item = self.weights_table.item(0, col)
                try:
                    value = float(item.text()) if item else 0.0
                    self.weights_table_data[criterion_name] = value
                except ValueError:
                    self.weights_table_data[criterion_name] = item.text() if item else ""
            
            # Данные таблицы оценок
            self.ratings_table_data = {}
            for row in range(self.ratings_table.rowCount()):
                criterion_name = self.criteria_names[row]
                row_data = []
                for col in range(self.ratings_table.columnCount()):
                    item = self.ratings_table.item(row, col)
                    try:
                        value = float(item.text()) if item else 0.0
                        row_data.append(value)
                    except ValueError:
                        row_data.append(item.text() if item else "")
                self.ratings_table_data[criterion_name] = row_data
            
            # Добавляем названия альтернатив
            self.ratings_table_data['Alternatives'] = self.alternative_names

    def save_additive_task_data(self):
        """Сохраняет все данные задачи для аддитивной стратегии"""
        task_data = {
            'task_type': self.task_type,
            'evaluation_method': self.evaluation_method,
            'basic_parameters': {
                'num_alternatives': self.num_alternatives,
                'num_criteria': self.num_criteria
            },
            'names': {
                'criteria_names': self.criteria_names,
                'alternative_names': self.alternative_names
            },
            'table_data': pd.DataFrame(self.ratings_table_data).set_index('Alternatives').T,
        }
        
        # Добавляем веса если есть
        if self.evaluation_method == "Нечеткие числа":
            task_data['weights'] = self.weights_table_data
        
        return task_data

    """Принятие решения при наличии функций принадлежности"""
    def init_step4_membership(self):
        """Четвертый шаг для функций принадлежности: таблицы функций принадлежности"""
        self.step4_group = QGroupBox("Шаг 4: Функции принадлежности для степеней")
        step4_layout = QVBoxLayout(self.step4_group)
        step4_layout.setContentsMargins(15, 15, 15, 15)
        
        # Таблица для степеней соответствия
        compliance_group = QGroupBox("Функции принадлежности для степеней соответствия")
        compliance_layout = QVBoxLayout(compliance_group)
        
        # Кнопка загрузки из CSV
        compliance_load_layout = QHBoxLayout()
        compliance_load_btn = QPushButton("Загрузить степени соответствия из CSV")
        compliance_load_layout.addWidget(compliance_load_btn)
        compliance_load_layout.addStretch()
        compliance_layout.addLayout(compliance_load_layout)
        
        # Создаем таблицу (3 строки, столбцы - степени соответствия)
        self.compliance_table = QTableWidget(3, self.num_compliance_degrees)
        self.compliance_table.setHorizontalHeaderLabels(self.compliance_names)
        self.compliance_table.setVerticalHeaderLabels(["Старт", "Пик", "Конец"])
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.compliance_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту
        table_height = 3 * self.ROW_HEIGHT + 40
        self.compliance_table.setMinimumHeight(table_height)
        self.compliance_table.setMaximumHeight(table_height)
        
        table_width = self.num_compliance_degrees * self.COLUMN_WIDTH + 40
        self.compliance_table.setMinimumWidth(table_width)
        self.compliance_table.setMaximumWidth(table_width)
        
        # Заполняем таблицу пустыми значениями
        for row in range(3):
            for col in range(self.num_compliance_degrees):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.compliance_table.setItem(row, col, item)
        self.compliance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        compliance_layout.addWidget(self.compliance_table)
        step4_layout.addWidget(compliance_group)
        
        # Привязываем кнопку загрузки
        compliance_load_btn.clicked.connect(lambda: self.load_table_from_csv(self.compliance_table))
        
        # Таблица для степеней важности
        importance_group = QGroupBox("Функции принадлежности для степеней важности")
        importance_layout = QVBoxLayout(importance_group)
        
        # Кнопка загрузки из CSV
        importance_load_layout = QHBoxLayout()
        importance_load_btn = QPushButton("Загрузить степени важности из CSV")
        importance_load_layout.addWidget(importance_load_btn)
        importance_load_layout.addStretch()
        importance_layout.addLayout(importance_load_layout)
        
        # Создаем таблицу (3 строки, столбцы - степени важности)
        self.importance_table = QTableWidget(3, self.num_importance_degrees)
        self.importance_table.setHorizontalHeaderLabels(self.importance_names)
        self.importance_table.setVerticalHeaderLabels(["Старт", "Пик", "Конец"])
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.importance_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту
        table_height = 3 * self.ROW_HEIGHT + 40
        self.importance_table.setMinimumHeight(table_height)
        self.importance_table.setMaximumHeight(table_height)
        
        table_width = self.num_importance_degrees * self.COLUMN_WIDTH + 40
        self.importance_table.setMinimumWidth(table_width)
        self.importance_table.setMaximumWidth(table_width)
        
        # Заполняем таблицу пустыми значениями
        for row in range(3):
            for col in range(self.num_importance_degrees):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.importance_table.setItem(row, col, item)
        self.importance_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        importance_layout.addWidget(self.importance_table)
        step4_layout.addWidget(importance_group)
        
        # Привязываем кнопку загрузки
        importance_load_btn.clicked.connect(lambda: self.load_table_from_csv(self.importance_table))
        
        # Кнопка Далее
        self.next_btn4 = QPushButton("Далее")
        self.next_btn4.clicked.connect(self.go_to_step5_membership)
        step4_layout.addWidget(self.next_btn4, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step4_group)
        self.update_window_size()

    def go_to_step5_membership(self):
        """Переход к пятому шагу для функций принадлежности"""        
        if not self.validate_table_data(self.compliance_table, "значений принадлежности"):
            return
        
        if not self.validate_table_data(self.importance_table, "значений важности"):
            return
        
        # Проверяем корректность данных в таблицах
        if not self.validate_membership_functions_step4():
            return
        
        # Собираем данные из таблиц
        self.collect_membership_data_step4()
        
        # Деактивируем четвертый шаг
        self.deactivate_group(self.step4_group)
        self.next_btn4.setEnabled(False)
        
        # Инициализируем пятый шаг
        self.init_step5_membership()
        self.current_step = 5
        self.schedule_resize_update()

    def validate_membership_functions_step4(self):
        """Проверяет корректность функций принадлежности на 4 этапе"""
        if not self.validate_triangular_table(self.compliance_table, "степеней соответствия"):
            return False
        
        if not self.validate_triangular_table(self.importance_table, "степеней важности"):
            return False
        
        return True

    def collect_membership_data_step4(self):
        """Собирает данные для функций принадлежности на 4 этапе"""
        self.compliance_data = self.collect_triangular_table_data(self.compliance_table, self.compliance_names)
        self.importance_data = self.collect_triangular_table_data(self.importance_table, self.importance_names)

    def init_step5_membership(self):
        """Пятый шаг для функций принадлежности: веса критериев и оценки альтернатив"""
        self.step5_group = QGroupBox("Шаг 5: Веса критериев и оценки альтернатив")
        step5_layout = QVBoxLayout(self.step5_group)
        step5_layout.setContentsMargins(15, 15, 15, 15)
        
        # Таблица весов критериев
        weights_group = QGroupBox("Веса критериев")
        weights_layout = QVBoxLayout(weights_group)
        
        # Создаем таблицу весов (1 строка, столбцы - критерии)
        self.weights_table_membership = QTableWidget(1, self.num_criteria)
        self.weights_table_membership.setHorizontalHeaderLabels(self.criteria_names)
        self.weights_table_membership.setVerticalHeaderLabels(["Степень важности"])
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.weights_table_membership, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту
        table_height = self.ROW_HEIGHT + 40
        self.weights_table_membership.setMinimumHeight(table_height)
        self.weights_table_membership.setMaximumHeight(table_height)
        
        table_width = self.num_criteria * self.COLUMN_WIDTH + 40
        self.weights_table_membership.setMinimumWidth(table_width)
        self.weights_table_membership.setMaximumWidth(table_width)
        
        # Заполняем таблицу комбобоксами
        for col in range(self.num_criteria):
            combo = QComboBox()
            combo.addItems(self.importance_names)
            combo.setCurrentIndex(0)
            combo.setMaximumWidth(self.COLUMN_WIDTH)
            self.weights_table_membership.setCellWidget(0, col, combo)
        self.weights_table_membership.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        weights_layout.addWidget(self.weights_table_membership)
        step5_layout.addWidget(weights_group)
        
        # Таблица оценок альтернатив
        ratings_group = QGroupBox("Оценки альтернатив по критериям")
        ratings_layout = QVBoxLayout(ratings_group)
        
        # Создаем таблицу оценок (строки - критерии, столбцы - альтернативы)
        self.ratings_table_membership = QTableWidget(self.num_criteria, self.num_alternatives)
        self.ratings_table_membership.setHorizontalHeaderLabels(self.alternative_names)
        self.ratings_table_membership.setVerticalHeaderLabels(self.criteria_names)
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.ratings_table_membership, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту
        table_height = self.num_criteria * self.ROW_HEIGHT + 40
        self.ratings_table_membership.setMinimumHeight(table_height)
        self.ratings_table_membership.setMaximumHeight(table_height)
        
        table_width = self.num_alternatives * self.COLUMN_WIDTH + 40
        self.ratings_table_membership.setMinimumWidth(table_width)
        self.ratings_table_membership.setMaximumWidth(table_width)
        
        # Заполняем таблицу комбобоксами
        for row in range(self.num_criteria):
            for col in range(self.num_alternatives):
                combo = QComboBox()
                combo.addItems(self.compliance_names)
                combo.setCurrentIndex(0)
                combo.setMinimumWidth(self.COLUMN_WIDTH)
                self.ratings_table_membership.setCellWidget(row, col, combo)
        self.ratings_table_membership.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        ratings_layout.addWidget(self.ratings_table_membership)
        step5_layout.addWidget(ratings_group)
        
        # Кнопка Далее
        self.next_btn5 = QPushButton("Далее")
        self.next_btn5.clicked.connect(self.go_to_step6_membership)
        step5_layout.addWidget(self.next_btn5, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step5_group)
        self.update_window_size()

    def go_to_step6_membership(self):
        """Переход к шестому шагу для функций принадлежности"""        
        # Собираем данные из таблиц
        self.collect_membership_data_step5()
        
        # Деактивируем пятый шаг
        self.deactivate_group(self.step5_group)
        self.next_btn5.setEnabled(False)
        
        # Инициализируем шестой шаг
        self.init_step6_membership()
        self.current_step = 6
        self.schedule_resize_update()

    def collect_membership_data_step5(self):
        """Собирает данные для функций принадлежности на 5 этапе"""
        # Собираем веса критериев
        self.criteria_weights_membership = {}
        for col in range(self.num_criteria):
            criterion_name = self.criteria_names[col]
            combo = self.weights_table_membership.cellWidget(0, col)
            self.criteria_weights_membership[criterion_name] = combo.currentText()
        
        # Собираем оценки альтернатив
        self.alternative_ratings_membership = {}
        for row in range(self.num_criteria):
            criterion_name = self.criteria_names[row]
            criterion_ratings = {}
            for col in range(self.num_alternatives):
                alt_name = self.alternative_names[col]
                combo = self.ratings_table_membership.cellWidget(row, col)
                criterion_ratings[alt_name] = combo.currentText()
            self.alternative_ratings_membership[criterion_name] = criterion_ratings

    def init_step6_membership(self):
        """Шестой шаг для функций принадлежности: метод дефаззификации"""
        self.step6_group = QGroupBox("Шаг 6: Метод дефаззификации")
        step6_layout = QVBoxLayout(self.step6_group)
        step6_layout.setSpacing(15)
        step6_layout.setContentsMargins(15, 15, 15, 15)
        
        # Комбобокс для выбора метода дефаззификации
        method_layout = QHBoxLayout()
        method_label = QLabel("Метод дефаззификации:")
        method_label.setMinimumWidth(self.COLUMN_WIDTH)
        
        self.defuzzification_combo = QComboBox()
        self.defuzzification_combo.addItems([
            "Метод центра тяжести",
            "Метод центра площади", 
            "Метод максимума"
        ])
        self.defuzzification_combo.setMinimumWidth(self.COLUMN_WIDTH)
        
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.defuzzification_combo)
        method_layout.addStretch()
        step6_layout.addLayout(method_layout)
        
        # Информация о методах
        #info_label = QLabel("Выберите метод для преобразования нечетких чисел в четкие значения")
        #info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        #step6_layout.addWidget(info_label)
        
        # Кнопка завершения
        self.final_btn = QPushButton("Завершить ввод данных")
        self.final_btn.clicked.connect(self.finalize_membership_data_input)
        step6_layout.addWidget(self.final_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step6_group)
        self.update_window_size()

    def finalize_membership_data_input(self):
        """Завершает ввод данных для функций принадлежности"""
        # Сохраняем метод дефаззификации
        self.defuzzification_method = self.defuzzification_combo.currentText()
        
        # Сохраняем все данные задачи
        task_data = self.save_membership_task_data()
        
        # Передаем данные в основное окно
        if self.parent:
            self.parent.on_third_task_completed(task_data)
        
        # Деактивируем шестой шаг
        self.deactivate_group(self.step6_group)
        self.final_btn.setEnabled(False)
        
        # Завершаем ввод
        QMessageBox.information(self, "Успех", "Все данные успешно введены и сохранены!")
        self.accept()

    def save_membership_task_data(self):
        """Сохраняет все данные задачи для функций принадлежности"""
        # Преобразуем данные в DataFrame
        compliance_df = self.triangular_data_to_dataframe(self.compliance_data, self.compliance_names)
        importance_df = self.triangular_data_to_dataframe(self.importance_data, self.importance_names)
        
        # Создаем DataFrame для весов критериев
        weights_series = pd.Series(self.criteria_weights_membership)
        
        # Создаем DataFrame для оценок альтернатив
        ratings_data = {}
        for criterion, alt_ratings in self.alternative_ratings_membership.items():
            ratings_data[criterion] = alt_ratings
        ratings_df = pd.DataFrame(ratings_data)
        
        task_data = {
            'task_type': self.task_type,
            'evaluation_method': self.evaluation_method,
            'defuzzification_method': self.defuzzification_method,
            'basic_parameters': {
                'num_alternatives': self.num_alternatives,
                'num_criteria': self.num_criteria,
                'num_compliance_degrees': self.num_compliance_degrees,
                'num_importance_degrees': self.num_importance_degrees
            },
            'names': {
                'criteria_names': self.criteria_names,
                'alternative_names': self.alternative_names,
                'compliance_names': self.compliance_names,
                'importance_names': self.importance_names
            },
            'membership_functions': {
                'compliance': compliance_df,
                'importance': importance_df
            },
            'criteria_weights': weights_series,
            'alternative_ratings': ratings_df
        }
        
        return task_data

    def triangular_data_to_dataframe(self, triangular_data, column_names):
        """Преобразует треугольные данные в DataFrame"""
        data = {}
        for col_name, values in triangular_data.items():
            data[col_name] = [values['start'], values['peak'], values['end']]
        return pd.DataFrame(data, index=['Старт', 'Пик', 'Конец'])

    """Принятие решения на основе нечетких систем"""
    def init_step2_fuzzy_systems(self):
        """Второй шаг для нечетких систем: основные параметры"""
        self.step2_group = QGroupBox("Шаг 2: Основные параметры нечеткой системы")
        step2_layout = QGridLayout(self.step2_group)
        step2_layout.setSpacing(15)
        step2_layout.setContentsMargins(15, 15, 15, 15)
        
        # Создаем элементы ввода
        labels = [
            "Количество критериев:",
            "Количество степеней соответствия:",
            "Количество альтернатив:",
            "Количество правил:"
        ]
        
        default_values = [3, 3, 5, 5]
        self.step2_inputs_fuzzy = []
        
        for i, (label_text, default_val) in enumerate(zip(labels, default_values)):
            label = QLabel(label_text)
            label.setMinimumWidth(180)
            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(20)
            spinbox.setValue(default_val)
            spinbox.setMinimumWidth(80)
            
            row = i // 2
            col = (i % 2) * 2
            step2_layout.addWidget(label, row, col)
            step2_layout.addWidget(spinbox, row, col + 1)
            self.step2_inputs_fuzzy.append(spinbox)
        
        # Кнопка Далее
        self.next_btn2 = QPushButton("Далее")
        self.next_btn2.clicked.connect(self.go_to_step3_fuzzy_systems)
        step2_layout.addWidget(self.next_btn2, 2, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step2_group)
        self.update_window_size()

    def go_to_step3_fuzzy_systems(self):
        """Переход к третьему шагу для нечетких систем"""
        # Сохраняем значения
        self.num_criteria = self.step2_inputs_fuzzy[0].value()
        self.num_compliance_degrees = self.step2_inputs_fuzzy[1].value()
        self.num_alternatives = self.step2_inputs_fuzzy[2].value()
        self.num_rules = self.step2_inputs_fuzzy[3].value()
        
        # Деактивируем второй шаг
        self.deactivate_group(self.step2_group)
        self.next_btn2.setEnabled(False)
        
        # Инициализируем третий шаг
        self.init_step3_fuzzy_systems()
        self.current_step = 3
        self.schedule_resize_update()

    def init_step3_fuzzy_systems(self):
        """Третий шаг для нечетких систем: ввод названий"""
        self.step3_group = QGroupBox("Шаг 3: Названия элементов системы")
        step3_layout = QVBoxLayout(self.step3_group)
        step3_layout.setContentsMargins(15, 15, 15, 15)
        
        # Сетка для ввода данных
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setHorizontalSpacing(20)
        
        # Заголовки столбцов
        headers = ["Критерии", "Степени соответствия", "Альтернативы"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet("""
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 11px;
                background: #e8f4fc;
                padding: 5px;
                border-radius: 4px;
            """)
            grid_layout.addWidget(label, 0, col*2, 1, 2, Qt.AlignmentFlag.AlignCenter)
        
        # Ввод критериев
        self.criteria_inputs_fuzzy = []
        max_rows = max(self.num_criteria, self.num_compliance_degrees, self.num_alternatives)
        
        for i in range(self.num_criteria):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Критерий {i+1}")
            name_input.setMinimumWidth(120)
            
            grid_layout.addWidget(QLabel(f"Крит.{i+1}:"), i+1, 0)
            grid_layout.addWidget(name_input, i+1, 1)
            self.criteria_inputs_fuzzy.append(name_input)
        
        # Ввод степеней соответствия
        self.compliance_inputs_fuzzy = []
        for i in range(self.num_compliance_degrees):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Степень {i+1}")
            name_input.setMinimumWidth(120)
            
            grid_layout.addWidget(QLabel(f"Степ.{i+1}:"), i+1, 2)
            grid_layout.addWidget(name_input, i+1, 3)
            self.compliance_inputs_fuzzy.append(name_input)
        
        # Ввод альтернатив
        self.alternative_inputs_fuzzy = []
        for i in range(self.num_alternatives):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Альтернатива {i+1}")
            name_input.setMinimumWidth(120)
            
            grid_layout.addWidget(QLabel(f"Альт.{i+1}:"), i+1, 4)
            grid_layout.addWidget(name_input, i+1, 5)
            self.alternative_inputs_fuzzy.append(name_input)
        
        step3_layout.addWidget(grid_widget)
        
        # Кнопка Далее с проверкой
        self.next_btn3 = QPushButton("Далее")
        self.next_btn3.clicked.connect(self.check_and_go_to_step4_fuzzy_systems)
        step3_layout.addWidget(self.next_btn3, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step3_group)
        self.update_window_size()

    def check_and_go_to_step4_fuzzy_systems(self):
        """Проверка данных и переход к четвертому шагу для нечетких систем"""
        # Проверка уникальности названий критериев
        criteria_names = [inp.text() or f"Критерий {i+1}" for i, inp in enumerate(self.criteria_inputs_fuzzy)]
        if len(criteria_names) != len(set(criteria_names)):
            QMessageBox.warning(self, "Ошибка", "Названия критериев должны быть уникальными")
            return
        
        # Проверка уникальности названий степеней соответствия
        compliance_names = [inp.text() or f"Степень {i+1}" for i, inp in enumerate(self.compliance_inputs_fuzzy)]
        if len(compliance_names) != len(set(compliance_names)):
            QMessageBox.warning(self, "Ошибка", "Названия степеней соответствия должны быть уникальными")
            return
        
        # Проверка уникальности названий альтернатив
        alternative_names = [inp.text() or f"Альтернатива {i+1}" for i, inp in enumerate(self.alternative_inputs_fuzzy)]
        if len(alternative_names) != len(set(alternative_names)):
            QMessageBox.warning(self, "Ошибка", "Названия альтернатив должны быть уникальными")
            return

        # Сохраняем данные
        self.criteria_names = criteria_names
        self.compliance_names = compliance_names
        self.alternative_names = alternative_names
        
        # Деактивируем третий шаг
        self.deactivate_group(self.step3_group)
        self.next_btn3.setEnabled(False)
        
        # Переходим к четвертому шагу
        self.init_step4_fuzzy_systems()
        self.current_step = 4
        self.schedule_resize_update()

    def init_step4_fuzzy_systems(self):
        """Четвертый шаг для нечетких систем: таблицы принадлежности"""
        self.step4_group = QGroupBox("Шаг 4: Степени принадлежности и характеристики")
        step4_layout = QVBoxLayout(self.step4_group)
        step4_layout.setContentsMargins(15, 15, 15, 15)
        
        # Таблица принадлежности альтернатив критериям
        membership_group = QGroupBox("Степени принадлежности альтернатив критериям")
        membership_layout = QVBoxLayout(membership_group)
        
        # Кнопка загрузки из CSV
        membership_load_layout = QHBoxLayout()
        membership_load_btn = QPushButton("Загрузить степени принадлежности из CSV")
        membership_load_layout.addWidget(membership_load_btn)
        membership_load_layout.addStretch()
        membership_layout.addLayout(membership_load_layout)
        
        # Создаем таблицу принадлежности (строки - критерии, столбцы - альтернативы)
        self.membership_table = QTableWidget(self.num_criteria, self.num_alternatives)
        self.membership_table.setHorizontalHeaderLabels(self.alternative_names)
        self.membership_table.setVerticalHeaderLabels(self.criteria_names)
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.membership_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту
        table_height = self.num_criteria * self.ROW_HEIGHT + 40
        self.membership_table.setMinimumHeight(table_height)
        self.membership_table.setMaximumHeight(max(table_height, 500))
        
        table_width = self.num_alternatives * self.COLUMN_WIDTH + 40
        self.membership_table.setMinimumWidth(table_width)
        self.membership_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем таблицу пустыми значениями
        for row in range(self.membership_table.rowCount()):
            for col in range(self.membership_table.columnCount()):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.membership_table.setItem(row, col, item)
        
        self.membership_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        membership_layout.addWidget(self.membership_table)
        step4_layout.addWidget(membership_group)
        
        # Привязываем кнопку загрузки
        membership_load_btn.clicked.connect(lambda: self.load_table_from_csv(self.membership_table))
        
        # Таблица характеристик степеней соответствия
        compliance_group = QGroupBox("Характеристики степеней соответствия")
        compliance_layout = QVBoxLayout(compliance_group)
        
        # Кнопка загрузки из CSV
        compliance_load_layout = QHBoxLayout()
        compliance_load_btn = QPushButton("Загрузить характеристики из CSV")
        compliance_load_layout.addWidget(compliance_load_btn)
        compliance_load_layout.addStretch()
        compliance_layout.addLayout(compliance_load_layout)
        
        # Создаем таблицу характеристик (3 строки, столбцы - степени соответствия)
        self.compliance_chars_table = QTableWidget(3, self.num_compliance_degrees)
        self.compliance_chars_table.setHorizontalHeaderLabels(self.compliance_names)
        self.compliance_chars_table.setVerticalHeaderLabels(["Старт", "Пик", "Конец"])
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.compliance_chars_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту
        table_height = 3 * self.ROW_HEIGHT + 40
        self.compliance_chars_table.setMinimumHeight(table_height)
        self.compliance_chars_table.setMaximumHeight(table_height)
        
        table_width = self.num_compliance_degrees * self.COLUMN_WIDTH + 40
        self.compliance_chars_table.setMinimumWidth(table_width)
        self.compliance_chars_table.setMaximumWidth(table_width)
        
        # Заполняем таблицу пустыми значениями
        for row in range(3):
            for col in range(self.num_compliance_degrees):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.compliance_chars_table.setItem(row, col, item)
        
        self.compliance_chars_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        compliance_layout.addWidget(self.compliance_chars_table)
        step4_layout.addWidget(compliance_group)
        
        # Привязываем кнопку загрузки
        compliance_load_btn.clicked.connect(lambda: self.load_table_from_csv(self.compliance_chars_table))
        
        # Кнопка Далее
        self.next_btn4 = QPushButton("Далее")
        self.next_btn4.clicked.connect(self.check_and_go_to_step5_fuzzy_systems)
        step4_layout.addWidget(self.next_btn4, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step4_group)
        self.update_window_size()

    def check_and_go_to_step5_fuzzy_systems(self):
        """Проверка данных и переход к пятому шагу для нечетких систем"""
        if not self.validate_table_data(self.membership_table, "значений принадлежности"):
            return
        
        if not self.validate_table_data(self.compliance_chars_table, "значений важности"):
            return
        
        # Проверяем таблицу принадлежности
        for row in range(self.membership_table.rowCount()):
            for col in range(self.membership_table.columnCount()):
                item = self.membership_table.item(row, col)
                if not item or not item.text().strip():
                    QMessageBox.warning(self, "Ошибка", "Не все степени принадлежности заполнены")
                    return
                try:
                    value = float(item.text())
                    if value < 0 or value > 1:
                        QMessageBox.warning(self, "Ошибка", 
                                          "Степени принадлежности должны быть в диапазоне [0, 1]")
                        return
                except ValueError:
                    QMessageBox.warning(self, "Ошибка", 
                                      "Степени принадлежности должны быть числами")
                    return
        
        # Проверяем таблицу характеристик степеней соответствия
        if not self.validate_compliance_characteristics():
            return
        
        # Собираем данные из таблиц
        self.collect_fuzzy_systems_data_step4()
        
        # Деактивируем четвертый шаг
        self.deactivate_group(self.step4_group)
        self.next_btn4.setEnabled(False)
        
        # Переходим к пятому шагу
        self.init_step5_fuzzy_systems()
        self.current_step = 5
        self.schedule_resize_update()

    def validate_compliance_characteristics(self):
        """Проверяет корректность характеристик степеней соответствия"""
        for col in range(self.compliance_chars_table.columnCount()):
            # Получаем значения из трех строк
            start_item = self.compliance_chars_table.item(0, col)
            peak_item = self.compliance_chars_table.item(1, col)
            end_item = self.compliance_chars_table.item(2, col)
            
            # Проверяем, что все ячейки заполнены
            if not start_item or not start_item.text().strip():
                QMessageBox.warning(self, "Ошибка", 
                                  f"Не заполнено значение 'Старт' для степени соответствия '{self.compliance_names[col]}'")
                return False
            if not peak_item or not peak_item.text().strip():
                QMessageBox.warning(self, "Ошибка", 
                                  f"Не заполнено значение 'Пик' для степени соответствия '{self.compliance_names[col]}'")
                return False
            if not end_item or not end_item.text().strip():
                QMessageBox.warning(self, "Ошибка", 
                                  f"Не заполнено значение 'Конец' для степени соответствия '{self.compliance_names[col]}'")
                return False
            
            try:
                # Преобразуем в числа
                start_val = float(start_item.text())
                peak_val = float(peak_item.text())
                end_val = float(end_item.text())
                
                # Проверяем условие: старт <= пик <= конец
                if start_val > peak_val:
                    QMessageBox.warning(self, "Ошибка", 
                                    f"Для степени соответствия '{self.compliance_names[col]}': 'Старт' ({start_val}) > 'Пик' ({peak_val})")
                    return False
                if peak_val > end_val:
                    QMessageBox.warning(self, "Ошибка", 
                                    f"Для степени соответствия '{self.compliance_names[col]}': 'Пик' ({peak_val}) > 'Конец' ({end_val})")
                    return False
                    
            except ValueError:
                QMessageBox.warning(self, "Ошибка", 
                                f"Для степени соответствия '{self.compliance_names[col]}': значения должны быть числами")
                return False
        
        return True

    def collect_fuzzy_systems_data_step4(self):
        """Собирает данные для нечетких систем на 4 этапе"""
        # Данные таблицы принадлежности
        self.membership_data = {}
        for row in range(self.membership_table.rowCount()):
            criterion_name = self.criteria_names[row]
            row_data = []
            for col in range(self.membership_table.columnCount()):
                item = self.membership_table.item(row, col)
                value = float(item.text()) if item else 0.0
                row_data.append(value)
            self.membership_data[criterion_name] = row_data
        
        # Данные таблицы характеристик
        self.compliance_characteristics = {}
        for col in range(self.compliance_chars_table.columnCount()):
            compliance_name = self.compliance_names[col]
            start_val = float(self.compliance_chars_table.item(0, col).text())
            peak_val = float(self.compliance_chars_table.item(1, col).text())
            end_val = float(self.compliance_chars_table.item(2, col).text())
            self.compliance_characteristics[compliance_name] = {
                'start': start_val,
                'peak': peak_val,
                'end': end_val
            }

    def init_step5_fuzzy_systems(self):
        """Пятый шаг для нечетких систем: ввод правил"""
        self.step5_group = QGroupBox("Шаг 5: Правила нечеткой системы")
        step5_layout = QVBoxLayout(self.step5_group)
        step5_layout.setContentsMargins(15, 15, 15, 15)
        
        info_label = QLabel("Задайте правила системы. Каждое правило должно иметь уникальную комбинацию степеней соответствия для критериев.")
        info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        info_label.setWordWrap(True)
        step5_layout.addWidget(info_label)
        
        # Создаем таблицу правил
        self.rules_table = QTableWidget(self.num_rules, self.num_criteria + 1)
        
        # Устанавливаем заголовки
        headers = self.criteria_names + ["Результат"]
        self.rules_table.setHorizontalHeaderLabels(headers)
        
        # Устанавливаем вертикальные заголовки (номера правил)
        rule_headers = [f"Правило {i+1}" for i in range(self.num_rules)]
        self.rules_table.setVerticalHeaderLabels(rule_headers)
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.rules_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту
        table_height = self.num_rules * self.ROW_HEIGHT + 40
        self.rules_table.setMinimumHeight(table_height)
        self.rules_table.setMaximumHeight(max(table_height, 500))
        
        table_width = (self.num_criteria + 1) * self.COLUMN_WIDTH + 40
        self.rules_table.setMinimumWidth(table_width)
        self.rules_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем таблицу комбобоксами
        for row in range(self.num_rules):
            for col in range(self.num_criteria + 1):
                combo = QComboBox()
                combo.addItems(self.compliance_names)
                combo.setCurrentIndex(0)
                combo.setMinimumWidth(self.COLUMN_WIDTH)
                self.rules_table.setCellWidget(row, col, combo)
        
        step5_layout.addWidget(self.rules_table)
        
        # Кнопка завершения
        self.final_btn_fuzzy = QPushButton("Завершить ввод данных")
        self.final_btn_fuzzy.clicked.connect(self.finalize_fuzzy_systems_data_input)
        step5_layout.addWidget(self.final_btn_fuzzy, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step5_group)
        self.update_window_size()

    def finalize_fuzzy_systems_data_input(self):
        """Завершает ввод данных для нечетких систем"""
        # Проверяем уникальность правил
        if not self.validate_rules_uniqueness():
            return
        
        # Собираем данные правил
        self.collect_rules_data()
        
        # Сохраняем все данные задачи
        task_data = self.save_fuzzy_systems_task_data()
        
        # Передаем данные в основное окно
        if self.parent:
            self.parent.on_third_task_completed(task_data)
        
        # Деактивируем пятый шаг
        self.deactivate_group(self.step5_group)
        self.final_btn_fuzzy.setEnabled(False)
        
        # Завершаем ввод
        QMessageBox.information(self, "Успех", "Все данные успешно введены и сохранены!")
        self.accept()

    def validate_rules_uniqueness(self):
        """Проверяет уникальность комбинаций правил"""
        rules_combinations = set()
        
        for row in range(self.num_rules):
            rule_combination = []
            
            # Собираем комбинацию для всех критериев (исключая результат)
            for col in range(self.num_criteria):
                combo = self.rules_table.cellWidget(row, col)
                rule_combination.append(combo.currentText())
            
            # Преобразуем в кортеж для хранения в множестве
            rule_tuple = tuple(rule_combination)
            
            # Проверяем, была ли уже такая комбинация
            if rule_tuple in rules_combinations:
                QMessageBox.warning(self, "Ошибка", 
                                  f"Правило {row+1} имеет такую же комбинацию критериев, как и другое правило. Все комбинации должны быть уникальными.")
                return False
            
            rules_combinations.add(rule_tuple)
        
        return True

    def collect_rules_data(self):
        """Собирает данные правил из таблицы"""
        self.rules_data = []
        
        for row in range(self.num_rules):
            rule = {}
            
            # Критерии
            for col in range(self.num_criteria):
                criterion_name = self.criteria_names[col]
                combo = self.rules_table.cellWidget(row, col)
                rule[criterion_name] = combo.currentText()
            
            # Результат
            result_combo = self.rules_table.cellWidget(row, self.num_criteria)
            rule['result'] = result_combo.currentText()
            
            self.rules_data.append(rule)

    def save_fuzzy_systems_task_data(self):
        """Сохраняет все данные задачи для нечетких систем"""
        # Преобразуем данные в DataFrame
        membership_df = pd.DataFrame(self.membership_data, index=self.alternative_names)
        
        compliance_chars_df = self.triangular_data_to_dataframe(
            self.compliance_characteristics, self.compliance_names
        )
        
        # Создаем DataFrame для правил
        rules_list = []
        for rule in self.rules_data:
            rule_dict = {}
            for criterion in self.criteria_names:
                rule_dict[criterion] = rule[criterion]
            rule_dict['result'] = rule['result']
            rules_list.append(rule_dict)
        
        rules_df = pd.DataFrame(rules_list)
        
        task_data = {
            'task_type': self.task_type,
            'basic_parameters': {
                'num_criteria': self.num_criteria,
                'num_compliance_degrees': self.num_compliance_degrees,
                'num_alternatives': self.num_alternatives,
                'num_rules': self.num_rules
            },
            'names': {
                'criteria_names': self.criteria_names,
                'compliance_names': self.compliance_names,
                'alternative_names': self.alternative_names
            },
            'membership_data': membership_df,
            'compliance_characteristics': compliance_chars_df,
            'rules': rules_df
        }
        
        return task_data

    """Рабочие методы"""
    def validate_table_data(self, table, table_name):
        """Проверяет корректность заполнения таблицы"""
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item = table.item(row, col)
                
                # Проверка на пустые значения
                if table_name != "матрицы отклонений" or col > row:
                    if not item or not item.text().strip():
                        QMessageBox.warning(
                            self, 
                            "Ошибка заполнения", 
                            f"Таблица {table_name} содержит пустые значения.\n"
                            f"Заполните все ячейки перед продолжением."
                        )
                        return False
                    
                # Проверка на числовые значения (для всех таблиц кроме экспертных на шаге 4)
                if table_name != "матрицы отклонений" or col > row:
                    try:
                        float(item.text())
                    except ValueError:
                        QMessageBox.warning(
                            self,
                            "Ошибка заполнения",
                            f"Таблица {table_name} содержит нечисловые значения.\n"
                            f"Строка {row+1}, столбец {col+1}: '{item.text()}'\n"
                            f"Все значения должны быть числами."
                        )
                        return False
        
        return True

    def calculate_table_width(self, table):
        """Рассчитывает минимальную ширину таблицы на основе заголовков и содержимого"""
        width = 0
        
        # Ширина вертикального заголовка
        if table.verticalHeader().isVisible():
            width += table.verticalHeader().width()
        
        # Ширина всех столбцов (минимум по 100px на столбец)
        column_count = table.columnCount()
        width += max(column_count * self.COLUMN_WIDTH, table.horizontalHeader().length())
        
        # Добавляем отступы и рамки
        width += 20  # рамки и отступы
        
        return width

    def adjust_all_tables(self):
        """Настраивает все таблицы после изменения размера окна"""
        tables = self.scroll_content.findChildren(QTableWidget)
        for table in tables:
            if table.isEnabled():
                # Принудительно обновляем размеры столбцов
                table.horizontalHeader().resizeSections(QHeaderView.ResizeMode.Stretch)
                
                # Обновляем минимальную ширину таблицы
                min_width = self.calculate_table_width(table)
                table.setMinimumWidth(min_width)

    def update_window_size(self):
        """Обновление размеров окна с учетом ширины таблиц"""
        self.scroll_content.layout().activate()
        self.scroll_content.updateGeometry()
        
        content_size = self.scroll_content.sizeHint()
        min_width = 900
        min_height = 300
        max_height = 1000
        max_width = 1800
        
        # РАССЧИТЫВАЕМ ТРЕБУЕМУЮ ШИРИНУ НА ОСНОВЕ СОДЕРЖИМОГО
        required_width = content_size.width() + 100
        
        # УЧИТЫВАЕМ ШИРИНУ САМОЙ ШИРОКОЙ ТАБЛИЦЫ
        tables = self.scroll_content.findChildren(QTableWidget)
        if tables:
            for table in tables:
                table_width = self.calculate_table_width(table)
                required_width = max(required_width, table_width + 100)
        
        new_width = min(max_width, max(min_width, required_width))
        new_height = min(max_height, max(min_height, content_size.height() + 100))
        
        self.setFixedSize(new_width, new_height)
        
        # ОБНОВЛЯЕМ РАЗМЕРЫ ТАБЛИЦ
        self.adjust_all_tables()
        
        # Обновляем политику прокрутки
        if content_size.height() + 40 > max_height:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def schedule_resize_update(self):
        """Запланировать обновление размеров с небольшой задержкой"""
        self.resize_timer.start(50)

    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        self.update_table_sizes()
        
        if event.size() != self.size():
            self.setFixedSize(self.size())
        super().resizeEvent(event)

    def update_table_sizes(self):
        """Обновляет размеры таблиц после изменения размера окна"""
        self.scroll_content.updateGeometry()
        self.update_window_size()