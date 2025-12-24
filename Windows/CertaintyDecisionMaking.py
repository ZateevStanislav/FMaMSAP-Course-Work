from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QCheckBox, QPushButton, QScrollArea,
                            QLabel, QLineEdit, QGroupBox, QSizePolicy, QDialog,
                            QGridLayout, QFrame, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QSpinBox, QDoubleSpinBox, QMessageBox,
                            QFileDialog, QButtonGroup, QRadioButton, QComboBox, QAbstractItemView)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QIcon
import pandas as pd
import numpy as np
import csv



class CDMTaskWindow(QDialog):
    COLUMN_WIDTH = 120
    ROW_HEIGHT = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Принятие решений в условиях определенности")
        self.setModal(True)
        
        # Переменные для хранения данных
        self.num_expert_ratings = 0
        self.num_numeric_ratings = 0
        self.num_alternatives = 0
        self.num_experts = 0
        
        self.expert_names = []
        self.numeric_names = []
        self.alternative_names = []
        self.numeric_weights = []
        self.expert_weights = []
        
        self.selected_method = None
        self.normalization_method = None
        self.direction_changes = {}
        self.savige_max_values = {}
        
        # Данные таблиц
        self.numeric_table_data = None
        self.expert_tables_data = []
        

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
                font-size: 12px;  /* Увеличили с 10px */
            }
            QTableWidget::item {
                padding: 6px;  /* Увеличили padding */
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                padding: 8px;  /* Увеличили padding */
                border: none;
                font-weight: bold;
                font-size: 12px;  /* Увеличили с 10px */
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
        title_label = QLabel("Принятие решений в условиях определенности")
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
        step1_layout.setSpacing(10)
        step1_layout.setContentsMargins(10, 10, 10, 10)
        
        # Создаем элементы ввода
        labels = [
            "Количество экспертных оценок:",
            "Количество численных оценок:",
            "Количество альтернатив:",
            "Количество экспертов:"
        ]
        
        default_values = [3, 4, 7, 3]
        self.inputs = []
        
        for i, (label_text, default_val) in enumerate(zip(labels, default_values)):
            label = QLabel(label_text)
            label.setMinimumWidth(150)
            spinbox = QSpinBox()
            spinbox.setMinimum(1)
            spinbox.setMaximum(20)
            spinbox.setValue(default_val)
            spinbox.setMinimumWidth(60)
            
            row = i // 2
            col = (i % 2) * 2
            step1_layout.addWidget(label, row, col)
            step1_layout.addWidget(spinbox, row, col + 1)
            self.inputs.append(spinbox)
        
        # Кнопка Далее
        self.next_btn1 = QPushButton("Далее")
        self.next_btn1.clicked.connect(self.go_to_step2)
        step1_layout.addWidget(self.next_btn1, 2, 0, 1, 4, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step1_group)
        self.update_window_size()
    
    def go_to_step2(self):
        """Переход ко второму шагу"""
        # Сохраняем значения
        self.num_expert_ratings = self.inputs[0].value()
        self.num_numeric_ratings = self.inputs[1].value()
        self.num_alternatives = self.inputs[2].value()
        self.num_experts = self.inputs[3].value()
        
        # Деактивируем первый шаг
        self.deactivate_group(self.step1_group)
        self.next_btn1.setEnabled(False)
        
        # Инициализируем второй шаг
        self.init_step2()
        self.current_step = 2
        
        # ОБНОВЛЯЕМ РАЗМЕР ОКНА СРАЗУ
        self.schedule_resize_update()
    
    def init_step2(self):
        """Второй шаг: ввод имен и весов"""
        self.step2_group = QGroupBox("Шаг 2: Имена и веса критериев")
        step2_layout = QVBoxLayout(self.step2_group)
        step2_layout.setContentsMargins(10, 10, 10, 10)
        
        # Сетка для ввода данных
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(8)
        grid_layout.setHorizontalSpacing(15)
        
        # Заголовки столбцов
        headers = ["Экспертные оценки", "Численные оценки", "Альтернативы"]
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
            grid_layout.addWidget(label, 0, col * 3, 1, 3, Qt.AlignmentFlag.AlignCenter)
        
        default_weight_value = 1 / (self.num_expert_ratings + self.num_numeric_ratings)
        # Ввод экспертных оценок
        self.expert_inputs = []
        for i in range(self.num_expert_ratings):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Экспертная {i+1}")
            name_input.setMinimumWidth(100)
            
            weight_input = QDoubleSpinBox()
            weight_input.setRange(0.0, 1.0)
            weight_input.setSingleStep(0.01)
            weight_input.setDecimals(3)
            weight_input.setValue(default_weight_value)
            weight_input.setPrefix("Вес: ")
            weight_input.setMinimumWidth(70)
            
            grid_layout.addWidget(QLabel(f"Эксп.{i+1}:"), i+1, 0)
            grid_layout.addWidget(name_input, i+1, 1)
            grid_layout.addWidget(weight_input, i+1, 2)
            self.expert_inputs.append((name_input, weight_input))
        
        # Ввод численных оценок
        self.numeric_inputs = []
        for i in range(self.num_numeric_ratings):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Численная {i+1}")
            name_input.setMinimumWidth(100)
            
            weight_input = QDoubleSpinBox()
            weight_input.setRange(0.0, 1.0)
            weight_input.setSingleStep(0.01)
            weight_input.setDecimals(3)
            weight_input.setValue(default_weight_value)
            weight_input.setPrefix("Вес: ")
            weight_input.setMinimumWidth(70)
            
            grid_layout.addWidget(QLabel(f"Числ.{i+1}:"), i+1, 3)
            grid_layout.addWidget(name_input, i+1, 4)
            grid_layout.addWidget(weight_input, i+1, 5)
            self.numeric_inputs.append((name_input, weight_input))
        
        # Ввод альтернатив
        self.alternative_inputs = []
        for i in range(self.num_alternatives):
            name_input = QLineEdit()
            name_input.setPlaceholderText(f"Альтернатива {i+1}")
            name_input.setMinimumWidth(100)
            
            grid_layout.addWidget(QLabel(f"Альт.{i+1}:"), i+1, 6)
            grid_layout.addWidget(name_input, i+1, 7)
            self.alternative_inputs.append(name_input)
        
        # Информация о весах
        weight_info = QLabel("Сумма всех весов (экспертных + численных) должна быть равна 1.0")
        weight_info.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
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
        total_sum = (sum(inp[1].value() for inp in self.expert_inputs) + 
                    sum(inp[1].value() for inp in self.numeric_inputs))
        
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
        expert_names = [inp[0].text() or f"Экспертная {i+1}" for i, inp in enumerate(self.expert_inputs)]
        numeric_names = [inp[0].text() or f"Численная {i+1}" for i, inp in enumerate(self.numeric_inputs)]
        
        all_criteria_names = expert_names + numeric_names
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
        self.expert_names = [inp[0].text() or f"Экспертная {i+1}" for i, inp in enumerate(self.expert_inputs)]
        self.expert_weights = {inp[0].text() or f"Экспертная {i+1}": inp[1].value() for i, inp in enumerate(self.expert_inputs)}
        self.numeric_names = [inp[0].text() or f"Численная {i+1}" for i, inp in enumerate(self.numeric_inputs)]
        self.numeric_weights = {inp[0].text() or f"Численная {i+1}": inp[1].value() for i, inp in enumerate(self.numeric_inputs)}
        self.alternative_names = [inp.text() or f"Альтернатива {i+1}" for i, inp in enumerate(self.alternative_inputs)]
    
        self.init_step3()
        self.current_step = 3
        
        # ОБНОВЛЯЕМ РАЗМЕР ОКНА СРАЗУ
        self.schedule_resize_update()
    
    def on_expert_table_changed(self, expert_idx):
        #"""Обработчик изменения данных в таблице экспертных оценок"""
        #try:
            settings = self.expert_criteria_settings[f"expert_{expert_idx}"]
            table = settings['table']
            method_combo = settings['method_combo']
            concordance_label = settings['concordance_label']
            expert_name = self.expert_names[expert_idx]
            
            # Обновляем доступные методы
            concordance = self.update_expert_methods_combobox(table, method_combo, expert_name)
            
            # Обновляем индикатор согласованности
            color = "green" if concordance > 0.5 else "red"
            concordance_label.setText(f"Коэффициент согласованности: <span style='color: {color}; font-weight: bold;'>{concordance:.3f}</span>")
            
        #except Exception as e:
        #    print(f"Ошибка обработки изменения таблицы: {e}")

    def load_table_from_csv(self, table, mode):
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

                if mode == 'expert':
                    # Обновляем проверку согласованности после загрузки данных
                    self.update_concordance_for_table(table)
                
            #except Exception as e:
            #    QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")
    
    def update_concordance_for_table(self, table):
        """Обновляет проверку согласованности для конкретной таблицы"""
        # Находим, к какому эксперту принадлежит таблица
        for expert_idx, settings in self.expert_criteria_settings.items():
            if settings['table'] == table:
                self.on_expert_table_changed(int(expert_idx.split('_')[1]))
                break

    def on_direction_change_toggled(self, checked, criterion_id):
        """Обработчик переключения чекбокса смены направления"""
        # Определяем, к какой группе принадлежит критерий
        if criterion_id.startswith('numeric_'):
            widgets = self.numeric_criteria_settings[criterion_id]
        elif criterion_id.startswith('expert_'):
            widgets = self.expert_criteria_settings[criterion_id]
        else:
            return
        
        widgets['method_group'].setVisible(checked)
        
        if not checked:
            widgets['negation_rb'].setChecked(False)
            widgets['savige_rb'].setChecked(False)
            widgets['max_value_input'].hide()
        
        # Автоматически выбираем первый метод, если ни один не выбран
        if checked and not widgets['negation_rb'].isChecked() and not widgets['savige_rb'].isChecked():
            widgets['negation_rb'].setChecked(True)

    def on_method_selected(self, criterion_id):
        """Обработчик выбора метода смены направления"""
        # Определяем, к какой группе принадлежит критерий
        if criterion_id.startswith('numeric_'):
            widgets = self.numeric_criteria_settings[criterion_id]
        elif criterion_id.startswith('expert_'):
            widgets = self.expert_criteria_settings[criterion_id]
        else:
            return
        
        # Если выбран метод Сэвиджа, показываем поле для максимального значения
        if widgets['savige_rb'].isChecked():
            widgets['max_value_input'].setVisible(True)
        else:
            widgets['max_value_input'].setVisible(False)

    def add_numeric_criterion_settings(self, layout, criterion_name, criterion_id):
        """Добавляет настройки для одного численного критерия"""
        criterion_group = QGroupBox(f"Критерий: {criterion_name}")
        criterion_layout = QVBoxLayout(criterion_group)
        
        # Метод нормализации
        normalization_layout = QHBoxLayout()
        normalization_label = QLabel("Метод нормализации:")
        normalization_combo = QComboBox()
        normalization_combo.addItems([
            "Нет нормализации",
            "Сравнительная нормализация", 
            "Относительная нормализация",
            "Естественная нормализация",
            "Полная нормализация"
        ])
        normalization_combo.setCurrentIndex(4)
        normalization_layout.addWidget(normalization_label)
        normalization_layout.addWidget(normalization_combo)
        normalization_layout.addStretch()
        criterion_layout.addLayout(normalization_layout)
        
        # Смена направления
        direction_layout = QHBoxLayout()
        change_direction_cb = QCheckBox("Смена направления нужна")
        change_direction_cb.toggled.connect(lambda checked, id=criterion_id: self.on_direction_change_toggled(checked, id))
        direction_layout.addWidget(change_direction_cb)
        direction_layout.addStretch()
        criterion_layout.addLayout(direction_layout)
        
        # Группа для методов смены направления (изначально скрыта)
        method_group = QWidget()
        method_layout = QVBoxLayout(method_group)
        method_layout.setContentsMargins(20, 5, 5, 5)
        method_group.hide()
        
        method_button_group = QButtonGroup(method_group)
        method_button_group.setExclusive(True)
        
        # Метод отрицания
        negation_rb = QRadioButton("Смена направления отрицанием")
        method_button_group.addButton(negation_rb, 0)
        negation_rb.toggled.connect(lambda checked, id=criterion_id: self.on_method_selected(id))
        method_layout.addWidget(negation_rb)
        
        # Метод Сэвиджа
        savige_rb = QRadioButton("Смена направления методом Сэвиджа")
        savige_rb.toggled.connect(lambda checked, id=criterion_id: self.on_method_selected(id))
        method_button_group.addButton(savige_rb, 1)
        method_layout.addWidget(savige_rb)
        
        # Поле для максимального значения (изначально скрыто)
        max_value_layout = QHBoxLayout()
        max_value_label = QLabel("Максимальное значение:")
        max_value_input = QDoubleSpinBox()
        max_value_input.setRange(0.0, 1000000.0)
        max_value_input.setDecimals(3)
        max_value_input.hide()
        
        max_value_layout.addWidget(max_value_label)
        max_value_layout.addWidget(max_value_input)
        max_value_layout.addStretch()
        method_layout.addLayout(max_value_layout)
        
        criterion_layout.addWidget(method_group)
        
        # Сохраняем виджеты для этого критерия
        self.numeric_criteria_settings[criterion_id] = {
            'normalization_combo': normalization_combo,
            'change_cb': change_direction_cb,
            'method_group': method_group,
            'negation_rb': negation_rb,
            'savige_rb': savige_rb,
            'max_value_input': max_value_input
        }
        
        layout.addWidget(criterion_group)

    def save_numeric_criteria_settings(self):
        """Сохраняет настройки для численных критериев"""
        self.numeric_methods = {}
        self.numeric_normalization = {}
        self.numeric_direction_changes = {}
        self.numeric_savige_max_values = {}
        
        for i, name in enumerate(self.numeric_names):
            criterion_id = f"numeric_{i}"
            settings = self.numeric_criteria_settings[criterion_id]
            
            # Сохраняем метод нормализации
            self.numeric_normalization[name] = settings['normalization_combo'].currentText()
            
            # Сохраняем настройки смены направления
            if settings['change_cb'].isChecked():
                if settings['negation_rb'].isChecked():
                    self.numeric_direction_changes[name] = 'negation'
                elif settings['savige_rb'].isChecked():
                    self.numeric_direction_changes[name] = 'savige'
                    self.numeric_savige_max_values[name] = settings['max_value_input'].value()

    def save_expert_criteria_settings(self):
        """Сохраняет настройки для экспертных критериев"""
        self.expert_methods = {}
        self.expert_normalization = {}
        self.expert_direction_changes = {}
        self.expert_savige_max_values = {}
        
        for i, name in enumerate(self.expert_names):
            criterion_id = f"expert_{i}"
            settings = self.expert_criteria_settings[criterion_id]
            
            # Сохраняем метод сведения
            self.expert_methods[name] = settings['method_combo'].currentText()
            
            # Сохраняем метод нормализации
            self.expert_normalization[name] = settings['normalization_combo'].currentText()
            
            # Сохраняем настройки смены направления
            if settings['change_cb'].isChecked():
                if settings['negation_rb'].isChecked():
                    self.expert_direction_changes[name] = 'negation'
                elif settings['savige_rb'].isChecked():
                    self.expert_direction_changes[name] = 'savige'
                    self.expert_savige_max_values[name] = settings['max_value_input'].value()

    def init_step3(self):
        """Третий шаг: таблица численных оценок и настройки критериев"""
        self.step3_group = QGroupBox("Шаг 3: Численные оценки альтернатив и настройки критериев")
        step3_layout = QVBoxLayout(self.step3_group)
        step3_layout.setContentsMargins(10, 10, 10, 10)
        
        info_label = QLabel("Заполните таблицу численных оценок. Используйте кнопку для загрузки данных из CSV файла.")
        info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        step3_layout.addWidget(info_label)
        
        # Кнопка загрузки из CSV
        load_btn_layout = QHBoxLayout()
        load_csv_btn = QPushButton("Загрузить из CSV")
        load_csv_btn.clicked.connect(lambda: self.load_table_from_csv(self.numeric_table, 'numeric'))
        load_btn_layout.addWidget(load_csv_btn)
        load_btn_layout.addStretch()
        step3_layout.addLayout(load_btn_layout)
        
        # Создаем таблицу
        self.numeric_table = QTableWidget(self.num_numeric_ratings, self.num_alternatives)
        self.numeric_table.setMinimumHeight(200)
        
        # Устанавливаем заголовки
        horizontal_headers = self.alternative_names
        vertical_headers = self.numeric_names
        self.numeric_table.setHorizontalHeaderLabels(horizontal_headers)
        self.numeric_table.setVerticalHeaderLabels(vertical_headers)
        
        # НАСТРАИВАЕМ ВНЕШНИЙ ВИД
        self.setup_table_appearance(self.numeric_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
        # Устанавливаем фиксированную высоту для таблицы
        table_height = self.num_numeric_ratings * self.ROW_HEIGHT + 40
        self.numeric_table.setMinimumHeight(table_height)
        self.numeric_table.setMaximumHeight(max(table_height, 500))

        table_width = self.num_alternatives * self.COLUMN_WIDTH + 40
        self.numeric_table.setMinimumWidth(table_width)
        self.numeric_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем таблицу пустыми значениями
        for row in range(self.num_numeric_ratings):
            for col in range(self.num_alternatives):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.numeric_table.setItem(row, col, item)
        
        self.numeric_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        step3_layout.addWidget(self.numeric_table)
        
        # НАСТРОЙКИ ДЛЯ ЧИСЛЕННЫХ КРИТЕРИЕВ
        criteria_settings_label = QLabel("Настройки для численных критериев:")
        criteria_settings_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 11px; margin-top: 15px;")
        step3_layout.addWidget(criteria_settings_label)
        
        # Создаем виджет для настроек критериев (без прокрутки)
        criteria_widget = QWidget()
        criteria_layout = QVBoxLayout(criteria_widget)
        
        self.numeric_criteria_settings = {}
        
        # Добавляем настройки для каждого численного критерия
        for i, name in enumerate(self.numeric_names):
            self.add_numeric_criterion_settings(criteria_layout, name, f"numeric_{i}")
        
        step3_layout.addWidget(criteria_widget)
        
        # Кнопка Далее
        self.next_btn3 = QPushButton("Далее")
        self.next_btn3.clicked.connect(self.go_to_step4)
        step3_layout.addWidget(self.next_btn3, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step3_group)
        self.update_window_size()

    def update_expert_methods_combobox(self, table, method_combo, expert_name):
        """
        Обновляет доступные методы в combobox на основе согласованности экспертов
        """
        try:
            # Получаем данные из таблицы
            table_data = self.get_table_data(table)
            
            # Рассчитываем коэффициент конкордации
            concordance = self.calculate_kendall_concordance(table_data)
            
            # Сохраняем текущий выбранный метод
            current_method = method_combo.currentText()
            
            # Обновляем combobox
            method_combo.clear()
            
            # Всегда доступные методы
            available_methods = [
                "Усреднение экспертных оценок",
                "Усреднение с оценкой компетентности экспертов по алгоритму Евланова-Кутузова",
                "Усреднение с оценкой компетентности экспертов по алгоритму Рыкова"
            ]
            
            # Добавляем обобщенную ранжировку только если согласованность > 0.5
            if concordance > 0.5:
                available_methods.append("Обобщенная ранжировка")
            
            method_combo.addItems(available_methods)
            
            # Восстанавливаем предыдущий выбор, если он все еще доступен
            if current_method in available_methods:
                method_combo.setCurrentText(current_method)
            else:
                # Если предыдущий метод недоступен, выбираем первый
                method_combo.setCurrentIndex(0)
            
            # Обновляем подсказку с информацией о согласованности
            method_combo.setToolTip(f"Коэффициент согласованности Кэндалла: {concordance:.3f}. " 
                                f"Обобщенная ранжировка {'доступна' if concordance > 0.5 else 'недоступна'}")
            
            return concordance
            
        except Exception as e:
            print(f"Ошибка обновления методов: {e}")
            return 0.0

    def get_table_data(self, table):
        """Получает данные из таблицы в структурированном виде"""
        table_data = {}
        
        for row in range(table.rowCount()):
            expert_name = f"Expert{row}"
            ratings = []
            
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and item.text().strip():
                    try:
                        ratings.append(float(item.text()))
                    except ValueError:
                        ratings.append(0.0)
                else:
                    ratings.append(0.0)
            
            table_data[expert_name] = ratings
        
        table_data["Alternatives"] = self.alternative_names
        return table_data

    def calculate_kendall_concordance(self, table_data):
        """
        Расчет коэффициента конкордации Кэндалла (коэффициента согласованности экспертов)
        table_data - данные таблицы: словарь {эксперт: [оценки]}
        """
        try:
            # Преобразуем данные в матрицу оценок
            experts_data = [ratings for expert, ratings in table_data.items() if expert != "Alternatives"]
            
            if len(experts_data) < 2:
                return 1.0  # Если один эксперт - полная согласованность
            
            # Преобразуем в numpy array
            ratings_matrix = np.array(experts_data)
            n, m = ratings_matrix.shape  # n экспертов, m альтернатив
            
            if n < 2 or m < 2:
                return 1.0
            
            # Расчет коэффициента конкордации Кэндалла
            # 1. Преобразуем оценки в ранги для каждого эксперта
            ranked_matrix = np.zeros_like(ratings_matrix)
            for i in range(n):
                ranked_matrix[i] = self._convert_to_ranks(ratings_matrix[i])
            
            # 2. Сумма рангов для каждой альтернативы
            sum_ranks = np.sum(ranked_matrix, axis=0)
            
            # 3. Средняя сумма рангов
            mean_sum_ranks = np.mean(np.sum(ranked_matrix, axis=0))
            
            # 4. Сумма квадратов отклонений
            sum_sq_deviations = np.sum((sum_ranks - mean_sum_ranks) ** 2)
            
            # 5. Коэффициент конкордации Кэндалла
            concordance = (12 * sum_sq_deviations) / (n ** 2 * (m ** 3 - m))
            
            return min(max(concordance, 0.0), 1.0)  # Ограничиваем от 0 до 1
            
        except Exception as e:
            print(f"Ошибка расчета коэффициента Кэндалла: {e}")
            return 0.0

    def _convert_to_ranks(self, values):
        """Преобразует значения в ранги"""
        rel_values = [i for i in values]
        ranks = np.zeros_like(values)
        ranks = ranks.astype(float)
        current_rank = 0
        while len(rel_values) > 0:
            max_value = max(rel_values)
            maxes = [i for i, est in enumerate(values) if est == max_value]
            rank = sum(range(current_rank+1, current_rank+1+len(maxes))) / len(maxes)
            for i in maxes:
                ranks[i] = rank
            current_rank += len(maxes)
            rel_values = [j for j in rel_values if j < max_value]

        return ranks
    
    def go_to_step4(self):
        """Переход к четвертому шагу"""
        # Проверяем, что для критериев с включенной сменой направления выбран метод
        for criterion_id, settings in self.numeric_criteria_settings.items():
            if settings['change_cb'].isChecked():
                if not settings['negation_rb'].isChecked() and not settings['savige_rb'].isChecked():
                    criterion_name = self.numeric_names[int(criterion_id.split('_')[1])]
                    QMessageBox.warning(self, "Ошибка", 
                                    f"Для критерия '{criterion_name}' включена смена направления, но не выбран метод смены направления")
                    return
                
        
        if not self.validate_table_data(self.numeric_table, "численных оценок"):
            return
            
        # Сохраняем настройки численных критериев
        self.save_numeric_criteria_settings()

        # Деактивируем третий шаг
        self.deactivate_group(self.step3_group)
        self.next_btn3.setEnabled(False)

        self.init_step4()
        self.current_step = 4
        
        # ОБНОВЛЯЕМ РАЗМЕР ОКНА СРАЗУ
        self.schedule_resize_update()
    
    def init_step4(self):
        """Четвертый шаг: экспертные оценки и настройки критериев"""
        self.step4_group = QGroupBox("Шаг 4: Экспертные оценки и настройки критериев")
        step4_layout = QVBoxLayout(self.step4_group)
        step4_layout.setContentsMargins(10, 10, 10, 10)
        
        info_label = QLabel("Заполните таблицы экспертных оценок. Используйте кнопки для загрузки данных из CSV файлов.")
        info_label.setStyleSheet("font-style: italic; color: #666; font-size: 9px; margin: 5px;")
        step4_layout.addWidget(info_label)
        
        self.expert_tables = []
        self.expert_criteria_settings = {}
        
        for expert_idx in range(self.num_expert_ratings):
            expert_name = self.expert_names[expert_idx]
            expert_group = QGroupBox(f"{expert_name}")
            expert_layout = QVBoxLayout(expert_group)
            
            # Кнопка загрузки из CSV для этой таблицы
            load_btn_layout = QHBoxLayout()
            load_csv_btn = QPushButton("Загрузить из CSV")
            load_csv_btn.clicked.connect(lambda checked, idx=expert_idx: self.load_table_from_csv(self.expert_tables[idx], 'expert'))
            load_btn_layout.addWidget(load_csv_btn)
            load_btn_layout.addStretch()
            expert_layout.addLayout(load_btn_layout)
            
            # Создаем таблицу для этого эксперта
            table = QTableWidget(self.num_experts, self.num_alternatives)
            table.setMinimumHeight(200)
            
            # Заголовки
            horizontal_headers = self.alternative_names
            vertical_headers = [f"Эксперт {i+1}" for i in range(self.num_experts)]
            table.setHorizontalHeaderLabels(horizontal_headers)
            table.setVerticalHeaderLabels(vertical_headers)
            
            # НАСТРАИВАЕМ ВНЕШНИЙ ВИД
            self.setup_table_appearance(table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
        
            # Устанавливаем фиксированную высоту для таблицы
            table_height = self.num_experts * self.ROW_HEIGHT + 40
            table.setMinimumHeight(table_height)
            table.setMaximumHeight(max(table_height, 500))

            table_width = self.num_alternatives * self.COLUMN_WIDTH + 40
            table.setMinimumWidth(table_width)
            table.setMaximumWidth(max(table_width, 500))
            
            # Заполняем пустыми значениями
            for row in range(self.num_experts):
                for col in range(self.num_alternatives):
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(row, col, item)
            
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            expert_layout.addWidget(table)
            self.expert_tables.append(table)
            
            # НАСТРОЙКИ ДЛЯ ЭКСПЕРТНОГО КРИТЕРИЯ
            settings_group = QGroupBox(f"Настройки для критерия: {expert_name}")
            settings_layout = QVBoxLayout(settings_group)
            
            # Метод сведения экспертных оценок
            method_layout = QHBoxLayout()
            method_label = QLabel("Метод сведения:")
            method_combo = QComboBox()
            
            # Подключаем сигнал изменения данных в таблице
            #table.itemChanged.connect(lambda x=expert_idx: self.on_expert_table_changed(x))
            #table.itemChanged.connect(lambda: self.update_concordance_for_table(table))
            #table.itemChanged.connect(lambda: print(expert_idx))


            # Инициализируем combobox с проверкой согласованности
            self.update_expert_methods_combobox(table, method_combo, expert_name)

            #method_combo.addItems([
            #    "Усреднение экспертных оценок",
            #    "Усреднение с оценкой компетентности экспертов по алгоритму Евланова-Кутузова",
            #    "Усреднение с оценкой компетентности экспертов по алгоритму Рыкова", 
            #    "Обобщенная ранжировка"
            #])
            #method_combo.setCurrentIndex(0)
            method_layout.addWidget(method_label)
            method_layout.addWidget(method_combo)
            method_layout.addStretch()
            settings_layout.addLayout(method_layout)

            
        
            # Индикатор согласованности с кнопкой перерасчета
            concordance_layout = QHBoxLayout()
            concordance_label = QLabel("Коэффициент согласованности: рассчитывается...")
            concordance_label.setStyleSheet("font-size: 9px; color: #666;")
            
            # Кнопка перерасчета
            recalc_btn = QPushButton("↻")
            recalc_btn.setToolTip("Пересчитать коэффициент согласованности")
            recalc_btn.setFixedSize(20, 20)
            recalc_btn.setStyleSheet("""
                QPushButton {
                    background: #3498db;
                    border: none;
                    border-radius: 3px;
                    color: white;
                    font-weight: bold;
                    font-size: 8px;
                }
                QPushButton:hover {
                    background: #2980b9;
                }
            """)
            recalc_btn.clicked.connect(lambda checked, idx=expert_idx: self.manual_recalculate_concordance(idx))
            
            concordance_layout.addWidget(concordance_label)
            concordance_layout.addWidget(recalc_btn)
            concordance_layout.addStretch()
            settings_layout.addLayout(concordance_layout)
            
            # Метод нормализации
            normalization_layout = QHBoxLayout()
            normalization_label = QLabel("Метод нормализации:")
            normalization_combo = QComboBox()
            normalization_combo.addItems([
                "Нет нормализации",
                "Сравнительная нормализация",
                "Относительная нормализация",
                "Естественная нормализация", 
                "Полная нормализация"
            ])
            normalization_combo.setCurrentIndex(4)
            normalization_layout.addWidget(normalization_label)
            normalization_layout.addWidget(normalization_combo)
            normalization_layout.addStretch()
            settings_layout.addLayout(normalization_layout)
            
            # Смена направления
            direction_layout = QHBoxLayout()
            change_direction_cb = QCheckBox("Смена направления нужна")
            change_direction_cb.toggled.connect(lambda checked, id=f"expert_{expert_idx}": self.on_direction_change_toggled(checked, id))
            direction_layout.addWidget(change_direction_cb)
            direction_layout.addStretch()
            settings_layout.addLayout(direction_layout)
            
            # Группа для методов смены направления (изначально скрыта)
            method_group = QWidget()
            method_direction_layout = QVBoxLayout(method_group)
            method_direction_layout.setContentsMargins(20, 5, 5, 5)
            method_group.hide()
            
            method_button_group = QButtonGroup(method_group)
            method_button_group.setExclusive(True)
            
            # Метод отрицания
            negation_rb = QRadioButton("Смена направления отрицанием")
            negation_rb.toggled.connect(lambda checked, id=f"expert_{expert_idx}": self.on_method_selected(id))
            method_button_group.addButton(negation_rb, 0)
            method_direction_layout.addWidget(negation_rb)
            
            # Метод Сэвиджа
            savige_rb = QRadioButton("Смена направления методом Сэвиджа")
            savige_rb.toggled.connect(lambda checked, id=f"expert_{expert_idx}": self.on_method_selected(id))
            method_button_group.addButton(savige_rb, 1)
            method_direction_layout.addWidget(savige_rb)
            
            # Поле для максимального значения (изначально скрыто)
            max_value_layout = QHBoxLayout()
            max_value_label = QLabel("Максимальное значение:")
            max_value_input = QDoubleSpinBox()
            max_value_input.setRange(0.0, 1000000.0)
            max_value_input.setDecimals(3)
            max_value_input.hide()
            
            max_value_layout.addWidget(max_value_label)
            max_value_layout.addWidget(max_value_input)
            max_value_layout.addStretch()
            method_direction_layout.addLayout(max_value_layout)
            
            settings_layout.addWidget(method_group)
            expert_layout.addWidget(settings_group)
            
            # Сохраняем настройки для этого экспертного критерия
            self.expert_criteria_settings[f"expert_{expert_idx}"] = {
                'method_combo': method_combo,
                'normalization_combo': normalization_combo,
                'change_cb': change_direction_cb,
                'method_group': method_group,
                'negation_rb': negation_rb,
                'savige_rb': savige_rb,
                'max_value_input': max_value_input,
                'concordance_label': concordance_label,
                'table': table
            }
            
            step4_layout.addWidget(expert_group)
        
        # Кнопка завершения
        self.finish_btn = QPushButton("Далее")
        self.finish_btn.clicked.connect(self.go_to_step5)
        step4_layout.addWidget(self.finish_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step4_group)
        self.update_window_size()
    
    def manual_recalculate_concordance(self, expert_idx):
        """Ручной перерасчет коэффициента согласованности"""
        try:
            settings = self.expert_criteria_settings.get(f"expert_{expert_idx}")
            if not settings:
                return
                
            table = settings['table']
            method_combo = settings['method_combo']
            concordance_label = settings['concordance_label']
            expert_name = self.expert_names[expert_idx]
            
            # Временно меняем текст на "расчет..."
            concordance_label.setText("Коэффициент согласованности: расчет...")
            concordance_label.setStyleSheet("font-size: 9px; color: #666;")
            
            # Принудительно обновляем интерфейс
            QApplication.processEvents()
            
            # Обновляем доступные методы
            concordance = self.update_expert_methods_combobox(table, method_combo, expert_name)
            
            # Обновляем индикатор согласованности
            color = "green" if concordance > 0.5 else "red"
            status = "✓ достаточно" if concordance > 0.5 else "✗ недостаточно"
            concordance_label.setText(
                f"Коэффициент согласованности Кэндалла: "
                f"<span style='color: {color}; font-weight: bold;'>{concordance:.3f}</span> "
                f"({status})"
            )
            
            # Показываем сообщение об успехе
            QMessageBox.information(self, "Перерасчет завершен", 
                                f"Коэффициент согласованности для '{expert_name}': {concordance:.3f}\n"
                                f"Обобщенная ранжировка {'доступна' if concordance > 0.5 else 'недоступна'}")
            
        except Exception as e:
            print(f"Ошибка ручного перерасчета для эксперта {expert_idx}: {e}")
            concordance_label.setText("Коэффициент согласованности: ошибка расчета")
            concordance_label.setStyleSheet("font-size: 9px; color: red;")
            QMessageBox.warning(self, "Ошибка", f"Не удалось рассчитать коэффициент согласованности: {str(e)}")

    def go_to_step5(self):
        """Переход к пятому шагу"""
        # Проверяем, что для критериев с включенной сменой направления выбран метод
        for criterion_id, settings in self.expert_criteria_settings.items():
            if settings['change_cb'].isChecked():
                if not settings['negation_rb'].isChecked() and not settings['savige_rb'].isChecked():
                    expert_idx = int(criterion_id.split('_')[1])
                    criterion_name = self.expert_names[expert_idx]
                    QMessageBox.warning(self, "Ошибка", 
                                    f"Для критерия '{criterion_name}' включена смена направления, но не выбран метод смены направления")
                    return
        
        
        for i, table in enumerate(self.expert_tables):
            if not self.validate_table_data(table, f"экспертных оценок '{self.expert_names[i]}'"):
                return
            
        # Сохраняем настройки экспертных критериев
        self.save_expert_criteria_settings()

         # Собираем данные из таблиц
        self.collect_table_data()

        # Деактивируем четвертый шаг
        self.deactivate_group(self.step4_group)
        self.finish_btn.setEnabled(False)
        
        #self.init_step5()
        #self.current_step = 5

        self.init_step7()
        self.current_step = 7
        
        # ОБНОВЛЯЕМ РАЗМЕР ОКНА СРАЗУ
        self.schedule_resize_update()
    
    def init_step7(self):
        """Седьмой шаг: параметры для метода квазиравенства"""
        self.step7_group = QGroupBox("Шаг 5: Параметры методов оптимальности")
        step7_layout = QVBoxLayout(self.step7_group)
        step7_layout.setContentsMargins(15, 15, 15, 15)
        
        # Общее количество критериев
        total_criteria = self.num_expert_ratings + self.num_numeric_ratings
        all_criteria_names = self.numeric_names + self.expert_names
        
        # 1. Координаты идеальной точки (таблица)
        ideal_group = QGroupBox("Координаты идеальной точки")
        ideal_layout = QVBoxLayout(ideal_group)
        
        # Кнопка загрузки CSV
        ideal_load_layout = QHBoxLayout()
        ideal_load_btn = QPushButton("Загрузить из CSV")
        ideal_load_btn.clicked.connect(lambda: self.load_vector_from_csv(self.ideal_table, total_criteria))
        ideal_load_layout.addWidget(ideal_load_btn)
        ideal_load_layout.addStretch()
        ideal_layout.addLayout(ideal_load_layout)
        
        # Таблица для идеальной точки
        self.ideal_table = QTableWidget(1, total_criteria)
        self.ideal_table.setHorizontalHeaderLabels(all_criteria_names)
        self.ideal_table.setVerticalHeaderLabels(["Значения"])
        
        # НАСТРАИВАЕМ ВНЕШНИЙ ВИД
        self.setup_table_appearance(self.ideal_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
         
        # Устанавливаем фиксированную высоту для таблицы (показывает все строки)
        table_height = self.ROW_HEIGHT + 40  # высота_строки * количество + заголовок
        self.ideal_table.setMinimumHeight(table_height)  # ограничиваем максимум 500px
        self.ideal_table.setMaximumHeight(max(table_height, 500))

        table_width = (self.num_expert_ratings + self.num_numeric_ratings) * self.COLUMN_WIDTH + 40  # высота_строки * количество + заголовок
        self.ideal_table.setMinimumWidth(table_width)  # ограничиваем максимум 500px
        self.ideal_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем значениями по умолчанию
        for col in range(total_criteria):
            item = QTableWidgetItem("1.0")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ideal_table.setItem(0, col, item)
        
        self.ideal_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ideal_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ideal_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        ideal_layout.addWidget(self.ideal_table)
        
        step7_layout.addWidget(ideal_group)
        
        # 2. Координаты антиидеальной точки (таблица)
        anti_ideal_group = QGroupBox("Координаты антиидеальной точки")
        anti_ideal_layout = QVBoxLayout(anti_ideal_group)
        
        # Кнопка загрузки CSV
        anti_ideal_load_layout = QHBoxLayout()
        anti_ideal_load_btn = QPushButton("Загрузить из CSV")
        anti_ideal_load_btn.clicked.connect(lambda: self.load_vector_from_csv(self.anti_ideal_table, total_criteria))
        anti_ideal_load_layout.addWidget(anti_ideal_load_btn)
        anti_ideal_load_layout.addStretch()
        anti_ideal_layout.addLayout(anti_ideal_load_layout)
        
        # Таблица для антиидеальной точки
        self.anti_ideal_table = QTableWidget(1, total_criteria)
        self.anti_ideal_table.setHorizontalHeaderLabels(all_criteria_names)
        self.anti_ideal_table.setVerticalHeaderLabels(["Значения"])
        
        # НАСТРАИВАЕМ ВНЕШНИЙ ВИД
        self.setup_table_appearance(self.anti_ideal_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
         
        # Устанавливаем фиксированную высоту для таблицы (показывает все строки)
        table_height = self.ROW_HEIGHT + 40  # высота_строки * количество + заголовок
        self.anti_ideal_table.setMinimumHeight(table_height)  # ограничиваем максимум 500px
        self.anti_ideal_table.setMaximumHeight(max(table_height, 500))

        table_width = (self.num_expert_ratings + self.num_numeric_ratings) * self.COLUMN_WIDTH + 40  # высота_строки * количество + заголовок
        self.anti_ideal_table.setMinimumWidth(table_width)  # ограничиваем максимум 500px
        self.anti_ideal_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем значениями по умолчанию
        for col in range(total_criteria):
            item = QTableWidgetItem("0.0")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.anti_ideal_table.setItem(0, col, item)
        
        self.anti_ideal_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.anti_ideal_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.anti_ideal_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        anti_ideal_layout.addWidget(self.anti_ideal_table)
        
        step7_layout.addWidget(anti_ideal_group)
        
        # 3. Матрица допустимых отклонений (треугольная)
        deviations_group = QGroupBox("Матрица допустимых отклонений")
        deviations_layout = QVBoxLayout(deviations_group)
        
        # Кнопка загрузки CSV
        deviations_load_layout = QHBoxLayout()
        deviations_load_btn = QPushButton("Загрузить из CSV")
        deviations_load_btn.clicked.connect(lambda: self.load_triangular_matrix_from_csv(self.deviations_table, total_criteria))
        deviations_load_layout.addWidget(deviations_load_btn)
        deviations_load_layout.addStretch()
        deviations_layout.addLayout(deviations_load_layout)
        
         # Создаем таблицу для треугольной матрицы
        self.deviations_table = QTableWidget(total_criteria, total_criteria)
        self.deviations_table.setHorizontalHeaderLabels(all_criteria_names)
        self.deviations_table.setVerticalHeaderLabels(all_criteria_names)
        
        # НАСТРАИВАЕМ ВНЕШНИЙ ВИД С БОЛЬШЕЙ ВЫСОТОЙ
        self.setup_table_appearance(self.deviations_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
         
        # Устанавливаем фиксированную высоту для таблицы (показывает все строки)
        table_height = (self.num_expert_ratings + self.num_numeric_ratings) * self.ROW_HEIGHT + 40  # высота_строки * количество + заголовок
        self.deviations_table.setMinimumHeight(table_height)  # ограничиваем максимум 500px
        self.deviations_table.setMaximumHeight(max(table_height, 500))

        table_width = (self.num_expert_ratings + self.num_numeric_ratings) * self.COLUMN_WIDTH + 40  # высота_строки * количество + заголовок
        self.deviations_table.setMinimumWidth(table_width)  # ограничиваем максимум 500px
        self.deviations_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем таблицу и блокируем нижнюю треугольную часть
        for row in range(total_criteria):
            for col in range(total_criteria):
                item = QTableWidgetItem("")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Блокируем диагональ и нижнюю треугольную часть
                if row >= col:
                    item.setFlags(Qt.ItemFlag.NoItemFlags)  # Полностью нередактируемый
                    item.setBackground(QColor(240, 240, 240))  # Серый фон
                else:
                    # Верхняя треугольная часть - редактируемая
                    item.setText("0.1")  # значение по умолчанию
                
                self.deviations_table.setItem(row, col, item)
        
        self.deviations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.deviations_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.deviations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        deviations_layout.addWidget(self.deviations_table)
        
        step7_layout.addWidget(deviations_group)
        
        # 4. Пороги допустимости (только если один критерий с максимальным весом)
        self.threshold_table = None
        max_weight_criterion = self.find_max_weight_criterion()
        
        if max_weight_criterion and self.is_single_max_weight():
            thresholds_group = QGroupBox(f"Пороги допустимости (относительно главного критерия {max_weight_criterion} с максимальным весом)")
            thresholds_layout = QVBoxLayout(thresholds_group)
            
            # Кнопка загрузки CSV
            thresholds_load_layout = QHBoxLayout()
            thresholds_load_btn = QPushButton("Загрузить из CSV")
            thresholds_load_btn.clicked.connect(lambda: self.load_vector_from_csv(self.threshold_table, total_criteria - 1))
            thresholds_load_layout.addWidget(thresholds_load_btn)
            thresholds_load_layout.addStretch()
            thresholds_layout.addLayout(thresholds_load_layout)
            
            # Таблица для порогов допустимости
            other_criteria = [name for name in all_criteria_names if name != max_weight_criterion]
            self.threshold_table = QTableWidget(1, len(other_criteria))
            self.threshold_table.setHorizontalHeaderLabels(other_criteria)
            self.threshold_table.setVerticalHeaderLabels(["Пороги"])
            
            # НАСТРАИВАЕМ ВНЕШНИЙ ВИД
            self.setup_table_appearance(self.threshold_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
         
            # Устанавливаем фиксированную высоту для таблицы (показывает все строки)
            table_height = self.ROW_HEIGHT + 40  # высота_строки * количество + заголовок
            self.threshold_table.setMinimumHeight(table_height)  # ограничиваем максимум 500px
            self.threshold_table.setMaximumHeight(max(table_height, 500))

            table_width = (self.num_expert_ratings + self.num_numeric_ratings - 1) * self.COLUMN_WIDTH + 40  # высота_строки * количество + заголовок
            self.threshold_table.setMinimumWidth(table_width)  # ограничиваем максимум 500px
            self.threshold_table.setMaximumWidth(max(table_width, 500))
            
            # Заполняем значениями по умолчанию
            for col in range(len(other_criteria)):
                item = QTableWidgetItem("0.5")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.threshold_table.setItem(0, col, item)
            
            self.threshold_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.threshold_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.threshold_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            thresholds_layout.addWidget(self.threshold_table)
            
            step7_layout.addWidget(thresholds_group)
        
        # 5. Вектор дополнительных параметров (таблица)
        vector_group = QGroupBox("Вектор допустимых отклонений от максимального значения для лексикографического принципа квазиоптимальности")
        vector_layout = QVBoxLayout(vector_group)
        
        # Кнопка загрузки CSV
        vector_load_layout = QHBoxLayout()
        vector_load_btn = QPushButton("Загрузить из CSV")
        vector_load_btn.clicked.connect(lambda: self.load_vector_from_csv(self.vector_table, total_criteria))
        vector_load_layout.addWidget(vector_load_btn)
        vector_load_layout.addStretch()
        vector_layout.addLayout(vector_load_layout)
        
        # Таблица для вектора параметров
        self.vector_table = QTableWidget(1, total_criteria)
        self.vector_table.setHorizontalHeaderLabels(all_criteria_names)
        self.vector_table.setVerticalHeaderLabels(["Значения"])
        
        # НАСТРАИВАЕМ ВНЕШНИЙ ВИД
        self.setup_table_appearance(self.vector_table, min_column_width=self.COLUMN_WIDTH, min_row_height=self.ROW_HEIGHT)
         
        # Устанавливаем фиксированную высоту для таблицы (показывает все строки)
        table_height = self.ROW_HEIGHT + 40  # высота_строки * количество + заголовок
        self.vector_table.setMinimumHeight(table_height)  # ограничиваем максимум 500px
        self.vector_table.setMaximumHeight(max(table_height, 500))

        table_width = (self.num_expert_ratings + self.num_numeric_ratings - 1) * self.COLUMN_WIDTH + 40  # высота_строки * количество + заголовок
        self.vector_table.setMinimumWidth(table_width)  # ограничиваем максимум 500px
        self.vector_table.setMaximumWidth(max(table_width, 500))
        
        # Заполняем значениями по умолчанию
        for col in range(total_criteria):
            item = QTableWidgetItem("0.1")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.vector_table.setItem(0, col, item)
        
        self.vector_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vector_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.vector_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        vector_layout.addWidget(self.vector_table)
        
        step7_layout.addWidget(vector_group)
        
        # Кнопка завершения
        self.final_btn = QPushButton("Завершить ввод данных")
        self.final_btn.clicked.connect(self.finalize_data_input)
        step7_layout.addWidget(self.final_btn, 0, Qt.AlignmentFlag.AlignCenter)
        
        self.scroll_layout.addWidget(self.step7_group)
        self.update_window_size()
        self.schedule_resize_update()

    def load_vector_from_csv(self, table, expected_columns):
        """Загружает вектор из CSV файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    data = [list(reader)[1][1:]]
                    
                    # Проверяем размерность
                    if len(data) != 1 or len(data[0]) != expected_columns:
                        QMessageBox.warning(self, "Ошибка", 
                                        f"Ожидается 1 строка и {expected_columns} столбцов")
                        return
                    
                    # Заполняем таблицу
                    for col, value in enumerate(data[0]):
                        item = QTableWidgetItem(value.strip())
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        table.setItem(0, col, item)
                        
                QMessageBox.information(self, "Успех", "Данные успешно загружены!")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")

    def load_triangular_matrix_from_csv(self, table, expected_size):
        """Загружает треугольную матрицу из CSV файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите CSV файл", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    data = [string[1:] for string in list(reader)[1:]]
                    
                    # Проверяем размерность
                    if len(data) != expected_size or any(len(row) != expected_size for row in data):
                        QMessageBox.warning(self, "Ошибка", 
                                        f"Ожидается матрица {expected_size}x{expected_size}")
                        return
                    
                    # Заполняем таблицу (только верхнюю треугольную часть)
                    for row in range(expected_size):
                        for col in range(expected_size):
                            if row < col:  # Только верхняя треугольная часть
                                value = data[row][col].strip()
                                item = table.item(row, col)
                                if item:
                                    item.setText(value)
                    
                QMessageBox.information(self, "Успех", "Данные успешно загружены!")
                
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить файл: {str(e)}")

    def find_max_weight_criterion(self):
        """Находит критерий с максимальным весом"""
        all_weights = {**self.numeric_weights, **self.expert_weights}
        if not all_weights:
            return None
        
        max_weight = max(all_weights.values())
        max_criteria = [k for k, v in all_weights.items() if v == max_weight]
        
        # Если есть несколько критериев с одинаковым максимальным весом, берем первый
        return max_criteria[0] if max_criteria else None
    
    def is_single_max_weight(self):
        """Проверяет, есть ли только один критерий с максимальным весом"""
        all_weights = {**self.numeric_weights, **self.expert_weights}
        if not all_weights:
            return False
        
        max_weight = max(all_weights.values())
        max_criteria = [k for k, v in all_weights.items() if v == max_weight]
        
        return len(max_criteria) == 1

    def finalize_data_input(self):
        """Завершает ввод всех данных"""
        # ПРОВЕРКА ВСЕХ ТАБЛИЦ В ШАГЕ 7
        tables_to_check = [
            (self.ideal_table, "идеальной точки"),
            (self.anti_ideal_table, "антиидеальной точки"),
            (self.deviations_table, "матрицы отклонений"),
            (self.vector_table, "вектора параметров")
        ]
        
        if self.threshold_table:
            tables_to_check.append((self.threshold_table, "порогов допустимости"))
        
        for table, table_name in tables_to_check:
            if not self.validate_table_data(table, table_name):
                return
            
        # Собираем данные из седьмого шага
        total_criteria = self.num_expert_ratings + self.num_numeric_ratings
        all_criteria_names = self.numeric_names + self.expert_names
        
        # 1. Координаты идеальной точки
        ideal_point = {}
        for col in range(total_criteria):
            item = self.ideal_table.item(0, col)
            value = float(item.text()) if item and item.text() else 1.0
            ideal_point[all_criteria_names[col]] = value
        
        # 2. Координаты антиидеальной точки
        anti_ideal_point = {}
        for col in range(total_criteria):
            item = self.anti_ideal_table.item(0, col)
            value = float(item.text()) if item and item.text() else 0.0
            anti_ideal_point[all_criteria_names[col]] = value
        
        # 3. Матрица допустимых отклонений (преобразуем в полную матрицу)
        deviations_matrix = np.zeros((total_criteria, total_criteria))
        for row in range(total_criteria):
            for col in range(total_criteria):
                if row < col:  # Верхняя треугольная часть
                    item = self.deviations_table.item(row, col)
                    value = float(item.text()) if item and item.text() else 0.0
                    deviations_matrix[row, col] = value
                    deviations_matrix[col, row] = value  # Зеркалируем
        
        # 4. Пороги допустимости (только если есть таблица)
        thresholds = {}
        if self.threshold_table:
            max_weight_criterion = self.find_max_weight_criterion()
            other_criteria = [name for name in all_criteria_names if name != max_weight_criterion]
            
            for col, criterion in enumerate(other_criteria):
                item = self.threshold_table.item(0, col)
                value = float(item.text()) if item and item.text() else 0.1
                thresholds[criterion] = value
        
        # 5. Вектор параметров
        vector = {}
        for col in range(total_criteria):
            item = self.vector_table.item(0, col)
            value = float(item.text()) if item and item.text() else 0.5
            vector[all_criteria_names[col]] = value
        
        # Сохраняем все данные
        self.optimization_params = {
            'ideal_point': ideal_point,
            'anti_ideal_point': anti_ideal_point,
            'deviations_matrix': deviations_matrix,
            'thresholds': thresholds,
            'vector': vector
        }
        
        # Сохраняем все данные задачи
        task_data = self.save_task_data()
        
        # Передаем данные в основное окно
        if self.parent:
            self.parent.on_first_task_completed(task_data)
        
        # Деактивируем седьмой шаг
        self.deactivate_group(self.step7_group)
        self.final_btn.setEnabled(False)
        
        # Завершаем ввод
        QMessageBox.information(self, "Успех", 
                            "Все данные успешно введены и сохранены!")
        self.accept()

    def collect_table_data(self):
        """Собирает данные из всех таблиц"""
        # Данные численной таблицы
        self.numeric_table_data = {}
        for row in range(self.numeric_table.rowCount()):
            row_data = []
            for col in range(self.numeric_table.columnCount()):
                item = self.numeric_table.item(row, col)
                row_data.append(float(item.text()) if item else 0.0)#item.text() if item else "")
            self.numeric_table_data[self.numeric_names[row]] = row_data
            self.numeric_table_data['Alternatives'] = self.alternative_names
        
        # Данные экспертных таблиц
        self.expert_tables_data = {}
        for i, table in enumerate(self.expert_tables):
            table_data = {}
            for row in range(table.rowCount()):
                row_data = []
                for col in range(table.columnCount()):
                    item = table.item(row, col)
                    row_data.append(float(item.text()) if item else 0.0)#item.text() if item else "")
                table_data[f"Expert{row}"] = row_data
            table_data["Alternatives"] = self.alternative_names
            self.expert_tables_data[self.expert_names[i]] = table_data
    
    def save_task_data(self):
        """Сохраняет все данные задачи в структурированном формате"""
        task_data = {
            'basic_parameters': {
                'num_expert_ratings': self.num_expert_ratings,
                'num_numeric_ratings': self.num_numeric_ratings,
                'num_alternatives': self.num_alternatives,
                'num_experts': self.num_experts
            },
            'criteria_names': {
                'expert_names': self.expert_names,
                'numeric_names': self.numeric_names,
                'alternative_names': self.alternative_names
            },
            'weights': {
                'expert_weights': self.expert_weights,
                'numeric_weights': self.numeric_weights
            },
            'criteria_settings': {
                'numeric': {
                    'normalization_methods': self.numeric_normalization,
                    'direction_changes': self.numeric_direction_changes,
                    'savige_max_values': self.numeric_savige_max_values
                },
                'expert': {
                    'reduction_methods': self.expert_methods,
                    'normalization_methods': self.expert_normalization,
                    'direction_changes': self.expert_direction_changes,
                    'savige_max_values': self.expert_savige_max_values
                }
            },
            'table_data': {
                'numeric_data': pd.DataFrame(self.numeric_table_data).set_index('Alternatives').T,
                'expert_data': {exp_rate: pd.DataFrame(self.expert_tables_data[exp_rate]).set_index('Alternatives').T for exp_rate in self.expert_tables_data}
            },
            'optimization_params': self.optimization_params
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
        max_width = 1800  # Увеличили максимальную ширину
        
        # РАССЧИТЫВАЕМ ТРЕБУЕМУЮ ШИРИНУ НА ОСНОВЕ СОДЕРЖИМОГО
        required_width = content_size.width() + 100  # Добавляем больше отступов
        
        # УЧИТЫВАЕМ ШИРИНУ САМОЙ ШИРОКОЙ ТАБЛИЦЫ
        tables = self.scroll_content.findChildren(QTableWidget)
        if tables:
            for table in tables:
                # Рассчитываем минимальную ширину таблицы на основе содержимого
                table_width = self.calculate_table_width(table)
                required_width = max(required_width, table_width + 100)
        
        new_width = min(max_width, max(min_width, required_width))
        new_height = min(max_height, max(min_height, content_size.height() + 100))
        
        self.setFixedSize(new_width, new_height)
        
        # ОБНОВЛЯЕМ РАЗМЕРЫ ТАБЛИЦ ПОСЛЕ ИЗМЕНЕНИЯ РАЗМЕРА ОКНА
        #QTimer.singleShot(50, )
        self.adjust_all_tables()
        
        # Обновляем политику прокрутки
        if content_size.height() + 40 > max_height:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    def schedule_resize_update(self):
        """Запланировать обновление размеров с небольшой задержкой"""
        self.resize_timer.start(50)  # Увеличили задержку для полного обновления layout

    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        # Обновляем размеры таблиц при изменении размера окна
        #QTimer.singleShot(50, self.update_table_sizes)
        self.update_table_sizes()
        
        if event.size() != self.size():
            self.setFixedSize(self.size())
        super().resizeEvent(event)

    def update_table_sizes(self):
        """Обновляет размеры таблиц после изменения размера окна"""
        # Принудительно обновляем layout
        self.scroll_content.updateGeometry()
        self.update_window_size()
