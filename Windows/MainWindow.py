from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QCheckBox, QPushButton, QScrollArea,
                            QLabel, QLineEdit, QGroupBox, QSizePolicy, QDialog,
                            QGridLayout, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QIcon
import sys
import json

from Windows.CertaintyDecisionMaking import CDMTaskWindow
from Windows.UncertaintyDecisionMaking import UDMTaskWindow
from Windows.FuzzyLogicDecisionMaking import FLTaskWindow
from ReportCalculation import ReportCalculation

class StyledCheckBox(QCheckBox):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QCheckBox {
                spacing: 8px;
                font-weight: 500;
                color: #2c3e50;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #3498db;
                border-radius: 4px;
                background: white;
            }
            QCheckBox::indicator:checked {
                background: #3498db;
                border: 2px solid #2980b9;
            }
            QCheckBox::indicator:checked:hover {
                border: 2px solid #2471a3;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #2980b9;
            }
        """)

class StyledButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #3498db, stop: 1 #2980b9);
                border: none;
                border-radius: 8px;
                color: white;
                padding: 12px 20px;
                font-weight: 600;
                font-size: 12px;
                min-width: 100px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2980b9, stop: 1 #2471a3);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2471a3, stop: 1 #1c5a85);
            }
            QPushButton:disabled {
                background: #bdc3c7;
            }
        """)

class MainWindow(QMainWindow):
    task_list = [
        "Принятие решений в условиях определенности", 
        "Принятие решений в условиях неопределенности",
        "Принятие решений при помощи нечетких систем"
    ]

    # Переменные для хранения данных задач
    first_task_data = None
    second_task_data = None
    third_task_data = None
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система принятия решений")
        self.setMinimumSize(500, 300)
        
        # Устанавливаем стиль для главного окна
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ecf0f1, stop: 1 #bdc3c7);
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QWidget#scrollContent {
                background: transparent;
            }                           
            QCheckBox:disabled {
                color: #6c757d;
            }
            QPushButton:disabled {
                background: #ced4da;
                color: #6c757d;
            }
        """)
        self.setWindowIcon(QIcon('icon.png'))

        # Основной виджет и layout
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet("QWidget#centralWidget { background: transparent; }")
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Создаем скроллируемую область
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Виджет для содержимого скролла
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_layout.setSpacing(25)
        self.scroll_layout.setContentsMargins(15, 15, 15, 15)
        
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # Переменные для хранения состояния
        self.task_buttons = {}
        self.task_checkboxes = {}
        
        # Таймер для отложенного обновления размеров
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_window_size)
        
        # Инициализация интерфейса
        self.init_ui()
        

    def on_first_task_completed(self, task_data):
        """Обработчик завершения первой задачи"""
        self.first_task_data = task_data
        print(task_data)
        
        # Деактивируем чекбокс и кнопку первой задачи
        self.deactivate_task('T1')
        
    def on_second_task_completed(self, task_data):
        """Обработчик завершения второй задачи"""
        self.second_task_data = task_data
        print(task_data)
        
        # Деактивируем чекбокс и кнопку первой задачи
        self.deactivate_task('T2')
        
    def on_third_task_completed(self, task_data):
        """Обработчик завершения второй задачи"""
        self.third_task_data = task_data
        print(task_data)
        
        # Деактивируем чекбокс и кнопку первой задачи
        self.deactivate_task('T3')
    
    def deactivate_task(self, task):
        """Деактивирует элементы первой задачи в основном окне"""
        # Находим чекбокс и кнопку для первой задачи
        task_checkbox = self.task_checkboxes.get(task)
        task_button = self.task_buttons.get(task)
        
        if task_checkbox:
            task_checkbox.setEnabled(False)
            task_checkbox.setStyleSheet("color: #6c757d;")
        
        if task_button:
            task_button.setEnabled(False)
            task_button.setText("Выполнено")
            
        # Проверяем нужно ли показать блок сохранения
        self.check_tasks_completion()

    def init_ui(self):
        # Заголовок
        subtitle_label = QLabel("Выберите тип решаемой задачи:")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("""
            font-size: 15pt;
            font-weight: 600;
            color: #34495e;
            padding: 10px;
        """)
        self.scroll_layout.addWidget(subtitle_label)

        # Создаем сетку для чекбоксов и кнопок
        grid_container = QWidget()
        grid_container.setStyleSheet("""
            background: white;
            border-radius: 12px;
            padding: 20px;
            border: 2px solid #bdc3c7;
        """)
        grid_layout = QGridLayout(grid_container)
        grid_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_layout.setHorizontalSpacing(30)
        grid_layout.setVerticalSpacing(15)
        grid_layout.setContentsMargins(15, 15, 15, 15)
        
        # Создаем чекбоксы и кнопки и размещаем их в сетке
        for i in range(3):
            # Чекбокс (первая строка)
            checkbox = StyledCheckBox(self.task_list[i])
            checkbox.setMinimumWidth(200)
            checkbox.stateChanged.connect(lambda state, num=i: self.on_task_selected(state, num))
            self.task_checkboxes[f'T{i+1}'] = checkbox
            grid_layout.addWidget(checkbox, 0, i)
            
            # Кнопка (вторая строка)
            button = StyledButton("Выполнить")
            button.clicked.connect(lambda checked, num=i: self.open_task_window(num))
            button.hide()
            self.task_buttons[f'T{i+1}'] = button
            grid_layout.addWidget(button, 1, i)
        
        # Устанавливаем минимальную ширину колонок
        for i in range(3):
            grid_layout.setColumnMinimumWidth(i, 220)
            grid_layout.setColumnStretch(i, 1)
        
        self.scroll_layout.addWidget(grid_container)

        # Инициализируем блок сохранения результатов
        self.save_block = self.create_save_block()
        self.save_block.hide()  
        self.scroll_layout.addWidget(self.save_block)
        
        # Устанавливаем начальный размер
        self.update_window_size()
        
    def on_task_selected(self, state, task_num):
        if state == Qt.CheckState.Checked.value:
            self.task_buttons[f'T{task_num+1}'].show()
        else:
            self.task_buttons[f'T{task_num+1}'].hide()
        
        self.schedule_resize_update()
    
    

    def create_save_block(self):
        """Создает блок для сохранения результатов"""
        save_group = QGroupBox("Сохранение результатов")
        save_group.setStyleSheet("""
            QGroupBox {
                font-size: 12pt;
                font-weight: bold;
                color: #2c3e50;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        save_layout = QVBoxLayout(save_group)
        save_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        save_layout.setSpacing(15)
        
        # Поле для ввода имени файла
        file_layout = QHBoxLayout()
        file_label = QLabel("Имя файла:")
        file_label.setStyleSheet("font-weight: 600; color: #2c3e50;")
        
        self.filename_input = QLineEdit()
        self.filename_input.setPlaceholderText("Введите имя файла (без расширения)")
        self.filename_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #bdc3c7;
                border-radius: 6px;
                font-size: 11px;
            }
            QLineEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        self.filename_input.textChanged.connect(self.on_filename_changed)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.filename_input)
        save_layout.addLayout(file_layout)
        
        # Кнопка сохранения и закрытия
        self.save_button = StyledButton("Сохранить результаты и выйти")
        self.save_button.clicked.connect(self.save_results_and_exit)
        self.save_button.setEnabled(False)  # Изначально неактивна
        save_layout.addWidget(self.save_button)
        
        return save_group
    
    
    def on_filename_changed(self, text):
        """Активирует кнопку сохранения если введено имя файла"""
        self.save_button.setEnabled(bool(text.strip()))

    def save_results_and_exit(self):
        """Сохраняет результаты в файл и закрывает программу"""
        filename = self.filename_input.text().strip()
        if not filename:
            return
                        
        #try:
        report = ReportCalculation(first_task_data=self.first_task_data, second_task_data=self.second_task_data, third_task_data=self.third_task_data)
        report.create(filename)
            
        # Закрываем программу
        QApplication.quit()
            
        #except Exception as e:
        #    print(f"Ошибка при сохранении: {e}")

    
    def check_tasks_completion(self):
        """Проверяет выполнены ли задачи и показывает блок сохранения"""
        any_completed = any(not checkbox.isEnabled() 
                          for checkbox in self.task_checkboxes.values())
        
        if any_completed:
            self.save_block.show()
        else:
            self.save_block.hide()
            
        self.schedule_resize_update()
        self.update_window_size()

    def open_task_window(self, task_num):
        if task_num == 0:  # Первая задача
            task_window = CDMTaskWindow(self)
            task_window.exec()
        elif task_num == 1:  # Вторая задача
            task_window = UDMTaskWindow(self)
            task_window.exec()
        elif task_num == 2:  # Третья задача
            task_window = FLTaskWindow(self)
            task_window.exec()
    
    def schedule_resize_update(self):
        self.resize_timer.start(50)
    
    def update_window_size(self):
        self.scroll_content.layout().activate()
        self.scroll_content.updateGeometry()
        
        content_size = self.scroll_content.sizeHint()
        
        min_width = 500
        min_height = 350
        max_height = 700
        
        new_width = max(min_width, content_size.width() + 60)
        new_height = min(max_height, max(min_height, content_size.height() + 80))
        
        self.setFixedSize(new_width, new_height)
        
        if content_size.height() + 80 > max_height:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        else:
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    
    def resizeEvent(self, event):
        if event.size() != self.size():
            self.setFixedSize(self.size())
        super().resizeEvent(event)
    
    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(100, self.update_window_size)
