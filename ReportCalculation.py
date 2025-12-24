import pandas as pd
import numpy as np
import os
from tabulate import tabulate
from itertools import combinations

from MethodsRealization.CriteriaProcessing import CriteriaProcessing
from MethodsRealization.UncertaintyRemoving import UncertaintyRemoving
from MethodsRealization.DecisionMaking import DecisionMaking
from MethodsRealization.FuzzyLogic import FuzzyLogic

#from SingleCriteriaDecisionMaking import SCDM

class ReportCalculation:
    direction_vocabilary = {
        'negation': "Метод смены знака",
        'savige': "Метод Сэвиджа"
    }

    def __init__(self, first_task_data = None, second_task_data = None, third_task_data = None):
        self.first_task_data = first_task_data
        self.second_task_data = second_task_data
        self.third_task_data = third_task_data

    """Обработка выполнения первого задания"""
    def __write_input_data_for_first_task__(self, file):
        """Вывод информации о входных данных"""
        file.write("═" * 80 + "\n")
        file.write("РЕШЕНИЕ ЗАДАЧИ ПРИНЯТИЯ РЕШЕНИЙ В УСЛОВИЯХ ОПРЕДЕЛЕННОСТИ".center(80) + "\n")
        file.write("═" * 80 + "\n\n\n\n")

        file.write("-" * 80 + "\n")
        file.write("ИСХОДНЫЕ ДАННЫЕ".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")

        
        """Основные параметры"""
        file.write(f"Количество альтернатив: {self.first_task_data['basic_parameters']['num_alternatives']}\n")
        file.write(f"Количество экспертов: {self.first_task_data['basic_parameters']['num_experts']}\n")
        file.write(f"Количество численных критериев: {self.first_task_data['basic_parameters']['num_numeric_ratings']}\n")
        file.write(f"Количество экспертных критериев: {self.first_task_data['basic_parameters']['num_expert_ratings']}\n\n\n")


        """Веса критериев"""
        file.write("Веса критериев:\n")
        exp_weights = self.first_task_data["weights"]["expert_weights"]
        for weight in exp_weights:
            file.write(f"\t{weight}: {exp_weights[weight]:.3f}; \n")
        num_weights = self.first_task_data["weights"]["numeric_weights"]
        for weight in num_weights:
            file.write(f"\t{weight}: {num_weights[weight]:.3f}; \n")
        file.write("\n\n")

            
        """Методы сведения экспертных оценок"""
        file.write(f"Методы агрегации экспертных оценок:\n")
        criteria_settings = self.first_task_data['criteria_settings']['expert']['reduction_methods']
        for criterion in criteria_settings:
            file.write(f"\t{criterion}: {criteria_settings[criterion]}\n")
        file.write("\n\n")
        

        """Методы нормализации"""
        file.write(f"Методы нормализации критериев:\n")
        criteria_settings = {
            **self.first_task_data['criteria_settings']['numeric']['normalization_methods'],
            **self.first_task_data['criteria_settings']['expert']['normalization_methods']
        }
        for criterion in criteria_settings:
            file.write(f"\t{criterion}: {criteria_settings[criterion]}\n")
        file.write("\n\n")


        """Методы смены направлений"""
        file.write("Смена направлений: ")
        criteria_settings = {
            **self.first_task_data['criteria_settings']['numeric']['direction_changes'],
            **self.first_task_data['criteria_settings']['expert']['direction_changes']
        }
        values_sev = {
            **self.first_task_data['criteria_settings']['numeric']['savige_max_values'],
            **self.first_task_data['criteria_settings']['expert']['savige_max_values']
        }
        if len(criteria_settings) == 0:
                file.write("Направления критериев не меняются\n\n")
        else:
            file.write("\n")
            for criterion in criteria_settings:
                sample = "" if criteria_settings[criterion] != "savige" else f"Максимальное значение:{values_sev[criterion]}"
                file.write(f"\t{criterion}: {self.direction_vocabilary[criteria_settings[criterion]]}. {sample}\n")
            file.write("\n\n")


        """Значения критериев"""
        file.write("Значения численных критериев:\n")
        file.write(tabulate(self.first_task_data["table_data"]["numeric_data"], headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n")

        file.write("Значения экспертных критериев:\n\n")
        exp_cr = self.first_task_data["table_data"]["expert_data"]
        for criterion in exp_cr:
            file.write(criterion)
            file.write(tabulate(exp_cr[criterion], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")
        file.write("\n\n")

    def __calculate_result_data_for_first_task__(self):
        """Предобработка"""
        direcion_settings = {
            'direction_changes': {
                **self.first_task_data['criteria_settings']['numeric']['direction_changes'],
                **self.first_task_data['criteria_settings']['expert']['direction_changes']
            },
            'savige_max_values': {
                **self.first_task_data['criteria_settings']['numeric']['savige_max_values'],
                **self.first_task_data['criteria_settings']['expert']['savige_max_values']
            }            
        }
        normalization_methods = {
            **self.first_task_data['criteria_settings']['numeric']['normalization_methods'],
            **self.first_task_data['criteria_settings']['expert']['normalization_methods']
        }
        preprocessing = CriteriaProcessing(
            numeric_data=self.first_task_data['table_data']['numeric_data'],
            expert_data=self.first_task_data['table_data']['expert_data'],
            expert_methods=self.first_task_data['criteria_settings']['expert']['reduction_methods'],
            normalization_methods=normalization_methods,
            direcion_settings=direcion_settings
        )
        evaluating_alternatives, related_information_preprocessing = preprocessing.get_processed_data()
        self.related_information_preprocessing_task1 = related_information_preprocessing


        """Принятие решений"""
        criterion_names = self.first_task_data['criteria_names']['numeric_names'] + self.first_task_data['criteria_names']['expert_names']
        deviation_matrix = pd.DataFrame({
            **{'': criterion_names},
            **{criterion: self.first_task_data['optimization_params']['deviations_matrix'][i] for i, criterion in enumerate(criterion_names)}
        }).set_index('')

        optimizing = DecisionMaking(
            data=evaluating_alternatives, 
            weights={
                **self.first_task_data['weights']['expert_weights'],
                **self.first_task_data['weights']['numeric_weights']
            }
        )
        optimal_alternatives, related_information_optimizing = optimizing.calculate({
            'idp': self.first_task_data['optimization_params']['ideal_point'],
            'aidp': self.first_task_data['optimization_params']['anti_ideal_point'],
            'metric': None,
            'sigma': deviation_matrix,
            'main_thresholds': self.first_task_data['optimization_params']['thresholds'],
            'quasi_equal_thresholds': self.first_task_data['optimization_params']['vector']
        })
        self.related_information_optimizing_task1 = related_information_optimizing

    def __write_results_for_first_task__(self, file):
        """Вывод информации о процессе предобработки данных"""
        file.write("-" * 80 + "\n")
        file.write("РЕЗУЛЬТАТЫ ПРЕДОБРАБОТКИ".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")


        """Сведение экспертных оценок"""
        file.write("\n\n" + "-" * 80 + "\n")
        file.write("Сведение экспертных оценок".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")

        reduction_methods = self.related_information_preprocessing_task1["expert_assessments_generalization"]["methods"]
        related_reduction_info = self.related_information_preprocessing_task1["expert_assessments_generalization"]["data"]
        
        for criterion in reduction_methods:
            file.write(f"КРИТЕРИЙ. {criterion}\n\n")
            if reduction_methods[criterion] == "Усреднение с оценкой компетентности экспертов по алгоритму Евланова-Кутузова":
                file.write("История оценки компетентности экспертов\n")
                for i, comp in enumerate(related_reduction_info[criterion]):
                    file.write(f"\tШаг {i}. {''.join([f'{expert}: {comp[expert]}   'for expert in comp])}\n")
                file.write("\n")
            elif reduction_methods[criterion] == "Усреднение с оценкой компетентности экспертов по алгоритму Рыкова":
                file.write("История оценки компетентности экспертов\n")
                for i, comp in enumerate(related_reduction_info[criterion]):
                    file.write(f"\tШаг {i}. {''.join([f'{expert}: {comp[expert]}   'for expert in comp])}\n")
                file.write("\n")
            elif reduction_methods[criterion] == "Обобщенная ранжировка":
                file.write(f"Рассчитывается {'медианная' if related_reduction_info[criterion]['mode'] == 'median' else 'усредненная'} метрика\n")
                file.write("Попарные сравнения по экспертам: \n")
                for expert in related_reduction_info[criterion]['pairs_rankings']:
                    file.write(f"Эксперт {expert}\n")
                    file.write(tabulate(related_reduction_info[criterion]['pairs_rankings'][expert], headers='keys', tablefmt='simple', showindex=True))
                    file.write("\n\n")
                file.write("Расстояния между ранжировками экспертов: \n")
                for distance in related_reduction_info[criterion]['distances']:
                    file.write(f"\tРасстояния между оценками {distance[0]} и {distance[1]} составляет {distance[2]:.3f}\n")
                file.write(f"\nОптимальной является оценка эксперта {related_reduction_info[criterion]['expert']}\n\n")
            elif reduction_methods[criterion] == "Усреднение экспертных оценок":
                file.write("Значения критерия по экспертам усреднены\n\n")

        file.write("Результат сведения экспертных оценок:\n")        
        file.write(tabulate(self.related_information_preprocessing_task1["result_criterions_values"], headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n")

        
        """Смена направлений"""
        file.write("-" * 80 + "\n")
        file.write("Результат смены направлений".center(80) + "\n")
        file.write("-" * 80 + "\n")
        file.write(tabulate(self.related_information_preprocessing_task1["direction_changing_result"], headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n\n")
        

        """Нормализация"""
        file.write("-" * 80 + "\n")
        file.write("Результат нормализации".center(80) + "\n")
        file.write("-" * 80 + "\n")
        file.write(tabulate(self.related_information_preprocessing_task1["normalization_result"], headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n\n")


        """Вывод информации о применении принципов оптимизации"""
        file.write("\n\n" + "-" * 80 + "\n")
        file.write("РЕЗУЛЬТАТЫ ПРИНЯТИЯ РЕШЕНИЯ".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")


        """Принципы идеальной и антиидеальной точек"""
        file.write("-" * 80 + "\n")
        file.write("Принципы идеальной и антиидеальной точек".center(80) + "\n")
        file.write("-" * 80 + "\n\n")

        ideal_point_info = self.related_information_optimizing_task1['idp']
        antiideal_point_info = self.related_information_optimizing_task1['aidp']

        iterable_points = ' '.join([f"{alter}: {ideal_point_info['ideal_point'].loc[alter]}," for alter in ideal_point_info['ideal_point'].index])
        file.write(f"Идеальная точка. {iterable_points}\n")
        iterable_points = ' '.join([f"{alter}: {antiideal_point_info['anti_ideal_point'].loc[alter]}," for alter in antiideal_point_info['anti_ideal_point'].index])
        file.write(f"Антиидеальная точка. {iterable_points}\n\n")

        file.write("Расстояния до точек\n")
        distances_table = ideal_point_info['data_with_distances_to_ideal_point']
        distances_table.loc[antiideal_point_info['data_with_distances_to_anti_ideal_point'].index[-1]] = antiideal_point_info['data_with_distances_to_anti_ideal_point'].loc[antiideal_point_info['data_with_distances_to_anti_ideal_point'].index[-1]]
        file.write(tabulate(distances_table, headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n")

        optimal_alternatives = "нет оптимальных альтернатив" if len(ideal_point_info['optimal_alternatives']) == 0 else ', '.join(ideal_point_info['optimal_alternatives'])
        file.write(f"Оптимальные альтернативы по принципу идеальной точки: {optimal_alternatives}\n")
        optimal_alternatives = "нет оптимальных альтернатив" if len(antiideal_point_info['optimal_alternatives']) == 0 else ', '.join(antiideal_point_info['optimal_alternatives'])
        file.write(f"Оптимальные альтернативы по принципу антиидеальной точки: {optimal_alternatives}\n\n")


        """Принцип Парето"""
        file.write("-" * 80 + "\n")
        file.write("Принцип оптимальности Парето".center(80) + "\n")
        file.write("-" * 80 + "\n\n")
        
        pareto_info = self.related_information_optimizing_task1['pareto']

        file.write("Подчиненные альтернативы:\n")
        if len(pareto_info['dominant_alternatives']) > 0:
            for alternative in pareto_info['dominant_alternatives']:
                file.write(f"\t{alternative}. Доминирующие альтернативы: {', '.join(pareto_info['dominant_alternatives'][alternative])}\n")
        else:
            file.write("Подчиненных альтернатив нет.\n")

        optimal_alternatives = "нет оптимальных альтернатив" if len(pareto_info['optimal_alternatives']) == 0 else ', '.join(pareto_info['optimal_alternatives'])
        file.write(f"\nФронт Парето: {optimal_alternatives}\n\n")
        

        """Принципы равенства и квазиравенства"""
        file.write("-" * 80 + "\n")
        file.write("Принципы равенства и квазиравенства".center(80) + "\n")
        file.write("-" * 80 + "\n\n")


        equal_info = self.related_information_optimizing_task1['equal']
        quasiequal_info = self.related_information_optimizing_task1['qequal']

        file.write("Взвешенные значения критериев\n")
        file.write(tabulate(equal_info["weighted_values"], headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n")

        file.write("Допустимые отклонения для пар взвешенных значений критериев:\n")
        for criterion1, criterion2 in list(combinations(quasiequal_info['sigma'].columns, 2)):
                file.write(f"\t{criterion1} и {criterion2}: {quasiequal_info['sigma'][criterion1].loc[criterion2]}\n")
        
        equal_values = ', '.join([f"{alter} ({equal_info['equal_values'][alter]})" for alter in equal_info['equal_values']])
        optimal_alternatives = "нет оптимальных альтернатив" if len(equal_info['optimal_alternatives']) == 0 else equal_values
        file.write(f"\nОптимальные альтернативы по принципу равенства: {optimal_alternatives}\n")
        optimal_alternatives = "нет оптимальных альтернатив" if len(quasiequal_info['optimal_alternatives']) == 0 else ', '.join(quasiequal_info['optimal_alternatives'])
        file.write(f"Оптимальные альтернативы по принципу квазиравенства: {optimal_alternatives}\n\n")
        

        """Принцип справедливой уступки"""
        file.write("-" * 80 + "\n")
        file.write("Принцип справедливой уступки".center(80) + "\n")
        file.write("-" * 80 + "\n\n")

        absolute_info = self.related_information_optimizing_task1['absolute']
        relative_info = self.related_information_optimizing_task1['relative']

        file.write("Взвешенные значения критериев\n")
        distances_table = absolute_info['data_with_common_criterion']
        distances_table.loc[relative_info['data_with_common_criterion'].index[-1]] = relative_info['data_with_common_criterion'].loc[relative_info['data_with_common_criterion'].index[-1]]
        file.write(tabulate(distances_table, headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n")

        optimal_alternatives = "нет оптимальных альтернатив" if len(absolute_info['optimal_alternatives']) == 0 else ', '.join(absolute_info['optimal_alternatives'])
        file.write(f"Оптимальные альтернативы по принципу абсолютной уступки: {optimal_alternatives}\n")
        optimal_alternatives = "нет оптимальных альтернатив" if len(relative_info['optimal_alternatives']) == 0 else ', '.join(relative_info['optimal_alternatives'])
        file.write(f"Оптимальные альтернативы по принципу относительной уступки: {optimal_alternatives}\n\n")
        

        """Принцип главного критерия"""
        file.write("-" * 80 + "\n")
        file.write("Принцип главного критерия".center(80) + "\n")
        file.write("-" * 80 + "\n\n")

        main_info = self.related_information_optimizing_task1['main']

        if main_info is None:
            file.write("Веса не позволяют определить главный критерий произвести расчеты по этому принципу\n\n")
        else:
            file.write(f"Главный критерий: {main_info['main_criterion']}\n")

            thresholds = ', '.join([f"{criterion}: {main_info['thresholds'][criterion]}" for criterion in main_info['thresholds']])
            file.write(f"Пороги для второстепенных критериев: {thresholds}\n\n")
            
            file.write(f"Альтернативы, для которых значения второстепенных критериев превосходят пороги отсечения:\n")
            file.write(tabulate(main_info['relevent_alternatives_data'], headers='keys', tablefmt='simple', showindex=True))

            optimal_alternatives = "нет оптимальных альтернатив" if len(main_info['optimal_alternatives']) == 0 else ', '.join(main_info['optimal_alternatives'])
            file.write(f"\n\nОптимальные альтернативы по принципу главного критерия: {optimal_alternatives}\n\n")
        

        """Принцип лексикографического равенства"""
        file.write("-" * 80 + "\n")
        file.write("Принцип лексикографического равенства".center(80) + "\n")
        file.write("-" * 80 + "\n\n")

        eq_lex_info = self.related_information_optimizing_task1['lex_equal']

        for criterion in eq_lex_info['criterions_history']:
            file.write(f"\tОтсечение по критерию {criterion}\n")
            file.write(tabulate(eq_lex_info['criterions_history'][criterion], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

        optimal_alternatives = "нет оптимальных альтернатив" if len(eq_lex_info['optimal_alternatives']) == 0 else ', '.join(eq_lex_info['optimal_alternatives'])
        file.write(f"Оптимальные альтернативы по принципу лексикографического равенства: {optimal_alternatives}\n\n")
        

        """Принцип лексикографического квазиравенства"""
        file.write("-" * 80 + "\n")
        file.write("Принцип лексикографического квазиравенства".center(80) + "\n")
        file.write("-" * 80 + "\n\n")

        quasi_eq_lex_info = self.related_information_optimizing_task1['lex_qequal']

        thresholds = ', '.join([f"{criterion}: {quasi_eq_lex_info['thresholds'][criterion]}" for criterion in quasi_eq_lex_info['thresholds']])
        file.write(f"Допустимые отклонения для критериев: {thresholds}\n")

        for criterion in quasi_eq_lex_info['criterions_history']:
            file.write(f"\tОтсечение по критерию {criterion}\n")
            file.write(tabulate(quasi_eq_lex_info['criterions_history'][criterion], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n")

        optimal_alternatives = "нет оптимальных альтернатив" if len(quasi_eq_lex_info['optimal_alternatives']) == 0 else ', '.join(quasi_eq_lex_info['optimal_alternatives'])
        file.write(f"\nОптимальные альтернативы по принципу лексикографического квазиравенства: {optimal_alternatives}\n\n")

        """Результаты применения принципов оптимизации"""
        file.write("-" * 80 + "\n")
        file.write("Результаты".center(80) + "\n")
        file.write("-" * 80 + "\n\n")

        optimal_alt = self.related_information_optimizing_task1['optimal_alternatives']
        file.write(tabulate(self.related_information_optimizing_task1['result'], headers='keys', tablefmt='simple', showindex=True))
        optimal_alternatives = "нет оптимальных альтернатив" if len(optimal_alt) == 0 else ', '.join(optimal_alt)
        
        file.write("\n\n" + "-" * 80 + "\n")
        file.write("|" + "ОПТИМАЛЬНЫЕ АЛЬТЕРНАТИВЫ".center(78) + "|\n")
        file.write("|" + f"{optimal_alternatives}".center(78) + "|\n")
        file.write("-" * 80 + "\n\n")

    """Обработка выполнения второго задания"""    
    def __write_input_data_for_second_task__(self, file):
        """Вывод информации о входных данных"""
        file.write("═" * 80 + "\n")
        file.write("РЕШЕНИЕ ЗАДАЧИ ПРИНЯТИЯ РЕШЕНИЙ В УСЛОВИЯХ НЕОПРЕДЕЛЕННОСТИ".center(80) + "\n")
        file.write("═" * 80 + "\n\n\n\n")

        file.write("-" * 80 + "\n")
        file.write("ИСХОДНЫЕ ДАННЫЕ".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")

        
        """Основные параметры"""
        file.write(f"Количество определенных критериев: {self.second_task_data['basic_parameters']['num_certain_criteria']}\n")
        file.write(f"Количество неопределенных критериев: {self.second_task_data['basic_parameters']['num_uncertain_criteria']}\n")
        file.write(f"Количество альтернатив: {self.second_task_data['basic_parameters']['num_alternatives']}\n\n\n")


        """Веса критериев"""
        file.write("Веса критериев:\n")
        cert_weights = self.second_task_data["weights"]["certain_weights"]
        for weight in cert_weights:
            file.write(f"\t{weight}: {cert_weights[weight]:.3f}; \n")
        uncert_weights = self.second_task_data["weights"]["uncertain_weights"]
        for weight in uncert_weights:
            file.write(f"\t{weight}: {uncert_weights[weight]:.3f}; \n")
        file.write("\n\n")

            
        """Методы снятия неопределенности"""
        file.write(f"Методы снятия неопределенности:\n")
        uncertainty_methods = self.second_task_data['uncertainty_methods']
        for criterion in uncertainty_methods:
            file.write(f"\t{criterion}: {uncertainty_methods[criterion]['method_name']}\n")
        file.write("\n\n")
        

        """Методы нормализации"""
        file.write(f"Методы нормализации критериев:\n")
        criteria_settings = self.second_task_data['normalization_settings']['normalization_methods']
        for criterion in criteria_settings:
            file.write(f"\t{criterion}: {criteria_settings[criterion]}\n")
        file.write("\n\n")


        """Методы смены направлений"""
        file.write("Смена направлений: ")

        criteria_settings = self.second_task_data['normalization_settings']['direction_methods']
        values_sev = self.second_task_data['normalization_settings']['savige_max_values']
        if len(criteria_settings) == 0:
                file.write("Направления критериев не меняются\n\n")
        else:
            file.write("\n")
            for criterion in criteria_settings:
                sample = "" if criteria_settings[criterion] != "savige" else f"Максимальное значение:{values_sev[criterion]}"
                file.write(f"\t{criterion}: {self.direction_vocabilary[criteria_settings[criterion]]}. {sample}\n")
            file.write("\n\n")


        """Значения критериев"""
        file.write("Значения определенных критериев:\n")
        file.write(tabulate(self.second_task_data["table_data"]["certain_data"], headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n")

        file.write("Значения неопределенных критериев:\n\n")
        unc_cr = self.second_task_data["table_data"]["uncertain_data"]
        for criterion in unc_cr:
            file.write(criterion)
            file.write(tabulate(unc_cr[criterion], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")
        file.write("\n\n")

    def __calculate_result_data_for_second_task__(self):
        """Предобработка"""
        direcion_settings = {
            'direction_changes': self.second_task_data['normalization_settings']['direction_methods'],
            'savige_max_values': self.second_task_data['normalization_settings']['savige_max_values']
        }
        normalization_methods = self.second_task_data['normalization_settings']['normalization_methods']

        preprocessing = UncertaintyRemoving(
            certain_data=self.second_task_data['table_data']['certain_data'],
            uncertain_data=self.second_task_data['table_data']['uncertain_data'], 
            uncertainty_settings=self.second_task_data['uncertainty_settings'], 
            uncertainty_methods=self.second_task_data['uncertainty_methods'], 
            normalization_methods=normalization_methods,
            direcion_settings=direcion_settings
        )
        evaluating_alternatives, related_information_preprocessing = preprocessing.get_processed_data()
        self.related_information_preprocessing_task2 = related_information_preprocessing


        """Принятие решений"""
        optimizing = DecisionMaking(
            data=evaluating_alternatives, 
            weights={
                **self.second_task_data['weights']['certain_weights'],
                **self.second_task_data['weights']['uncertain_weights']
            }
        )

        optimal_alternatives, related_information_optimizing = optimizing.uncertain_calculate(self.second_task_data['optimization_settings'])
        self.related_information_optimizing_task2 = related_information_optimizing

    def __write_results_for_second_task__(self, file):
        """Вывод информации о процессе предобработки данных"""
        file.write("-" * 80 + "\n")
        file.write("РЕЗУЛЬТАТЫ ПРЕДОБРАБОТКИ".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")

        
        """Смена направлений"""
        file.write("-" * 80 + "\n")
        file.write("Результат смены направлений".center(80) + "\n")
        file.write("-" * 80 + "\n")

        direction_changing_result = self.related_information_preprocessing_task2["direction_changing_result"]

        file.write("ОПРЕДЕЛЕННЫЕ КРИТЕРИИ\n")
        file.write(tabulate(direction_changing_result["certain"], headers='keys', tablefmt='simple', showindex=True))

        file.write("\n\nНЕОПРЕДЕЛЕННЫЕ КРИТЕРИИ\n\n")
        for criterion in direction_changing_result["uncertain"]:
            file.write(f"{criterion}\n")
            file.write(tabulate(direction_changing_result["uncertain"][criterion], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")
        file.write("\n\n")
        

        """Нормализация"""
        file.write("-" * 80 + "\n")
        file.write("Результат нормализации".center(80) + "\n")
        file.write("-" * 80 + "\n")

        normalization_result = self.related_information_preprocessing_task2["normalization_result"]

        file.write("ОПРЕДЕЛЕННЫЕ КРИТЕРИИ\n")
        file.write(tabulate(normalization_result["certain"], headers='keys', tablefmt='simple', showindex=True))
        
        file.write("\n\nНЕОПРЕДЕЛЕННЫЕ КРИТЕРИИ\n\n")
        for criterion in normalization_result["uncertain"]:
            file.write(f"{criterion}\n")
            file.write(tabulate(normalization_result["uncertain"][criterion], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")
        file.write("\n\n")


        """Снятие неопределенности"""
        file.write("\n\n" + "-" * 80 + "\n")
        file.write("Снятие неопределенности".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")

        removing_methods = self.related_information_preprocessing_task2["uncertainty_removing"]["methods"]
        related_removing_info = self.related_information_preprocessing_task2["uncertainty_removing"]["data"]

        uncertainty_settings = self.second_task_data['uncertainty_settings']
        uncertainty_probabilities = uncertainty_settings['probabilities']
        uncertainty_methods = self.second_task_data['uncertainty_methods']

        for criterion in removing_methods:
            file.write(f"КРИТЕРИЙ. {criterion}\n")
            #print(removing_methods[criterion])
            if removing_methods[criterion]['method_name'] == 'Критерий Байеса-Лапласа':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                if len(uncertainty_probabilities[criterion]) > 0:
                    file.write(f"\tСостояния среды:\n")
                    for state in uncertainty_probabilities[criterion]:
                        file.write(f"\t\t{state}: {uncertainty_probabilities[criterion][state]:.3f}\n")
                
                file.write(f"\nРасчитана взвешенная сумма состояний\n\n\n")

            elif removing_methods[criterion]['method_name'] == 'Критерий минимальной среднеквадратичной ошибки':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                if len(uncertainty_probabilities[criterion]) > 0:
                    file.write(f"\tСостояния среды:\n")
                    for state in uncertainty_probabilities[criterion]:
                        file.write(f"\t\t{state}: {uncertainty_probabilities[criterion][state]:.3f}\n")
                file.write(f"\n\tТип величины: {related_removing_info[criterion]['value_type']}\n\n")

                file.write("Взвешенная сумма состояний:\n")
                file.write(tabulate(related_removing_info[criterion]['weighted_data'], headers='keys', tablefmt='simple', showindex=True))
                
                file.write("\n\nОтклонения:") 
                file.write(tabulate(related_removing_info[criterion]['differences'], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n")

            elif removing_methods[criterion]['method_name'] == 'Критерий максимальной вероятности':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                if len(uncertainty_probabilities[criterion]) > 0:
                    file.write(f"\tСостояния среды:\n")
                    for state in uncertainty_probabilities[criterion]:
                        file.write(f"\t\t{state}: {uncertainty_probabilities[criterion][state]:.3f}\n")
                file.write(f"\n\tПорог значений критерия: {related_removing_info[criterion]['threshold']}\n\n")

                file.write("Вероятности состояний с наложенным условием (> порога):\n")
                file.write(tabulate(related_removing_info[criterion]['states_probability_with_condition'], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n")

            elif removing_methods[criterion]['method_name'] == 'Модальный критерий':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                if len(uncertainty_probabilities[criterion]) > 0:
                    file.write(f"\tСостояния среды:\n")
                    for state in uncertainty_probabilities[criterion]:
                        file.write(f"\t\t{state}: {uncertainty_probabilities[criterion][state]:.3f}\n")

                file.write(f"\nСостояния с максимальными вероятностями: {', '.join(related_removing_info[criterion]['best_states'])}\n\n\n")

            elif removing_methods[criterion]['method_name'] == 'Критерий минимума энтропии':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                if len(uncertainty_probabilities[criterion]) > 0:
                    file.write(f"\tСостояния среды:\n")
                    for state in uncertainty_probabilities[criterion]:
                        file.write(f"\t\t{state}: {uncertainty_probabilities[criterion][state]:.3f}\n")
                file.write("\n")

                if not related_removing_info[criterion]['condition']:
                    file.write("Данные были скорректированы для соответствия условиям критерия\n")
                    file.write(f"Максимальное значение: {related_removing_info[criterion]['max_value']}\n")
                    file.write("Исправленные  значения критерия: \n")
                    file.write(tabulate(related_removing_info[criterion]['fixed_data'], headers='keys', tablefmt='simple', showindex=True))
                    file.write("\n\n")

                file.write("Взвешенные значения критерия:\n")
                file.write(tabulate(related_removing_info[criterion]['weighted_matrix'], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n")

            elif removing_methods[criterion]['method_name'] == 'Критерий Гермейера':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                if len(uncertainty_probabilities[criterion]) > 0:
                    file.write(f"\tСостояния среды:\n")
                    for state in uncertainty_probabilities[criterion]:
                        file.write(f"\t\t{state}: {uncertainty_probabilities[criterion][state]:.3f}\n")
                file.write("\n")

                if not related_removing_info[criterion]['condition']:
                    file.write("Данные были скорректированы для соответствия условиям критерия\n")
                    file.write(f"Максимальное значение: {related_removing_info[criterion]['max_value']}\n")
                    file.write("Исправленные  значения критерия: \n")
                    file.write(tabulate(related_removing_info[criterion]['fixed_data'], headers='keys', tablefmt='simple', showindex=True))
                    file.write("\n\n\n")
                else:
                    file.write("Минимум взвешенных значений критерия был расчитан\n\n\n")

            elif removing_methods[criterion]['method_name'] == 'Критерий Вальда':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n\n")
                
                file.write(f"\n\tРасчитаны минимальные значения критерия\n\n\n")
                
            elif removing_methods[criterion]['method_name'] == 'Критерий минимаксного Сэвиджа':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n\n")
                
                file.write(f"Матрица штрафов:\n")
                file.write(tabulate(related_removing_info[criterion]['penalty_matrix'], headers='keys', tablefmt='simple', showindex=True))
                file.write(f"\n\n\n")

            elif removing_methods[criterion]['method_name'] == 'Критерий Гурвица':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                file.write(f"\n\tСтепень склонности ЛПР к риску: {related_removing_info[criterion]['risk_attitude']}\n")
                
                file.write(f"\nРасчитано значение критерия Гурвица\n\n\n")
                
            elif removing_methods[criterion]['method_name'] == 'Критерий Ходжеса-Лемана':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                if len(uncertainty_probabilities[criterion]) > 0:
                    file.write(f"\tСостояния среды:\n")
                    for state in uncertainty_probabilities[criterion]:
                        file.write(f"\t\t{state}: {uncertainty_probabilities[criterion][state]:.3f}\n")
                file.write(f"\n\tПараметр кр. Ходжеса-Лемана: {related_removing_info[criterion]['hl_parameter']}\n\n")

                file.write("Взвешенная сумма состояний:\n")
                file.write(tabulate(related_removing_info[criterion]['weighted_data'], headers='keys', tablefmt='simple', showindex=True))
                
                file.write("\n\nМинимумы значений критериев:") 
                file.write(tabulate(related_removing_info[criterion]['min_data'], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n")

            elif removing_methods[criterion]['method_name'] == 'Универсальный критерий':
                file.write(f"\tСитуация априорной информированности. {uncertainty_methods[criterion]['situation_type']}\n")
                file.write(f"\tМетод снятия неопределенности. {uncertainty_methods[criterion]['method_name']}\n")
                if len(uncertainty_probabilities[criterion]) > 0:
                    file.write(f"\tСостояния среды:\n")
                    for state in uncertainty_probabilities[criterion]:
                        file.write(f"\t\t{state}: {uncertainty_probabilities[criterion][state]:.3f}\n")
                file.write(f"\n\tСтепень склонности ЛПР к риску: {related_removing_info[criterion]['risk_attitude']}\n")
                file.write(f"\tПараметр дополнительного критерия: {related_removing_info[criterion]['additional_param']}\n")
                file.write(f"\tУровень доверия: {related_removing_info[criterion]['trust_level']}\n\n")

                if 'weighted_data' in related_removing_info[criterion]:
                    file.write("Взвешенная сумма состояний:\n")
                    file.write(tabulate(related_removing_info[criterion]['weighted_data'], headers='keys', tablefmt='simple', showindex=True))

                    file.write("\n\nОтклонения от среднего значения:\n")
                    file.write(tabulate(related_removing_info[criterion]['sigma_data'], headers='keys', tablefmt='simple', showindex=True))

                    file.write("\n\nЗначения критерия Гурвица:\n")
                    file.write(tabulate(related_removing_info[criterion]['gurcvitz_criteria'], headers='keys', tablefmt='simple', showindex=True))

                    file.write("\n\nЗначения дополнительного критерия:\n")
                    file.write(tabulate(related_removing_info[criterion]['additional_criteria'], headers='keys', tablefmt='simple', showindex=True))
                    file.write("\n\n\n")
                else:
                    file.write(f"\nРасчитано значение критерия Гурвица\n\n\n")

        file.write("Результат снятия неопределенности:\n")        
        file.write(tabulate(self.related_information_preprocessing_task2["result_criterions_values"], headers='keys', tablefmt='simple', showindex=True))
        file.write("\n\n")


        """Вывод информации о применении принципов оптимизации"""
        file.write("\n\n" + "-" * 80 + "\n")
        file.write("РЕЗУЛЬТАТЫ ПРИНЯТИЯ РЕШЕНИЯ".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")

        optimization_principle = self.second_task_data['optimization_settings']['optimization_principle']
        file.write(f"Принцип оптимальности: {optimization_principle}\n")
        file.write(f"Порог для отсечения: {self.second_task_data['optimization_settings']['constraint_value']}\n\n")

        info = self.related_information_optimizing_task2

        if optimization_principle == "Принцип идеальной точки": 
            file.write(f"Данные для ограничения:\n")
            file.write(tabulate(info["restriction_function"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

            iterable_points = ' '.join([f"{alter}: {info['restriction']['ideal_point'].loc[alter]}," for alter in info['restriction']['ideal_point'].index])
            file.write(f"Идеальная точка. {iterable_points}\n")

            file.write("Расстояния до идеальной точки\n")
            file.write(tabulate(info['restriction']['data_with_distances_to_ideal_point'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n") 

            file.write(f"Данные для целевых переменных (с учетом отсечения):\n")
            file.write(tabulate(info["target_function"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

            iterable_points = ' '.join([f"{alter}: {info['target']['ideal_point'].loc[alter]}," for alter in info['target']['ideal_point'].index])
            file.write(f"Идеальная точка. {iterable_points}\n")

            file.write("Расстояния до идеальной точки\n")
            file.write(tabulate(info['target']['data_with_distances_to_ideal_point'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n") 

        elif optimization_principle == "Принцип антиидеальной точки":
            file.write(f"Данные для ограничения:\n")
            file.write(tabulate(info["restriction_function"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

            iterable_points = ' '.join([f"{alter}: {info['restriction']['anti_ideal_point'].loc[alter]}," for alter in info['restriction']['anti_ideal_point'].index])
            file.write(f"Антиидеальная точка. {iterable_points}\n")

            file.write("Расстояния до антиидеальной точки\n")
            file.write(tabulate(info['restriction']['data_with_distances_to_anti_ideal_point'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n") 

            file.write(f"Данные для целевых переменных (с учетом отсечения):\n")
            file.write(tabulate(info["target_function"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

            iterable_points = ' '.join([f"{alter}: {info['target']['anti_ideal_point'].loc[alter]}," for alter in info['target']['anti_ideal_point'].index])
            file.write(f"Антиидеальная точка. {iterable_points}\n")

            file.write("Расстояния до антиидеальной точки\n")
            file.write(tabulate(info['target']['data_with_distances_to_anti_ideal_point'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n") 

        elif optimization_principle == "Принцип абсолютной уступки":
            file.write(f"Данные для ограничения:\n")
            file.write(tabulate(info["restriction_function"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

            file.write("Взвешенные суммы критериев\n")
            file.write(tabulate(info['restriction']['data_with_common_criterion'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n") 

            file.write(f"Данные для целевых переменных (с учетом отсечения):\n")
            file.write(tabulate(info["target_function"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

            file.write("Взвешенные суммы критериев\n")
            file.write(tabulate(info['target']['data_with_common_criterion'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n") 
            
        elif optimization_principle == "Принцип относительной уступки":
            file.write(f"Данные для ограничения:\n")
            file.write(tabulate(info["restriction_function"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

            file.write("Взвешенные произведения критериев\n")
            file.write(tabulate(info['restriction']['data_with_common_criterion'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n") 

            file.write(f"Данные для целевых переменных (с учетом отсечения):\n")
            file.write(tabulate(info["target_function"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n")

            file.write("Взвешенные произведения критериев\n")
            file.write(tabulate(info['target']['data_with_common_criterion'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n") 

        """Результаты применения принципов оптимизации"""
        optimal_alternatives = "нет оптимальных альтернатив" if len(info['target']['optimal_alternatives']) == 0 else ', '.join(info['target']['optimal_alternatives'])
        
        file.write("\n\n" + "-" * 80 + "\n")
        file.write("|" + "ОПТИМАЛЬНЫЕ АЛЬТЕРНАТИВЫ".center(78) + "|\n")
        file.write("|" + f"{optimal_alternatives}".center(78) + "|\n")
        file.write("-" * 80 + "\n\n")

    """Обработка выполнения третьего задания"""    
    def __write_input_data_for_third_task__(self, file):
        """Вывод информации о входных данных"""
        file.write("═" * 80 + "\n")
        file.write("РЕШЕНИЕ ЗАДАЧИ ПРИНЯТИЯ РЕШЕНИЙ ПРИ ПОМОЩИ НЕЧЕТКОЙ ЛОГИКИ".center(80) + "\n")
        file.write("═" * 80 + "\n\n\n\n")

        file.write("-" * 80 + "\n")
        file.write("ИСХОДНЫЕ ДАННЫЕ".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")
        
        """Тип задачи"""
        task_type = self.third_task_data['task_type']
        file.write(f"Тип задачи: {task_type}\n")

        if task_type == 'Принятие решения в условиях неаддитивности критериев':
            """Основные параметры"""
            file.write(f"Количество критериев: {self.third_task_data['basic_parameters']['num_criteria']}\n")
            file.write(f"Количество альтернатив: {self.third_task_data['basic_parameters']['num_alternatives']}\n\n\n")
            
            """Веса критериев"""
            file.write("Веса критериев:\n")
            weights = self.third_task_data["weights"]
            for weight in weights:
                file.write(f"\t{weight}: {weights[weight]:.3f}; \n")
            file.write("\n\n")
            
            """Степени соответствия"""
            file.write("Степени соответствия альтернатив критериям:\n")
            file.write(tabulate(self.third_task_data["table_data"], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n\n\n")


        elif task_type == 'Принятие решения в условиях аддитивности критериев':
            """Метод задания соответствия"""
            evaluation_method = self.third_task_data['evaluation_method']
            file.write(f"Метод задания соответствия: {evaluation_method}\n")

            if evaluation_method == 'Нечеткие числа':
                """Основные параметры"""
                file.write(f"Количество критериев: {self.third_task_data['basic_parameters']['num_criteria']}\n")
                file.write(f"Количество альтернатив: {self.third_task_data['basic_parameters']['num_alternatives']}\n\n\n")
                
                """Веса критериев"""
                file.write("Веса критериев:\n")
                weights = self.third_task_data["weights"]
                for weight in weights:
                    file.write(f"\t{weight}: {weights[weight]:.3f}; \n")
                file.write("\n\n")
                
                """Степени соответствия"""
                file.write("Степени соответствия альтернатив критериям:\n")
                file.write(tabulate(self.third_task_data["table_data"], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n\n")

            elif evaluation_method == 'Функции принадлежности':
                """Основные параметры"""
                file.write(f"Количество критериев: {self.third_task_data['basic_parameters']['num_criteria']}\n")
                file.write(f"Количество альтернатив: {self.third_task_data['basic_parameters']['num_alternatives']}\n")
                file.write(f"Количество степеней соответствия альтернатив критериям: {self.third_task_data['basic_parameters']['num_compliance_degrees']}\n")
                file.write(f"Количество степеней важности критериев: {self.third_task_data['basic_parameters']['num_importance_degrees']}\n")
                file.write(f"Метод дефаззификации результата: {self.third_task_data['defuzzification_method']}\n\n\n")
                
                """Степеней соответствия"""
                file.write("Степени соответствия критериям:\n")
                file.write(tabulate(self.third_task_data['membership_functions']["compliance"], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n")
                
                """Степени важности"""
                file.write("Степени важности:\n")
                file.write(tabulate(self.third_task_data['membership_functions']["importance"], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n")

                """Веса критериев"""
                file.write("Cтепени важности критериев:\n")
                weights = self.third_task_data["criteria_weights"]
                for weight in weights.index:
                    file.write(f"\t{weight}: {weights.loc[weight]}; \n")
                file.write("\n\n")
                
                """Степени соответствия альтернатив"""
                file.write("Степени соответствия альтернатив критериям:\n")
                file.write(tabulate(self.third_task_data['alternative_ratings'].T, headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n\n")

        elif task_type == 'Принятие решения на основе нечетких систем':
            """Основные параметры"""
            file.write(f"Количество критериев: {self.third_task_data['basic_parameters']['num_criteria']}\n")
            file.write(f"Количество альтернатив: {self.third_task_data['basic_parameters']['num_alternatives']}\n")
            file.write(f"Количество степеней соответствия альтернатив критериям: {self.third_task_data['basic_parameters']['num_compliance_degrees']}\n")
            file.write(f"Количество правил: {self.third_task_data['basic_parameters']['num_rules']}\n\n\n")

            """Оценки критериев"""
            file.write("Оценки критериев\Степени соответствия:\n")
            file.write(tabulate(self.third_task_data['compliance_characteristics'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n\n")
                
            """Степени соответствия альтернатив"""
            file.write("Степени соответствия альтернатив критериям:\n")
            file.write(tabulate(self.third_task_data['membership_data'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n\n")

            """Правила нечеткой системы"""
            file.write("Правила нечеткой системы:\n")
            rules = self.third_task_data["rules"]
            for rule in rules.index:
                file.write(f"\tЕСЛИ {' И '.join(f'{criterion} имеет оценку {rules[criterion].loc[rule]}' for criterion in rules.columns if criterion != 'result')} ТО Общая оценка {rules['result'].loc[rule]}; \n")
            file.write("\n\n\n\n")
        
    def __calculate_result_data_for_third_task__(self):
        """Обработка"""
        processing = FuzzyLogic(self.third_task_data)
        self.processing_data_task3 = processing.calculate()
        
    def __write_results_for_third_task__(self, file):
        """Вывод информации о процессе предобработки данных"""
        file.write("-" * 80 + "\n")
        file.write("РЕЗУЛЬТАТЫ ВЫЧИСЛЕНИЙ".center(80) + "\n")
        file.write("-" * 80 + "\n\n\n")

        task_type = self.third_task_data['task_type']

        if task_type == 'Принятие решения в условиях неаддитивности критериев':
            file.write("Взвешенные данные с указанием минимальных степеней принадлежности:\n")
            file.write(tabulate(self.processing_data_task3['data_with_belonging'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n\n\n")

        elif task_type == 'Принятие решения в условиях аддитивности критериев':
            evaluation_method = self.third_task_data['evaluation_method']

            if evaluation_method == 'Нечеткие числа':
                file.write("Взвешенные данные с указанием усредненных степеней соответствия:\n")
                file.write(tabulate(self.processing_data_task3['data_with_belonging'], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n\n")

            elif evaluation_method == 'Функции принадлежности':
                file.write("Усредненные функции принадлежности (треугольная форма) с дефаззифицированными данными:\n")
                file.write(tabulate(self.processing_data_task3['defazzified_data'], headers='keys', tablefmt='simple', showindex=True))
                file.write("\n\n\n\n")

        elif task_type == 'Принятие решения на основе нечетких систем':
            file.write("Степени соответствия альтернатив после дефаззификации:\n")
            file.write(tabulate(self.processing_data_task3['data_with_measure'], headers='keys', tablefmt='simple', showindex=True))
            file.write("\n\n\n\n")
        
        """Результаты применения нечеткой логики"""
        file.write("-" * 80 + "\n")
        file.write("Результаты".center(80) + "\n")
        file.write("-" * 80 + "\n\n")

        optimal_alternatives = "нет оптимальных альтернатив" if len(self.processing_data_task3['optimal_alternatives']) == 0 else ', '.join(self.processing_data_task3['optimal_alternatives'])
        
        file.write("\n\n" + "-" * 80 + "\n")
        file.write("|" + "ОПТИМАЛЬНЫЕ АЛЬТЕРНАТИВЫ".center(78) + "|\n")
        file.write("|" + f"{optimal_alternatives}".center(78) + "|\n")
        file.write("-" * 80 + "\n\n")

    def create(self, filename='default'):
        while filename + '.txt' in os.listdir("Reports"):
            filename = filename + "(1)"

        with open(os.path.join("Reports", filename + '.txt'), 'w', encoding='utf-8') as f:
            f.write("╔" + "═" * 78 + "╗\n")
            f.write("║" + "ОТЧЕТ О ВЫЧИСЛЕНИЯХ".center(78) + "║\n")
            f.write("╚" + "═" * 78 + "╝\n\n\n\n\n")

            if not self.first_task_data is None:
                self.__write_input_data_for_first_task__(file=f)
                self.__calculate_result_data_for_first_task__()
                self.__write_results_for_first_task__(file=f)
                f.write("\n\n\n")

            if not self.second_task_data is None:
                self.__write_input_data_for_second_task__(file=f)
                self.__calculate_result_data_for_second_task__()
                self.__write_results_for_second_task__(file=f)
                f.write("\n\n\n")

            if not self.third_task_data is None:
                self.__write_input_data_for_third_task__(file=f)
                self.__calculate_result_data_for_third_task__()
                self.__write_results_for_third_task__(file=f)
                f.write("\n\n\n")

        
        print(f"Табличный отчет сохранен в: {filename}")###########Удалить