from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QCheckBox, QPushButton, QScrollArea,
                            QLabel, QLineEdit, QGroupBox, QSizePolicy, QDialog,
                            QGridLayout, QFrame, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QSpinBox, QDoubleSpinBox, QMessageBox,
                            QFileDialog, QButtonGroup, QRadioButton, QComboBox, QTabWidget)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QIcon
import pandas as pd
import numpy as np
import csv


class UDMTaskWindow(QDialog):
    COLUMN_WIDTH = 120
    ROW_HEIGHT = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Принятие решений в условиях неопределенности")
        self.setModal(True)
        
        # Переменные для хранения данных
        self.num_certain_criteria = 0
        self.num_uncertain_criteria = 0
        self.num_alternatives = 0
        
        self.certain_criteria_names = []
        self.uncertain_criteria_names = []
        self.alternative_names = []
        self.certain_weights = {}
        self.uncertain_weights = {}
        
        self.environment_states = {}  # {criterion_name: [state_names]}
        self.prior_information = {}   # {criterion_name: situation_type}
        self.probabilities = {}       # {criterion_name: [probabilities]}
        self.uncertainty_methods = {}  # {criterion_name: method_data}

        
        self.normalization_methods = {}  # {criterion_name: method}
        self.direction_changes = {}      # {criterion_name: bool}
        self.direction_methods = {}      # {criterion_name: method}
        self.savige_max_values = {}      # {criterion_name: max_value}
        
        # Данные таблиц
        self.certain_table_data = None
        self.uncertain_tables_data = {}
        
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
            QLineEdit, QSpinBox, QDoubleSpinBox {
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px;
                font-size: 10px;
                background: white;
                min-height: 20px;
                max-height: 25px;
            }
            QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
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
        title_label = QLabel("Принятие решений в условиях неопределенности")
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
        """Первый шаг: ввод основных параметров"""
        self.step1_group = QGroupBox("Шаг 1: Основные параметры")
        step1_layout = QGridLayout(self.step1_group)
        step1_layout.setSpacing(15)
        step1_layout.setContentsMargins(15, 15, 15, 15)
        
        # Критерии с определенностью
        certain_label = QLabel("Количество критериев с определенностью:")
        certain_label.setMinimumWidth(200)
        self.certain_spinbox = QSpinBox()
        self.certain_spinbox.setMinimum(0)
        self.certain_spinbox.setMaximum(20)
        self.certain_spinbox.setValue(4)
        self.certain_spinbox.setMinimumWidth(80)
        
        # Критерии с неопределенностью
        uncertain_label = QLabel("Количество критериев в условиях неопределенности:")
        uncertain_label.setMinimumWidth(200)
        self.uncertain_spinbox = QSpinBox()
        self.uncertain_spinbox.setMinimum(0)
        self.uncertain_spinbox.setMaximum(20)
        self.uncertain_spinbox.setValue(3)
        self.uncertain_spinbox.setMinimumWidth(80)
        
        # Альтернативы
        alternatives_label = QLabel("Количество альтернатив:")
        alternatives_label.setMinimumWidth(200)
        self.alternatives_spinbox = QSpinBox()
        self.alternatives_spinbox.setMinimum(1)
        self.alternatives_spinbox.setMaximum(20)
        self.alternatives_spinbox.setValue(7)
        self.alternatives_spinbox.setMinimumWidth(80)
        
        # Располагаем элементы в сетке
        step1_layout.addWidget(certain_label, 0, 0)
        step1_layout.addWidget(self.certain_spinbox, 0, 1)
        step1_layout.addWidget(uncertain_label, 0, 2)
        step1_layout.addWidget(self.uncertain_spinbox, 0, 3)
        step1_layout.addWidget(alternatives_label, 1, 1)
        step1_layout.addWidget(self.alternatives_spinbox, 1, 2)
        
        # Кнопка Далее
        self.next_btn1 = QPushButton("Далее")
        self.next_btn1.clicked.connect(self.go_to_step2)
        step1_layout.addWidget(self.next_btn1, 2, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step1_group)
        self.update_window_size()

    def go_to_step2(self):
        """Переход ко второму шагу"""
        # Сохраняем значения
        self.num_certain_criteria = self.certain_spinbox.value()
        self.num_uncertain_criteria = self.uncertain_spinbox.value()
        self.num_alternatives = self.alternatives_spinbox.value()
        
        # Проверяем, что есть хотя бы один критерий
        if self.num_certain_criteria + self.num_uncertain_criteria == 0:
            QMessageBox.warning(self, "Ошибка", "Должен быть хотя бы один критерий (определенный или неопределенный)")
            return
        
        # Деактивируем первый шаг
        self.deactivate_group(self.step1_group)
        self.next_btn1.setEnabled(False)
        
        # Инициализируем второй шаг
        self.init_step2()
        self.current_step = 2
        
        # Обновляем размер окна
        self.schedule_resize_update()

    def init_step2(self):
        """Второй шаг: ввод имен и весов"""
        self.step2_group = QGroupBox("Шаг 2: Имена и веса критериев")
        step2_layout = QVBoxLayout(self.step2_group)
        step2_layout.setContentsMargins(15, 15, 15, 15)
        
        # Сетка для ввода данных
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(10)
        grid_layout.setHorizontalSpacing(20)
        
        # Заголовки столбцов
        headers = ["Критерии с определенностью", "Критерии с неопределенностью", "Альтернативы"]
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setStyleSheet("""
                font-weight: bold; 
                color: #2c3e50; 
                font-size: 11px;
                background: #e8f4fc;
                padding: 8px;
                border-radius: 4px;
            """)
            grid_layout.addWidget(label, 0, col * 3, 1, 3, Qt.AlignmentFlag.AlignCenter)
        
        # Рассчитываем вес по умолчанию
        total_criteria = self.num_certain_criteria + self.num_uncertain_criteria
        default_weight = 1.0 / total_criteria if total_criteria > 0 else 0.0
        
        # Ввод критериев с определенностью
        self.certain_inputs = []
        for i in range(self.num_certain_criteria):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Критерий {i+1}")
            name_input.setMinimumWidth(120)
            
            weight_input = QDoubleSpinBox()
            weight_input.setRange(0.0, 1.0)
            weight_input.setSingleStep(0.01)
            weight_input.setDecimals(3)
            weight_input.setValue(default_weight)
            weight_input.setPrefix("Вес: ")
            weight_input.setMinimumWidth(80)
            
            grid_layout.addWidget(QLabel(f"Опр.{i+1}:"), i+1, 0)
            grid_layout.addWidget(name_input, i+1, 1)
            grid_layout.addWidget(weight_input, i+1, 2)
            self.certain_inputs.append((name_input, weight_input))
        
        # Ввод критериев с неопределенностью
        self.uncertain_inputs = []
        for i in range(self.num_uncertain_criteria):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Критерий {self.num_certain_criteria + i + 1}")
            name_input.setMinimumWidth(120)
            
            weight_input = QDoubleSpinBox()
            weight_input.setRange(0.0, 1.0)
            weight_input.setSingleStep(0.01)
            weight_input.setDecimals(3)
            weight_input.setValue(default_weight)
            weight_input.setPrefix("Вес: ")
            weight_input.setMinimumWidth(80)
            
            grid_layout.addWidget(QLabel(f"Неопр.{i+1}:"), i+1, 3)
            grid_layout.addWidget(name_input, i+1, 4)
            grid_layout.addWidget(weight_input, i+1, 5)
            self.uncertain_inputs.append((name_input, weight_input))
        
        # Ввод альтернатив
        self.alternative_inputs = []
        for i in range(self.num_alternatives):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Альтернатива {i+1}")
            name_input.setMinimumWidth(120)
            
            grid_layout.addWidget(QLabel(f"Альт.{i+1}:"), i+1, 6)
            grid_layout.addWidget(name_input, i+1, 7)
            self.alternative_inputs.append(name_input)
        
        # Информация о весах
        weight_info = QLabel(f"Сумма всех весов ({self.num_certain_criteria + self.num_uncertain_criteria} критериев) должна быть равна 1.0")
        weight_info.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 10px;")
        step2_layout.addWidget(weight_info)
        
        step2_layout.addWidget(grid_widget)
        
        # Кнопка Далее с проверкой весов
        self.next_btn2 = QPushButton("Далее")
        self.next_btn2.clicked.connect(self.check_weights_and_go_to_step3)
        step2_layout.addWidget(self.next_btn2, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step2_group)
        self.update_window_size()

    def check_weights_and_go_to_step3(self):
        """Проверка суммы весов и переход к следующему шагу"""
        # Проверка суммы всех весов
        total_sum = (sum(inp[1].value() for inp in self.certain_inputs) + 
                    sum(inp[1].value() for inp in self.uncertain_inputs))
        
        if abs(total_sum - 1.0) > 0.001:
            QMessageBox.warning(self, "Ошибка", 
                               f"Сумма всех весов должна быть равна 1.0\nТекущая сумма: {total_sum:.3f}")
            return
        
        # Проверка уникальности названий альтернатив
        alternative_names = [inp.text() or f"Альтернатива {i+1}" for i, inp in enumerate(self.alternative_inputs)]
        if len(alternative_names) != len(set(alternative_names)):
            QMessageBox.warning(self, "Ошибка", "Названия альтернатив должны быть уникальными")
            return
        
        # Проверка уникальности названий критериев
        certain_names = [inp[0].text() or f"Критерий {i+1}" for i, inp in enumerate(self.certain_inputs)]
        uncertain_names = [inp[0].text() or f"Критерий {self.num_certain_criteria+i+1}" for i, inp in enumerate(self.uncertain_inputs)]
        
        all_criteria_names = certain_names + uncertain_names
        if len(all_criteria_names) != len(set(all_criteria_names)):
            QMessageBox.warning(self, "Ошибка", "Названия критериев должны быть уникальными")
            return

        # Деактивируем второй шаг
        self.deactivate_group(self.step2_group)
        self.next_btn2.setEnabled(False)

        self.go_to_step3()

    def go_to_step3(self):
        """Переход к третьему шагу"""
        # Сохраняем данные
        self.certain_criteria_names = [inp[0].text() or f"Критерий {i+1}" for i, inp in enumerate(self.certain_inputs)]
        self.certain_weights = {inp[0].text() or f"Критерий {i+1}": inp[1].value() for i, inp in enumerate(self.certain_inputs)}
        self.uncertain_criteria_names = [inp[0].text() or f"Критерий {self.num_certain_criteria+i+1}" for i, inp in enumerate(self.uncertain_inputs)]
        self.uncertain_weights = {inp[0].text() or f"Критерий {self.num_certain_criteria+i+1}": inp[1].value() for i, inp in enumerate(self.uncertain_inputs)}
        self.alternative_names = [inp.text() or f"Альтернатива {i+1}" for i, inp in enumerate(self.alternative_inputs)]
        
        self.init_step3()
        self.current_step = 3
        
        # Обновляем размер окна
        self.schedule_resize_update()

    def init_step3(self):
        """Третий шаг: таблица значений определенных критериев"""
        self.step3_group = QGroupBox("Шаг 3: Значения критериев с определенностью")
        step3_layout = QVBoxLayout(self.step3_group)
        step3_layout.setContentsMargins(15, 15, 15, 15)
        
        info_label = QLabel("Заполните таблицу значений для критериев с определенностью. Используйте кнопку для загрузки данных из CSV файла.")
        info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        step3_layout.addWidget(info_label)
        
        # Кнопка загрузки из CSV
        load_btn_layout = QHBoxLayout()
        load_csv_btn = QPushButton("Загрузить из CSV")
        load_csv_btn.clicked.connect(lambda: self.load_table_from_csv(self.certain_table, 'certain'))
        load_btn_layout.addWidget(load_csv_btn)
        load_btn_layout.addStretch()
        step3_layout.addLayout(load_btn_layout)
        
        # Создаем таблицу
        self.certain_table = QTableWidget(self.num_certain_criteria, self.num_alternatives)
        
        # Устанавливаем заголовки
        horizontal_headers = self.alternative_names
        vertical_headers = self.certain_criteria_names
        self.certain_table.setHorizontalHeaderLabels(horizontal_headers)
        self.certain_table.setVerticalHeaderLabels(vertical_headers)
        
        # Настраиваем внешний вид
        self.setup_table_appearance(self.certain_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту для таблицы
        table_height = self.num_certain_criteria * self.ROW_HEIGHT + 40
        self.certain_table.setMinimumHeight(table_height)
        self.certain_table.setMaximumHeight(max(table_height, 500))

        table_width = self.num_alternatives * self.COLUMN_WIDTH + 40
        self.certain_table.setMinimumWidth(table_width)
        self.certain_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем таблицу пустыми значениями
        for row in range(self.num_certain_criteria):
            for col in range(self.num_alternatives):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.certain_table.setItem(row, col, item)
        self.certain_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        step3_layout.addWidget(self.certain_table)

        # Кнопка Далее
        self.next_btn3 = QPushButton("Далее")
        self.next_btn3.clicked.connect(self.go_to_step4)
        step3_layout.addWidget(self.next_btn3, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step3_group)
        self.update_window_size()

    def load_table_from_csv(self, table, mode):
        """Загрузка данных в таблицу из CSV файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
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
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")

    def go_to_step4(self):
        """Переход к четвертому шагу"""
        if not self.validate_table_data(self.certain_table, "определенных значений"):
            return
        
        # Деактивируем третий шаг
        self.deactivate_group(self.step3_group)
        self.next_btn3.setEnabled(False)

        self.init_step4()
        self.current_step = 4
        
        # Обновляем размер окна
        self.schedule_resize_update()

    def init_step4(self):
        """Четвертый шаг: настройки критериев с неопределенностью"""
        self.step4_group = QGroupBox("Шаг 4: Настройки критериев с неопределенностью")
        step4_layout = QVBoxLayout(self.step4_group)
        step4_layout.setContentsMargins(15, 15, 15, 15)
        
        self.uncertain_criteria_widgets = {}
        
        for i, criterion_name in enumerate(self.uncertain_criteria_names):
            criterion_group = QGroupBox(f"Критерий: {criterion_name}")
            criterion_layout = QVBoxLayout(criterion_group)
            
            # Количество состояний среды
            states_layout = QHBoxLayout()
            states_label = QLabel("Количество состояний среды:")
            self.states_spinbox = QSpinBox()
            self.states_spinbox.setMinimum(1)
            self.states_spinbox.setMaximum(10)
            self.states_spinbox.setValue(3)
            self.states_spinbox.valueChanged.connect(lambda value, name=criterion_name: self.update_state_inputs(name, value))
            
            states_layout.addWidget(states_label)
            states_layout.addWidget(self.states_spinbox)
            states_layout.addStretch()
            criterion_layout.addLayout(states_layout)
            
            # Поля для имен состояний среды
            self.states_container = QWidget()
            self.states_layout = QVBoxLayout(self.states_container)
            criterion_layout.addWidget(self.states_container)
            
            # ComboBox для ситуации априорной информированности
            situation_layout = QHBoxLayout()
            situation_label = QLabel("Ситуация априорной информированности:")
            self.situation_combo = QComboBox()
            self.situation_combo.addItems([
                "Ситуация 1: Полная определенность",
                "Ситуация 2: Неопределенность", 
                "Ситуация 3: Риск"
            ])
            self.situation_combo.currentTextChanged.connect(lambda text, name=criterion_name: self.on_situation_changed(name, text))
            
            situation_layout.addWidget(situation_label)
            situation_layout.addWidget(self.situation_combo)
            situation_layout.addStretch()
            criterion_layout.addLayout(situation_layout)
            
            # Контейнер для вероятностей (изначально скрыт)
            self.probabilities_container = QWidget()
            self.probabilities_layout = QVBoxLayout(self.probabilities_container)
            self.probabilities_container.hide() 
            criterion_layout.addWidget(self.probabilities_container)
            
            # Сохраняем виджеты для этого критерия
            self.uncertain_criteria_widgets[criterion_name] = {
                'states_spinbox': self.states_spinbox,
                'states_container': self.states_container,
                'states_inputs': [],
                'situation_combo': self.situation_combo,
                'probabilities_container': self.probabilities_container,
                'probabilities_inputs': []
            }

            # Инициализируем поля для состояний
            self.update_state_inputs(criterion_name, self.states_spinbox.value())
            #print("init_yes")
            #self.on_situation_changed(criterion_name, "Ситуация 1: Полная определенность")
            
            step4_layout.addWidget(criterion_group)
        
        # Кнопка Далее
        self.next_btn4 = QPushButton("Далее")
        self.next_btn4.clicked.connect(self.check_step4_and_go_to_step5)
        step4_layout.addWidget(self.next_btn4, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step4_group)
        self.update_window_size()

    def update_state_inputs(self, criterion_name, num_states):
        """Обновляет поля для ввода имен состояний среды"""
        widgets = self.uncertain_criteria_widgets[criterion_name]
        container = widgets['states_container']
        inputs = widgets['states_inputs']
        situation = widgets['situation_combo'].currentText()

        # Очищаем старые поля
        #for input_field in inputs:
        #    input_field.deleteLater()
        inputs.clear()

        while container.layout().count():
            child = container.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # Очищаем вложенный layout
                sub_layout = child.layout()
                while sub_layout.count():
                    sub_child = sub_layout.takeAt(0)
                    if sub_child.widget():
                        sub_child.widget().deleteLater()
        
        # Создаем новые поля
        for i in range(num_states):
            state_layout = QHBoxLayout()
            state_label = QLabel(f"Состояние {i+1}:")
            state_input = QLineEdit()
            state_input.setPlaceholderText(f"Состояние {i+1}")
            state_input.setMinimumWidth(150)
            
            state_layout.addWidget(state_label)
            state_layout.addWidget(state_input)
            state_layout.addStretch()
            
            container.layout().addLayout(state_layout)
            inputs.append(state_input)
        
        # Обновляем поля вероятностей если они видны
        self.update_probability_inputs(criterion_name, num_states)
        #self.on_situation_changed(criterion_name, situation)

    def on_situation_changed(self, criterion_name, situation_text):
        """Обработчик изменения ситуации априорной информированности"""
        widgets = self.uncertain_criteria_widgets[criterion_name]
        #print(criterion_name)
        #print(situation_text)
        
        if situation_text in ["Ситуация 1: Полная определенность", "Ситуация 3: Риск"]:
            # Показываем поля для вероятностей
            widgets['probabilities_container'].show()
            #print(f"Sit {situation_text}: {widgets['probabilities_container'].isVisible()}")
            num_states = widgets['states_spinbox'].value()
            self.update_probability_inputs(criterion_name, num_states)
        else:
            # Скрываем поля для вероятностей
            container = widgets['probabilities_container']
            while container.layout().count():
                child = container.layout().takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                elif child.layout():
                    # Очищаем вложенный layout
                    sub_layout = child.layout()
                    while sub_layout.count():
                        sub_child = sub_layout.takeAt(0)
                        if sub_child.widget():
                            sub_child.widget().deleteLater()

            widgets['probabilities_container'].hide()

    def update_probability_inputs(self, criterion_name, num_states):
        """Обновляет поля для ввода вероятностей"""
        widgets = self.uncertain_criteria_widgets[criterion_name]
        container = widgets['probabilities_container']
        inputs = widgets['probabilities_inputs']
        situation = widgets['situation_combo'].currentText()
        #print("hoo")
        # Очищаем старые поля
        #for input_field in inputs:
        #    input_field.deleteLater()
        inputs.clear()
        while container.layout().count():
            child = container.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                # Очищаем вложенный layout
                sub_layout = child.layout()
                while sub_layout.count():
                    sub_child = sub_layout.takeAt(0)
                    if sub_child.widget():
                        sub_child.widget().deleteLater()
        #print(container.isVisible())
        # Создаем новые поля только если контейнер видим
        #print(situation)
        if situation in ["Ситуация 1: Полная определенность", "Ситуация 3: Риск"]:#container.isVisible():
            #print("I am in")
            prob_label = QLabel("Вероятности состояний среды:")
            prob_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            container.layout().addWidget(prob_label)
            
            #print(num_states)
            for i in range(num_states):
                prob_layout = QHBoxLayout()
                prob_label = QLabel(f"Вероятность {i+1}:")
                prob_input = QDoubleSpinBox()
                prob_input.setRange(0.0, 1.0)
                prob_input.setSingleStep(0.01)
                prob_input.setDecimals(3)
                prob_input.setValue(1.0 / num_states)
                prob_input.setMinimumWidth(100)
                
                prob_layout.addWidget(prob_label)
                prob_layout.addWidget(prob_input)
                prob_layout.addStretch()
                
                container.layout().addLayout(prob_layout)
                container.show()
                #while container.layout().count():
                #    child = container.layout().takeAt(0)
                #    print(child)
                inputs.append(prob_input)

    def check_step4_and_go_to_step5(self):
        """Проверка данных четвертого шага и переход к пятому"""
        # Проверяем уникальность имен состояний для каждого критерия
        for criterion_name in self.uncertain_criteria_names:
            widgets = self.uncertain_criteria_widgets[criterion_name]
            state_names = [inp.text() or f"Состояние {i+1}" for i, inp in enumerate(widgets['states_inputs'])]
            
            if len(state_names) != len(set(state_names)):
                QMessageBox.warning(self, "Ошибка", 
                                  f"Для критерия '{criterion_name}' названия состояний среды должны быть уникальными")
                return
        
        # Проверяем суммы вероятностей для ситуаций 1 и 3
        for criterion_name in self.uncertain_criteria_names:
            widgets = self.uncertain_criteria_widgets[criterion_name]
            situation = widgets['situation_combo'].currentText()
            
            if situation in ["Ситуация 1: Полная определенность", "Ситуация 3: Риск"]:
                total_prob = sum(inp.value() for inp in widgets['probabilities_inputs'])
                if abs(total_prob - 1.0) > 0.001:
                    QMessageBox.warning(self, "Ошибка", 
                                      f"Для критерия '{criterion_name}' сумма вероятностей должна быть равна 1.0\nТекущая сумма: {total_prob:.3f}")
                    return
        
        # Сохраняем данные четвертого шага
        self.save_step4_data()
        
        # Деактивируем четвертый шаг
        self.deactivate_group(self.step4_group)
        self.next_btn4.setEnabled(False)

        self.init_step5()
        self.current_step = 5
        
        # Обновляем размер окна
        self.schedule_resize_update()

    def save_step4_data(self):
        """Сохраняет данные из четвертого шага"""
        self.environment_states = {}
        self.prior_information = {}
        self.probabilities = {}
        
        for criterion_name in self.uncertain_criteria_names:
            widgets = self.uncertain_criteria_widgets[criterion_name]
            
            # Сохраняем состояния среды
            state_names = [inp.text() or f"Состояние {i+1}" for i, inp in enumerate(widgets['states_inputs'])]
            self.environment_states[criterion_name] = state_names
            
            # Сохраняем ситуацию априорной информированности
            self.prior_information[criterion_name] = widgets['situation_combo'].currentText()
            
            # Сохраняем вероятности (если применимо)
            if widgets['situation_combo'].currentText() in ["Ситуация 1: Полная определенность", "Ситуация 3: Риск"]:
                probs = {state_names[i]: inp.value() for i, inp in enumerate(widgets['probabilities_inputs'])}
                self.probabilities[criterion_name] = probs
            else:
                self.probabilities[criterion_name] = {}

    def init_step5(self):
        """Пятый шаг: таблицы значений для критериев с неопределенностью"""
        self.step5_group = QGroupBox("Шаг 5: Значения критериев с неопределенностью")
        step5_layout = QVBoxLayout(self.step5_group)
        step5_layout.setContentsMargins(15, 15, 15, 15)
        
        info_label = QLabel("Заполните таблицы значений для критериев с неопределенностью. Используйте кнопки для загрузки данных из CSV файлов.")
        info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        step5_layout.addWidget(info_label)
        
        self.uncertain_tables = {}
        self.method_widgets = {}  # Добавить этот словарь
        
        for criterion_name in self.uncertain_criteria_names:
            criterion_group = QGroupBox(f"Критерий: {criterion_name}")
            criterion_layout = QVBoxLayout(criterion_group)
            
            # Кнопка загрузки из CSV
            load_btn_layout = QHBoxLayout()
            load_csv_btn = QPushButton("Загрузить из CSV")
            load_csv_btn.clicked.connect(lambda checked, name=criterion_name: self.load_uncertain_table_from_csv(name))
            load_btn_layout.addWidget(load_csv_btn)
            load_btn_layout.addStretch()
            criterion_layout.addLayout(load_btn_layout)
            
            # Создаем таблицу
            num_states = len(self.environment_states[criterion_name])
            table = QTableWidget(num_states, self.num_alternatives)
            
            # Устанавливаем заголовки
            horizontal_headers = self.alternative_names
            vertical_headers = self.environment_states[criterion_name]
            table.setHorizontalHeaderLabels(horizontal_headers)
            table.setVerticalHeaderLabels(vertical_headers)
            
            # Настраиваем внешний вид
            self.setup_table_appearance(table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
            
            # Устанавливаем фиксированную высоту для таблицы
            table_height = num_states * self.ROW_HEIGHT + 40
            table.setMinimumHeight(table_height)
            table.setMaximumHeight(max(table_height, 500))

            table_width = self.num_alternatives * self.COLUMN_WIDTH + 40
            table.setMinimumWidth(table_width)
            table.setMaximumWidth(max(table_width, 500))
            
            # Заполняем таблицу пустыми значениями
            for row in range(num_states):
                for col in range(self.num_alternatives):
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(row, col, item)

            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            criterion_layout.addWidget(table)
            self.uncertain_tables[criterion_name] = table
            
            # ДОБАВИТЬ ЭТОТ БЛОК - выбор метода снятия неопределенности
            method_group = QGroupBox("Выбор метода снятия неопределенности")
            method_layout = QVBoxLayout(method_group)
            
            # ComboBox для выбора метода
            method_select_layout = QGridLayout()
            method_label = QLabel("Метод снятия неопределенности:")
            method_combo = QComboBox()
            
            # Заполняем методы в зависимости от ситуации априорной информированности
            situation = self.prior_information[criterion_name]
            if situation == "Ситуация 1: Полная определенность":
                methods = [
                    "Критерий Байеса-Лапласа",
                    "Критерий минимальной среднеквадратичной ошибки", 
                    "Критерий максимальной вероятности",
                    "Модальный критерий",
                    "Критерий минимума энтропии",
                    "Критерий Гермейера",
                    "Универсальный критерий"
                ]
            elif situation == "Ситуация 2: Неопределенность":
                methods = [
                    "Критерий Вальда",
                    "Критерий минимаксного Сэвиджа", 
                    "Универсальный критерий"
                ]
            else:  # Ситуация 3: Риск
                methods = [
                    "Критерий Гурвица",
                    "Критерий Ходжеса-Лемана",
                    "Универсальный критерий"
                ]
            
            method_combo.addItems(methods)
            method_combo.currentTextChanged.connect(
                lambda text, name=criterion_name, sit=situation: 
                self.on_method_changed(name, sit, text)
            )
            
            method_select_layout.addWidget(method_label, 0, 0)
            method_select_layout.addWidget(method_combo, 0, 1)
            #method_select_layout.addStretch()
            method_select_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            method_layout.addLayout(method_select_layout)
            
            # Контейнер для параметров метода (изначально пустой)
            params_container = QWidget()
            params_container.setObjectName(f"{criterion_name}_params_container")
            params_layout = QGridLayout(params_container)
            params_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
            method_layout.addWidget(params_container)
            
            criterion_layout.addWidget(method_group)
            
            # Сохраняем виджеты для этого критерия
            self.method_widgets[criterion_name] = {
                'method_combo': method_combo,
                'params_container': params_container
            }

            self.create_method_parameters_widget(criterion_name, situation, method_combo.currentText())
            params_container.show()
            
            step5_layout.addWidget(criterion_group)
        
        # Кнопка завершения
        self.finish_btn = QPushButton("Далее")
        self.finish_btn.clicked.connect(self.go_to_step6)
        step5_layout.addWidget(self.finish_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step5_group)
        self.update_window_size()    

    def go_to_step6(self):
        """Переход к четвертому шагу"""
        
        for i, table in enumerate(self.uncertain_tables):
            if not self.validate_table_data(self.uncertain_tables[table], f"неопределенных значений '{table}'"):
                return

        # Деактивируем третий шаг
        self.deactivate_group(self.step5_group)
        self.next_btn3.setEnabled(False)

        self.init_step6()
        self.current_step = 6
        
        # Обновляем размер окна
        self.schedule_resize_update()

    def on_method_changed(self, criterion_name, situation_type, method_name):
        """Обработчик изменения метода снятия неопределенности"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']
        
        # Очищаем контейнер
        while container.layout() and container.layout().count():
            child = container.layout().takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Создаем новый layout если его нет
        #if not container.layout():
        #    container.setLayout(QVBoxLayout())
        
        # Создаем виджет с параметрами
        #params_widget = 
        self.create_method_parameters_widget(criterion_name, situation_type, method_name)
        #container.layout().addWidget(params_widget)

    def save_methods_data(self):
        """Сохраняет данные о методах снятия неопределенности"""
        self.uncertainty_methods = {}
        
        for criterion_name in self.uncertain_criteria_names:
            widgets = self.method_widgets[criterion_name]
            method_name = widgets['method_combo'].currentText()
            situation_type = self.prior_information[criterion_name]
            
            method_data = {
                'method_name': method_name,
                'situation_type': situation_type,
                'parameters': {}
            }
            
            # Собираем параметры в зависимости от метода
            container = widgets['params_container']
            if container.layout() and container.layout().count():
                #params_widget = container.layout().itemAt(0).widget()
                #print(params_widget)
                #if params_widget:
                    # Собираем все поля ввода из виджета параметров
                    for child in container.findChildren((QComboBox, QDoubleSpinBox)):
                        param_name = child.objectName().replace(f"{criterion_name}_", "")
                        if isinstance(child, QComboBox):
                            method_data['parameters'][param_name] = child.currentText()
                        elif isinstance(child, QDoubleSpinBox):
                            method_data['parameters'][param_name] = child.value()
            
            self.uncertainty_methods[criterion_name] = method_data

    def create_method_parameters_widget(self, criterion_name, situation_type, method_name):
        """Создает виджет с параметрами для выбранного метода"""
        #widget = QWidget()
        #layout = QVBoxLayout(widget)
        #layout.setContentsMargins(10, 5, 5, 5)
        #print(method_name)
        
        # В зависимости от ситуации и метода создаем соответствующие поля
        if method_name == "Критерий Байеса-Лапласа":
            #self.add_bayes_laplace_params(criterion_name)
            pass
        elif method_name == "Критерий минимальной среднеквадратичной ошибки":
            self.add_mse_params(criterion_name)
        elif method_name == "Критерий максимальной вероятности":
            self.add_max_probability_params(criterion_name)
        elif method_name == "Модальный критерий":
            #self.add_modal_params(criterion_name)
            pass
        elif method_name == "Критерий минимума энтропии":
            pass
        elif method_name == "Критерий Гермейера":
            pass
        elif method_name == "Критерий Вальда":
            #self.add_wald_params(criterion_name)
            pass
        elif method_name == "Критерий минимаксного Сэвиджа":
            #self.add_savage_params(criterion_name)
            pass
        elif method_name == "Критерий Гурвица":
            self.add_hurwitz_params(criterion_name)
        elif method_name == "Критерий Ходжеса-Лемана":
            self.add_hodges_lehman_params(criterion_name)
        elif method_name == "Универсальный критерий":
            self.add_universal_criterion_params(situation_type, criterion_name)
        
        #return widget

    def add_bayes_laplace_params(self, criterion_name):
        """Параметры для критерия Байеса-Лапласа"""
        #param_layout = QHBoxLayout()
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']

        label = QLabel("Характеристика критерия:")
        combo = QComboBox()
        combo.addItems(["profit", "loss"])
        combo.setObjectName(f"{criterion_name}_characteristic")
        #(widget, Qt.AlignTop | Qt.AlignLeft)
        container.layout().addWidget(label, 0, 0)
        container.layout().addWidget(combo, 0, 1)
        #container.layout().addStretch()
        #layout.addLayout(param_layout)

    def add_mse_params(self, criterion_name):
        """Параметры для критерия среднеквадратичной ошибки"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']

        # Характеристика критерия
        #char_layout = QHBoxLayout()
        #char_label = QLabel("Характеристика критерия:")
        #char_combo = QComboBox()
        #char_combo.addItems(["profit", "loss"])
        #char_combo.setObjectName(f"{criterion_name}_characteristic")
        #container.layout().addWidget(char_label, 0, 0)
        #container.layout().addWidget(char_combo, 0, 1)
        #container.layout().addStretch()
        #layout.addLayout(char_layout)
        
        # Тип величины
        #type_layout = QHBoxLayout()
        type_label = QLabel("Тип величины:")
        type_combo = QComboBox()
        type_combo.addItems(["непрерывная", "дискретная"])
        type_combo.setObjectName(f"{criterion_name}_value_type")
        container.layout().addWidget(type_label, 1, 0)
        container.layout().addWidget(type_combo, 1, 1)
        #container.layout().addStretch()
        #layout.addLayout(type_layout)

    def add_max_probability_params(self, criterion_name):
        """Параметры для критерия максимальной вероятности"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']

        # Характеристика критерия
        #char_layout = QHBoxLayout()
        #char_label = QLabel("Характеристика критерия:")
        #char_combo = QComboBox()
        #char_combo.addItems(["profit", "loss"])
        #char_combo.setObjectName(f"{criterion_name}_characteristic")
        #container.layout().addWidget(char_label, 0, 0)
        #container.layout().addWidget(char_combo, 0, 1)
        #container.layout().addStretch()
        #layout.addLayout(char_layout)
        
        # Порог значений
        #threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Порог значений для критерия:")
        threshold_input = QDoubleSpinBox()
        threshold_input.setRange(0.0, 1000000.0)
        threshold_input.setDecimals(3)
        threshold_input.setObjectName(f"{criterion_name}_threshold")
        container.layout().addWidget(threshold_label, 1, 0)
        container.layout().addWidget(threshold_input, 1, 1)
        #container.layout().addStretch()
        #layout.addLayout(threshold_layout)

    def add_modal_params(self, criterion_name):
        """Параметры для модального критерия"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']

        #param_layout = QHBoxLayout()
        label = QLabel("Характеристика критерия:")
        combo = QComboBox()
        combo.addItems(["profit", "loss"])
        combo.setObjectName(f"{criterion_name}_characteristic")
        container.layout().addWidget(label, 0, 0)
        container.layout().addWidget(combo, 0, 1)
        #container.layout().addStretch()
        #layout.addLayout(param_layout)

    def add_wald_params(self, criterion_name):
        """Параметры для критерия Вальда"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']

        #param_layout = QHBoxLayout()
        label = QLabel("Характеристика критерия:")
        combo = QComboBox()
        combo.addItems(["profit", "loss"])
        combo.setObjectName(f"{criterion_name}_characteristic")
        container.layout().addWidget(label, 0, 0)
        container.layout().addWidget(combo, 0, 1)
        #container.layout().addStretch()
        #layout.addLayout(param_layout)

    def add_savage_params(self, criterion_name):
        """Параметры для критерия минимаксного Сэвиджа"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']

        #param_layout = QHBoxLayout()
        label = QLabel("Характеристика критерия:")
        combo = QComboBox()
        combo.addItems(["profit", "loss"])
        combo.setObjectName(f"{criterion_name}_characteristic")
        container.layout().addWidget(label, 0, 0)
        container.layout().addWidget(combo, 0, 1)
        #container.layout().addStretch()
        #layout.addLayout(param_layout)

    def add_hurwitz_params(self, criterion_name):
        """Параметры для критерия Гурвица"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']

        # Характеристика критерия
        #char_layout = QHBoxLayout()
        #char_label = QLabel("Характеристика критерия:")
        #char_combo = QComboBox()
        #char_combo.addItems(["profit", "loss"])
        #char_combo.setObjectName(f"{criterion_name}_characteristic")
        #container.layout().addWidget(char_label, 0, 0)
        #container.layout().addWidget(char_combo, 0, 1)
        #container.layout().addStretch()
        #layout.addLayout(char_layout)
        
        # Степень склонности к риску
        #risk_layout = QHBoxLayout()
        risk_label = QLabel("Степень склонности ЛПР к риску:")
        risk_input = QDoubleSpinBox()
        risk_input.setRange(0.0, 1.0)
        risk_input.setSingleStep(0.01)
        risk_input.setDecimals(3)
        risk_input.setValue(0.5)
        risk_input.setObjectName(f"{criterion_name}_risk_attitude")
        container.layout().addWidget(risk_label, 1, 0)
        container.layout().addWidget(risk_input, 1, 1)
        #container.layout().addStretch()
        #layout.addLayout(risk_layout)

    def add_hodges_lehman_params(self, criterion_name):
        """Параметры для критерия Ходжеса-Лемана"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']

        # Характеристика критерия
        #char_layout = QHBoxLayout()
        #char_label = QLabel("Характеристика критерия:")
        #char_combo = QComboBox()
        #char_combo.addItems(["profit", "loss"])
        #char_combo.setObjectName(f"{criterion_name}_characteristic")
        #container.layout().addWidget(char_label, 0, 0)
        #container.layout().addWidget(char_combo, 0, 1)
        #container.layout().addStretch()
        #layout.addLayout(char_layout)
        
        # Параметр критерия
        #param_layout = QHBoxLayout()
        param_label = QLabel("Параметр кр. Ходжеса-Лемана:")
        param_input = QDoubleSpinBox()
        param_input.setRange(0.0, 1.0)
        param_input.setSingleStep(0.01)
        param_input.setDecimals(3)
        param_input.setValue(0.5)
        param_input.setObjectName(f"{criterion_name}_hl_parameter")
        container.layout().addWidget(param_label, 1, 0)
        container.layout().addWidget(param_input, 1, 1)
        #container.layout().addStretch()
        #layout.addLayout(param_layout)

    def add_universal_criterion_params(self, situation, criterion_name):
        """Параметры для универсального критерия"""
        widgets = self.method_widgets[criterion_name]
        container = widgets['params_container']
        i = 0
        # Параметр дополнительного критерия
        #param1_layout = QHBoxLayout()
        if situation in ["Ситуация 1: Полная определенность", "Ситуация 3: Риск"]:
            param1_label = QLabel("Параметр дополнительного критерия:")
            param1_input = QDoubleSpinBox()
            param1_input.setRange(0.0, 1.0)
            param1_input.setSingleStep(0.01)
            param1_input.setDecimals(3)
            param1_input.setValue(0.5)
            param1_input.setObjectName(f"{criterion_name}_additional_param")
            container.layout().addWidget(param1_label, i, 0)
            container.layout().addWidget(param1_input, i, 1)
            i += 1
            #container.layout().addStretch()
            #layout.addLayout(param1_layout)
        
        # Степень склонности к риску
        #param2_layout = QHBoxLayout()
        if situation in ["Ситуация 2: Неопределенность", "Ситуация 3: Риск"]:
            param2_label = QLabel("Степень склонности ЛПР к риску:")
            param2_input = QDoubleSpinBox()
            param2_input.setRange(0.0, 1.0)
            param2_input.setSingleStep(0.01)
            param2_input.setDecimals(3)
            param2_input.setValue(0.5)
            param2_input.setObjectName(f"{criterion_name}_risk_attitude")
            container.layout().addWidget(param2_label, i, 0)
            container.layout().addWidget(param2_input, i, 1)
            i += 1
            #container.layout().addStretch()
            #layout.addLayout(param2_layout)
        
        # Степень доверия
        if situation == "Ситуация 3: Риск":
            #param3_layout = QHBoxLayout()
            param3_label = QLabel("Степень доверия ЛПР к информации:")
            param3_input = QDoubleSpinBox()
            param3_input.setRange(0.0, 1.0)
            param3_input.setSingleStep(0.01)
            param3_input.setDecimals(3)
            param3_input.setValue(0.5)
            param3_input.setObjectName(f"{criterion_name}_trust_level")
            container.layout().addWidget(param3_label, i, 0)
            container.layout().addWidget(param3_input, i, 1)
            #container.layout().addStretch()
            #layout.addLayout(param3_layout)

    def load_uncertain_table_from_csv(self, criterion_name):
        """Загрузка данных в таблицу неопределенного критерия из CSV файла"""
        table = self.uncertain_tables[criterion_name]
        self.load_table_from_csv(table, 'uncertain')

    def init_step6(self):
        """Шестой шаг: настройки нормализации и смены направления для всех критериев"""
        self.step6_group = QGroupBox("Шаг 6: Настройки нормализации и смены направления")
        step6_layout = QVBoxLayout(self.step6_group)
        step6_layout.setContentsMargins(15, 15, 15, 15)
        
        info_label = QLabel("Настройте параметры нормализации и смены направления для всех критериев")
        info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        step6_layout.addWidget(info_label)
        
        # Создаем вкладки для всех критериев
        self.all_criteria_tabs = QTabWidget()
        
        # Добавляем критерии с определенностью
        for criterion_name in self.certain_criteria_names:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            
            # Настройки нормализации
            self.add_normalization_settings(criterion_name, tab_layout)
            
            # Настройки смены направления
            self.add_direction_change_settings(criterion_name, tab_layout)
            
            self.all_criteria_tabs.addTab(tab_widget, f"📊 {criterion_name}")
        
        # Добавляем критерии с неопределенностью
        for criterion_name in self.uncertain_criteria_names:
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            
            # Настройки нормализации
            self.add_normalization_settings(criterion_name, tab_layout)
            
            # Настройки смены направления
            self.add_direction_change_settings(criterion_name, tab_layout)
            
            self.all_criteria_tabs.addTab(tab_widget, f"❓ {criterion_name}")
        
        step6_layout.addWidget(self.all_criteria_tabs)
        
        # Кнопка Далее
        self.next_btn6 = QPushButton("Далее")
        self.next_btn6.clicked.connect(self.go_to_step7)
        step6_layout.addWidget(self.next_btn6, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step6_group)
        self.update_window_size()

    def add_normalization_settings(self, criterion_name, layout):
        """Добавляет настройки нормализации для критерия"""
        normalization_group = QGroupBox("Настройки нормализации")
        normalization_layout = QVBoxLayout(normalization_group)
        
        # Метод нормализации
        method_layout = QHBoxLayout()
        method_label = QLabel("Метод нормализации:")
        method_combo = QComboBox()
        method_combo.addItems([
            "Нет нормализации",
            "Сравнительная нормализация", 
            "Относительная нормализация",
            "Естественная нормализация",
            "Полная нормализация"
        ])
        method_combo.setCurrentIndex(4)  # Полная нормализация по умолчанию
        method_combo.setObjectName(f"{criterion_name}_normalization")
        
        method_layout.addWidget(method_label)
        method_layout.addWidget(method_combo)
        method_layout.addStretch()
        normalization_layout.addLayout(method_layout)
        
        layout.addWidget(normalization_group)

    def add_direction_change_settings(self, criterion_name, layout):
        """Добавляет настройки смены направления для критерия"""
        direction_group = QGroupBox("Настройки смены направления")
        direction_layout = QVBoxLayout(direction_group)
        
        # Чекбокс для включения смены направления
        change_layout = QHBoxLayout()
        change_cb = QCheckBox("Смена направления нужна")
        change_cb.toggled.connect(lambda checked, name=criterion_name: self.on_direction_change_toggled(name, checked))
        change_cb.setObjectName(f"{criterion_name}_change_cb")
        
        change_layout.addWidget(change_cb)
        change_layout.addStretch()
        direction_layout.addLayout(change_layout)
        
        # Группа методов смены направления (изначально скрыта)
        method_group = QWidget()
        method_layout = QVBoxLayout(method_group)
        method_layout.setContentsMargins(20, 5, 5, 5)
        method_group.hide()
        method_group.setObjectName(f"{criterion_name}_method_group")
        
        method_button_group = QButtonGroup(method_group)
        method_button_group.setExclusive(True)
        
        # Метод отрицания
        negation_rb = QRadioButton("Смена направления отрицанием")
        negation_rb.toggled.connect(lambda checked, name=criterion_name: self.on_direction_method_selected(name))
        negation_rb.setObjectName(f"{criterion_name}_negation_rb")
        method_button_group.addButton(negation_rb)
        method_layout.addWidget(negation_rb)
        
        # Метод Сэвиджа
        savige_rb = QRadioButton("Смена направления методом Сэвиджа")
        savige_rb.toggled.connect(lambda checked, name=criterion_name: self.on_direction_method_selected(name))
        savige_rb.setObjectName(f"{criterion_name}_savige_rb")
        method_button_group.addButton(savige_rb)
        method_layout.addWidget(savige_rb)
        
        # Поле для максимального значения (изначально скрыто)
        max_value_layout = QHBoxLayout()
        max_value_label = QLabel("Максимальное значение:")
        max_value_input = QDoubleSpinBox()
        max_value_input.setRange(0.0, 1000000.0)
        max_value_input.setDecimals(3)
        max_value_input.hide()
        max_value_input.setObjectName(f"{criterion_name}_max_value")
        
        max_value_layout.addWidget(max_value_label)
        max_value_layout.addWidget(max_value_input)
        max_value_layout.addStretch()
        method_layout.addLayout(max_value_layout)
        
        direction_layout.addWidget(method_group)
        layout.addWidget(direction_group)

    def on_direction_change_toggled(self, criterion_name, checked):
        """Обработчик переключения чекбокса смены направления"""
        method_group = self.findChild(QWidget, f"{criterion_name}_method_group")
        if method_group:
            method_group.setVisible(checked)
            
        if not checked:
            negation_rb = self.findChild(QRadioButton, f"{criterion_name}_negation_rb")
            savige_rb = self.findChild(QRadioButton, f"{criterion_name}_savige_rb")
            max_value_input = self.findChild(QDoubleSpinBox, f"{criterion_name}_max_value")
            
            if negation_rb:
                negation_rb.setChecked(False)
            if savige_rb:
                savige_rb.setChecked(False)
            if max_value_input:
                max_value_input.hide()

    def on_direction_method_selected(self, criterion_name):
        """Обработчик выбора метода смены направления"""
        savige_rb = self.findChild(QRadioButton, f"{criterion_name}_savige_rb")
        max_value_input = self.findChild(QDoubleSpinBox, f"{criterion_name}_max_value")
        
        if savige_rb and max_value_input:
            if savige_rb.isChecked():
                max_value_input.setVisible(True)
            else:
                max_value_input.setVisible(False)

    def go_to_step7(self):
        """Переход к седьмому шагу"""
        # Проверяем, что для критериев с включенной сменой направления выбран метод
        all_criteria = self.certain_criteria_names + self.uncertain_criteria_names
        
        for criterion_name in all_criteria:
            change_cb = self.findChild(QCheckBox, f"{criterion_name}_change_cb")
            negation_rb = self.findChild(QRadioButton, f"{criterion_name}_negation_rb")
            savige_rb = self.findChild(QRadioButton, f"{criterion_name}_savige_rb")
            
            if change_cb and change_cb.isChecked():
                if not (negation_rb and negation_rb.isChecked()) and not (savige_rb and savige_rb.isChecked()):
                    QMessageBox.warning(self, "Ошибка", 
                                    f"Для критерия '{criterion_name}' включена смена направления, но не выбран метод смены направления")
                    return
        
        # Сохраняем настройки нормализации и смены направления
        self.save_normalization_direction_data()
        
        # Деактивируем шестой шаг
        self.deactivate_group(self.step6_group)
        self.next_btn6.setEnabled(False)

        self.init_step7()
        self.current_step = 7
        
        # Обновляем размер окна
        self.schedule_resize_update()

    def init_step7(self):
        """Седьмой шаг: настройки оптимизации"""
        self.step7_group = QGroupBox("Шаг 7: Настройки оптимизации")
        step7_layout = QVBoxLayout(self.step7_group)
        step7_layout.setContentsMargins(15, 15, 15, 15)
        
        info_label = QLabel("Настройте параметры оптимизации")
        info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        step7_layout.addWidget(info_label)
        
        # Выбор принципа оптимальности (один для всех критериев)
        principle_group = QGroupBox("Принцип оптимальности")
        principle_layout = QVBoxLayout(principle_group)
        
        principle_combo = QComboBox()
        principle_combo.addItems([
            "Принцип идеальной точки",
            "Принцип антиидеальной точки", 
            "Принцип абсолютной уступки",
            "Принцип относительной уступки"
        ])
        principle_combo.currentTextChanged.connect(self.on_principle_changed)
        principle_combo.setObjectName("optimization_principle")
        
        principle_layout.addWidget(principle_combo)
        step7_layout.addWidget(principle_group)
        
        # Контейнер для идеальной/антиидеальной точки (показывается только для соответствующих принципов)
        self.point_container = QWidget()
        point_layout = QVBoxLayout(self.point_container)
        self.point_container.show()
        
        # Кнопка загрузки CSV для точки
        point_load_layout = QHBoxLayout()
        point_load_btn = QPushButton("Загрузить точку из CSV")
        point_load_btn.clicked.connect(self.load_principle_point_from_csv)
        point_load_layout.addWidget(point_load_btn)
        point_load_layout.addStretch()
        point_layout.addLayout(point_load_layout)
        
        # Таблица для точки (1 строка, столбцы - все критерии)
        all_criteria = self.certain_criteria_names + self.uncertain_criteria_names
        self.point_table = QTableWidget(1, len(all_criteria))
        self.point_table.setHorizontalHeaderLabels(all_criteria)
        self.point_table.setVerticalHeaderLabels(["Значение"])
        
        # Настраиваем внешний вид таблицы
        self.setup_table_appearance(self.point_table, min_column_width=100, min_row_height=30)
        
        table_height =  30 + 40  # высота_строки * количество_строк + заголовок
        self.point_table.setMinimumHeight(table_height)
        self.point_table.setMaximumHeight(table_height)

        table_width = len(all_criteria) * 100 + 40  # высота_строки * количество_строк + заголовок
        self.point_table.setMinimumWidth(table_width)
        self.point_table.setMaximumWidth(table_width)
        
        # Заполняем значениями по умолчанию для идеальной точки
        for col in range(len(all_criteria)):
            item = QTableWidgetItem("1.0")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.point_table.setItem(0, col, item)
        

        self.point_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        point_layout.addWidget(self.point_table)
        self.point_container.show()
        step7_layout.addWidget(self.point_container)
        
        # Назначение типов функций для каждого критерия
        function_group = QGroupBox("Назначение типов функций для критериев")
        function_layout = QVBoxLayout(function_group)
        
        # Создаем таблицу для назначения типов
        self.function_table = QTableWidget(len(all_criteria), 2)
        self.function_table.setHorizontalHeaderLabels(["Критерий", "Тип функции"])
        #self.function_table.setVerticalHeaderLabels(all_criteria)
        
        # Настраиваем внешний вид таблицы
        self.setup_table_appearance(self.function_table, min_column_width=150, min_row_height=30)

        # УСТАНАВЛИВАЕМ ФИКСИРОВАННУЮ ВЫСОТУ ТАБЛИЦЫ
        table_height = len(all_criteria) * 35 + 40  # высота_строки * количество_строк + заголовок
        self.function_table.setMinimumHeight(table_height)
        self.function_table.setMaximumHeight(table_height)

        table_width = 2*150 + 40  # высота_строки * количество_строк + заголовок
        self.function_table.setMinimumWidth(table_width)
        self.function_table.setMaximumWidth(table_width)
        
        # Отключаем растягивание столбцов для этой таблицы
        #header = self.function_table.horizontalHeader()
        #header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # первый столбец растягивается
        #header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # второй по содержимому
        
        # Заполняем таблицу
        for row, criterion_name in enumerate(all_criteria):
            # Критерий (только для чтения)
            criterion_item = QTableWidgetItem(criterion_name)
            criterion_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            criterion_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.function_table.setItem(row, 0, criterion_item)
            
            # Combobox для выбора типа функции
            type_combo = QComboBox()
            type_combo.addItems(["Целевая функция", "Функция ограничения"])
            self.function_table.setCellWidget(row, 1, type_combo)
        
        function_layout.addWidget(self.function_table)
        step7_layout.addWidget(function_group)
        
        # Пограничное значение для функций ограничения (одно для всех)
        constraint_group = QGroupBox("Пограничное значение для функций ограничения")
        constraint_layout = QHBoxLayout(constraint_group)
        
        constraint_label = QLabel("Пограничное значение:")
        self.constraint_input = QDoubleSpinBox()
        self.constraint_input.setRange(-1000000.0, 1000000.0)
        self.constraint_input.setDecimals(3)
        self.constraint_input.setValue(0.0)
        
        constraint_layout.addWidget(constraint_label)
        constraint_layout.addWidget(self.constraint_input)
        constraint_layout.addStretch()
        step7_layout.addWidget(constraint_group)
        
        # Кнопка завершения
        self.final_btn = QPushButton("Завершить сбор данных")
        self.final_btn.clicked.connect(self.finalize_data_input)
        step7_layout.addWidget(self.final_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step7_group)
        self.update_window_size()

    def on_principle_changed(self, principle):
        """Обработчик изменения принципа оптимальности"""
        if "точки" in principle:
            self.point_container.show()
            
            # Обновляем значения по умолчанию
            default_value = "1.0" if " идеальн" in principle else "0.0"
            for col in range(self.point_table.columnCount()):
                item = self.point_table.item(0, col)
                if item:
                    item.setText(default_value)
        else:
            self.point_container.hide()

    def load_principle_point_from_csv(self):
        """Загрузка точки принципа из CSV файла"""
        self.load_table_from_csv(self.point_table, 'point')

    def finalize_data_input(self):
        """Завершает ввод всех данных и сохраняет их"""
        if not self.validate_table_data(self.point_table, "значений точки"):
            return
        
        # Сохраняем данные о методах
        self.save_methods_data()

        # Сохраняем настройки нормализации и смены направления
        self.save_normalization_direction_data()

        # Сохраняем настройки оптимизации
        self.save_optimization_data()

        # Собираем данные из таблиц
        self.collect_table_data()
        
        # Сохраняем все данные задачи
        task_data = self.save_task_data()
        
        # Передаем данные в основное окно
        if self.parent:
            self.parent.on_second_task_completed(task_data)
        
        # Деактивируем пятый шаг
        self.deactivate_group(self.step7_group)
        self.final_btn.setEnabled(False)
        
        # Завершаем ввод
        QMessageBox.information(self, "Успех", 
                            "Все данные успешно введены и сохранены!")
        self.accept()

    def save_optimization_data(self):
        """Сохраняет данные оптимизации"""
        all_criteria = self.certain_criteria_names + self.uncertain_criteria_names
        
        # Сохраняем принцип оптимальности
        principle_combo = self.findChild(QComboBox, "optimization_principle")
        if principle_combo:
            self.optimization_principle = principle_combo.currentText()
        
        # Сохраняем типы функций для каждого критерия
        self.function_types = {}
        for row in range(self.function_table.rowCount()):
            criterion_item = self.function_table.item(row, 0)
            type_combo = self.function_table.cellWidget(row, 1)
            
            if criterion_item and type_combo:
                criterion_name = criterion_item.text()
                self.function_types[criterion_name] = type_combo.currentText()
        
        # Сохраняем пограничное значение
        self.constraint_value = self.constraint_input.value()
        
        # Сохраняем точки если принцип требует
        if "точки" in self.optimization_principle:
            point_data = {}
            for col in range(self.point_table.columnCount()):
                item = self.point_table.item(0, col)
                criterion = self.point_table.horizontalHeaderItem(col).text()
                value = float(item.text()) if item and item.text() else 0.0
                point_data[criterion] = value
            
            if " идеальн" in self.optimization_principle:
                self.ideal_point = point_data
                self.anti_ideal_point = {}
            else:
                self.anti_ideal_point = point_data
                self.ideal_point = {}
        else:
            self.ideal_point = {}
            self.anti_ideal_point = {}

    def collect_table_data(self):
        """Собирает данные из всех таблиц"""
        # Данные таблицы определенных критериев
        self.certain_table_data = {}
        if self.num_certain_criteria > 0:
            for row in range(self.certain_table.rowCount()):
                row_data = []
                for col in range(self.certain_table.columnCount()):
                    item = self.certain_table.item(row, col)
                    row_data.append(float(item.text()) if item and item.text() else 0.0)
                self.certain_table_data[self.certain_criteria_names[row]] = row_data
            self.certain_table_data['Alternatives'] = self.alternative_names
        
        # Данные таблиц неопределенных критериев
        self.uncertain_tables_data = {}
        for criterion_name, table in self.uncertain_tables.items():
            table_data = {}
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data.append(float(item.text()) if item and item.text() else 0.0)
                table_data[self.environment_states[criterion_name][row]] = row_data
            table_data["Alternatives"] = self.alternative_names
            self.uncertain_tables_data[criterion_name] = table_data

    def save_normalization_direction_data(self):
        """Сохраняет данные о нормализации и смене направления для всех критериев"""
        self.normalization_methods = {}
        self.direction_changes = {}
        self.direction_methods = {}
        self.savige_max_values = {}
        
        # Сохраняем настройки для критериев с неопределенностью
        for criterion_name in self.uncertain_criteria_names:
            self._save_criterion_settings(criterion_name)
        
        # Сохраняем настройки для критериев с определенностью
        for criterion_name in self.certain_criteria_names:
            self._save_criterion_settings(criterion_name)

    def _save_criterion_settings(self, criterion_name):
        """Сохраняет настройки для одного критерия"""
        # Сохраняем метод нормализации
        normalization_combo = self.findChild(QComboBox, f"{criterion_name}_normalization")
        if normalization_combo:
            self.normalization_methods[criterion_name] = normalization_combo.currentText()
        
        # Сохраняем настройки смены направления
        change_cb = self.findChild(QCheckBox, f"{criterion_name}_change_cb")
        if change_cb:
            self.direction_changes[criterion_name] = change_cb.isChecked()
            
            if change_cb.isChecked():
                negation_rb = self.findChild(QRadioButton, f"{criterion_name}_negation_rb")
                savige_rb = self.findChild(QRadioButton, f"{criterion_name}_savige_rb")
                max_value_input = self.findChild(QDoubleSpinBox, f"{criterion_name}_max_value")
                
                if negation_rb and negation_rb.isChecked():
                    self.direction_methods[criterion_name] = 'negation'
                elif savige_rb and savige_rb.isChecked():
                    self.direction_methods[criterion_name] = 'savige'
                    if max_value_input:
                        self.savige_max_values[criterion_name] = max_value_input.value()

    def save_task_data(self):
        """Сохраняет все данные задачи в структурированном формате"""
        task_data = {
            'basic_parameters': {
                'num_certain_criteria': self.num_certain_criteria,
                'num_uncertain_criteria': self.num_uncertain_criteria,
                'num_alternatives': self.num_alternatives
            },
            'criteria_names': {
                'certain_names': self.certain_criteria_names,
                'uncertain_names': self.uncertain_criteria_names,
                'alternative_names': self.alternative_names
            },
            'weights': {
                'certain_weights': self.certain_weights,
                'uncertain_weights': self.uncertain_weights
            },
            'uncertainty_settings': {
                'prior_information': self.prior_information,
                'probabilities': self.probabilities
            },
            'uncertainty_methods': self.uncertainty_methods,
            'normalization_settings': {
                'normalization_methods': self.normalization_methods,
                'direction_changes': self.direction_changes,
                'direction_methods': self.direction_methods,
                'savige_max_values': self.savige_max_values
            },
            'optimization_settings': {
                'optimization_principle': self.optimization_principle,
                'function_types': self.function_types,
                'ideal_point': self.ideal_point,
                'anti_ideal_point': self.anti_ideal_point,
                'constraint_value': self.constraint_value
            },
            'table_data': {
                'certain_data': pd.DataFrame(self.certain_table_data).set_index('Alternatives').T if self.certain_table_data else None,
                'uncertain_data': {criterion: pd.DataFrame(data).set_index('Alternatives').T for criterion, data in self.uncertain_tables_data.items()}
            }
        }
        return task_data

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
        
        # ОБНОВЛЯЕМ РАЗМЕРЫ ТАБЛИЦ ПОСЛЕ ИЗМЕНЕНИЯ РАЗМЕРА ОКНА
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