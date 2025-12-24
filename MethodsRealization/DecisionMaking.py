from copy import copy
import numpy as np
import pandas as pd
from math import isclose, log, prod
from itertools import combinations


class DecisionMaking:
    methods_vocabulary = {
        'idp': 'Принцип идеальной точки',
        'aidp': 'Принцип антиидеальной точки',
        'pareto': 'Принцип оптимальности по Парето',
        'equal': 'Принцип равенства',
        'qequal': 'Принцип квазиравенства',
        'absolute': 'Принцип абсолютной уступки',
        'relative': 'Принцип относительной уступки',
        'main': 'Принцип главного критерия',
        'lex_equal': 'Лексикографический принцип равенства',
        'lex_qequal': 'Лексикографический принцип квазиравенства'
    }

    def __init__(self, data, weights=None):
        self.data = data
        self.weights = weights

    def __eucl__(self, x, y):
        weights = {criterion: 1 for criterion in x.index} if self.weights is None else self.weights
        return sum((weights[criterion] * (x.loc[criterion] - y.loc[criterion])) ** 2 for criterion in x.index) ** 0.5

    """Принципы оптимальности"""
    def __ideal_point__(self, idp=None, metric=None):
        if metric is None:
            metric = self.__eucl__

        idp = pd.Series({criterion: max(self.data.loc[criterion]) for criterion in self.data.index}) if idp is None else pd.Series(idp)
        estimated_value = {alternative: metric(self.data[alternative], idp) for alternative in self.data.columns}

        optimal_alternatives = [alter for alter in estimated_value if estimated_value[alter] == min(estimated_value.values())]
        data_with_distances = self.data.copy()
        data_with_distances.loc['Расстояния до идеальной точки', :] = [estimated_value[alternative] for alternative in self.data.columns]

        dump = {
            'ideal_point': idp,
            'optimal_alternatives': optimal_alternatives,
            'data_with_distances_to_ideal_point': data_with_distances
        }

        return optimal_alternatives, dump

    def __antiideal_point__(self, aidp=None, metric=None):
        if metric is None:
            metric = self.__eucl__

        aidp = pd.Series({criterion: min(self.data.loc[criterion]) for criterion in self.data.index}) if aidp is None else pd.Series(aidp)
        estimated_value = {alternative: metric(self.data[alternative], aidp) for alternative in self.data.columns}

        optimal_alternatives = [alter for alter in estimated_value if estimated_value[alter] == max(estimated_value.values())]
        data_with_distances = self.data.copy()
        data_with_distances.loc['Расстояния до антиидеальной точки', :] = [estimated_value[alternative] for alternative in self.data.columns]

        dump = {
            'anti_ideal_point': aidp,
            'optimal_alternatives': optimal_alternatives,
            'data_with_distances_to_anti_ideal_point': data_with_distances
        }

        return optimal_alternatives, dump

    def __pareto_domination__(self, target_alternative, compared_alternative):
        return all(target_alternative.loc[criterion] >= compared_alternative.loc[criterion] for criterion in target_alternative.index)\
              and any(target_alternative.loc[criterion] > compared_alternative.loc[criterion] for criterion in target_alternative.index)

    def __Pareto__(self):
        dump = {}

        alternatives = self.data.columns
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights

        front_pareto = [alternative for alternative in alternatives if not any(self.__pareto_domination__(self.data[compares_alternative], self.data[alternative]) for compares_alternative in alternatives)]
        dominant_alternatives = {
            alternative: [dominant_alternative for dominant_alternative in alternatives if self.__pareto_domination__(self.data[dominant_alternative], self.data[alternative])] for alternative in alternatives 
            if any(self.__pareto_domination__(self.data[compares_alternative], self.data[alternative]) for compares_alternative in alternatives)
        }
        
        result_data = self.data[front_pareto].copy()
        result_data.loc['Взвешенное среднее значение критериев'] = (result_data.mul(pd.Series(weights), axis=0).sum(axis=0))

        dump = {
            'dominant_alternatives': dominant_alternatives,
            'optimal_alternatives': front_pareto,
            'result_data': result_data
        }

        return front_pareto, dump

    def __equal_principle__(self):
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights

        weighted_data = self.data.mul(pd.Series(weights), axis=0)
        optimal_alternatives = [
            alternative for alternative in self.data.columns 
            if all(isclose(weighted_data[alternative].loc[criterion1], weighted_data[alternative].loc[criterion2]) 
                   for criterion1 in self.data.index for criterion2 in self.data.index)
        ]

        for criterion1, criterion2 in list(combinations(weighted_data.index, 2)):
            weighted_data.loc[f'Разница критериев {criterion1} и {criterion2}', :] = [
                abs(weighted_data.loc[criterion1, alternative] - weighted_data.loc[criterion2, alternative]) for alternative in weighted_data.columns
            ]

        dump = {
            'equal_values': {alternative: self.data[alternative].loc[self.data.index[0]] * weights[self.data.index[0]] for alternative in optimal_alternatives},
            'optimal_alternatives': optimal_alternatives,
            'weighted_values': weighted_data
        }

        return optimal_alternatives, dump

    def __quasi_equal_principle__(self, sigma):
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights

        weighted_data = self.data.mul(pd.Series(weights), axis=0)
        optimal_alternatives = [
            alternative for alternative in self.data.columns 
            if all(isclose(weighted_data[alternative].loc[criterion1], weighted_data[alternative].loc[criterion2], abs_tol=sigma[criterion1].loc[criterion2]) 
                   for criterion1 in self.data.index for criterion2 in self.data.index)
        ]

        for criterion1, criterion2 in list(combinations(weighted_data.index, 2)):
            weighted_data.loc[f'Разница критериев {criterion1} и {criterion1}', :] = [
                abs(weighted_data.loc[criterion1, alternative] - weighted_data.loc[criterion2, alternative]) for alternative in weighted_data.columns
            ]

        dump = {
            'sigma': sigma,
            'weighted_values': weighted_data,
            'optimal_alternatives': optimal_alternatives
        }

        return optimal_alternatives, dump

    def __absolute_concession__(self):
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights
        
        data_with_common_criterion = self.data.copy()
        data_with_common_criterion.loc['Взвешенная сумма критериев', :] = [(self.data[alternative] * pd.Series(weights)).sum() for alternative in self.data.columns]
        optimal_alternatives = data_with_common_criterion.columns[data_with_common_criterion.loc['Взвешенная сумма критериев'] == data_with_common_criterion.loc['Взвешенная сумма критериев'].max()].tolist()
        
        dump = {
            'data_with_common_criterion': data_with_common_criterion,
            'optimal_alternatives': optimal_alternatives
        }

        return optimal_alternatives, dump

    def __relative_concession__(self):
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights
        
        data_with_common_criterion = self.data.copy()
        data_with_common_criterion.loc['Взвешенное произведение критериев', :] = [prod(self.data[alternative].loc[criterion] ** weights[criterion] for criterion in self.data.index) for alternative in self.data.columns]
        optimal_alternatives = data_with_common_criterion.columns[data_with_common_criterion.loc['Взвешенное произведение критериев'] == data_with_common_criterion.loc['Взвешенное произведение критериев'].max()].tolist()
        
        dump = {
            'data_with_common_criterion': data_with_common_criterion,
            'optimal_alternatives': optimal_alternatives
        }

        return optimal_alternatives, dump

    def __main_criterion__(self, thresholds):
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights
        main = [criterion for criterion in weights if weights[criterion] == max(weights.values())]

        relevent_alternatives_data = self.data[[
            alternative for alternative in self.data.columns 
            if all(self.data[alternative].loc[criterion] >= threshold 
                   for criterion, threshold in thresholds.items())
                   ]]
        
        optimal_alternatives = relevent_alternatives_data[[
            alternative for alternative in relevent_alternatives_data.columns 
            if (relevent_alternatives_data[alternative].loc[main] == relevent_alternatives_data.loc[main].max().max()).item()
                   ]]
        
        dump = {
            'relevent_alternatives_data': relevent_alternatives_data,
            'optimal_alternatives': optimal_alternatives,
            'main_criterion': main[0],
            'thresholds': thresholds

        }

        return optimal_alternatives, dump
        
    def __lexicographic_equal__(self):
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights
        prioritet = sorted(weights, key=weights.get, reverse=True)

        prioritet_data = self.data.copy()
        criterions_history = {}
        for criterion in prioritet:
            prioritet_data = prioritet_data[prioritet_data.columns[prioritet_data.loc[criterion] == prioritet_data.loc[criterion].max()].tolist()]
            criterions_history[criterion] = prioritet_data

            if len(prioritet_data.columns) == 1:
                break
        
        optimal_alternatives = prioritet_data.columns
        
        dump = {
            'criterions_history': criterions_history,
            'optimal_alternatives': optimal_alternatives
        }

        return optimal_alternatives, dump

    def __lexicographic_quasiequal__(self, thresholds):
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights
        prioritet = sorted(weights, key=weights.get, reverse=True)

        prioritet_data = self.data.copy()
        criterions_history = {}
        for criterion in prioritet:
            prioritet_data = prioritet_data[prioritet_data.columns[abs(prioritet_data.loc[criterion] - prioritet_data.loc[criterion].max()) <= thresholds[criterion]].tolist()]
            criterions_history[criterion] = prioritet_data

            if len(prioritet_data.columns) == 1:
                break
        
        optimal_alternatives = prioritet_data.columns
        
        dump = {
            'thresholds': thresholds,
            'criterions_history': criterions_history,
            'optimal_alternatives': optimal_alternatives
        }

        return optimal_alternatives, dump

    """Перебор принципов"""
    def calculate(self, parameters):
        related_information = {}
        optimal_alternatives = {}
        weights = {criterion: 1 for criterion in self.data.index} if self.weights is None else self.weights

        optimal_alternatives['idp'], related_information['idp'] = self.__ideal_point__(idp=parameters['idp'], metric=parameters['metric'])
        optimal_alternatives['aidp'], related_information['aidp'] = self.__antiideal_point__(aidp=parameters['aidp'], metric=parameters['metric'])
        optimal_alternatives['pareto'], related_information['pareto'] = self.__Pareto__()
        optimal_alternatives['equal'], related_information['equal'] = self.__equal_principle__()
        optimal_alternatives['qequal'], related_information['qequal'] = self.__quasi_equal_principle__(sigma=parameters['sigma'])
        optimal_alternatives['absolute'], related_information['absolute'] = self.__absolute_concession__()
        optimal_alternatives['relative'], related_information['relative'] = self.__relative_concession__()
        if len([weight for weight in weights.values() if weight == max(weights.values())]) == 1:
            optimal_alternatives['main'], related_information['main'] = self.__main_criterion__(thresholds=parameters['main_thresholds'])
        else:
            optimal_alternatives['main'] = None
            related_information['main'] = None
        optimal_alternatives['lex_equal'], related_information['lex_equal'] = self.__lexicographic_equal__()
        optimal_alternatives['lex_qequal'], related_information['lex_qequal'] = self.__lexicographic_quasiequal__(thresholds=parameters['quasi_equal_thresholds'])

        result_data = pd.DataFrame(index=optimal_alternatives.keys(), columns=self.data.columns)
        for method, opt_alternatives in optimal_alternatives.items():
            if method == 'main' and opt_alternatives is None:
                opt_alternatives = []
            for alternative in result_data.columns:
                result_data.loc[method, alternative] = '✓' if alternative in opt_alternatives else '✗'
        result_data.rename(index=self.methods_vocabulary, inplace=True)
        
        result_data.loc['Количество методов'] = result_data.apply(lambda col: (col == '✓').sum())
        related_information['result'] = result_data
        
        optimal_alternatives = [
            alternative for alternative in result_data.columns 
            if (result_data[alternative].loc['Количество методов'] == result_data.loc['Количество методов'].max())
        ]
        related_information['optimal_alternatives'] = optimal_alternatives

        return optimal_alternatives, related_information

    """Расчет на основе целевой функции"""
    def uncertain_calculate(self, parameters):
        related_information = {}

        target_function_criterion = [criterion for (criterion, function_type) in parameters['function_types'].items() if function_type == 'Целевая функция']
        restriction_function_criterion = [criterion for (criterion, function_type) in parameters['function_types'].items() if function_type == 'Функция ограничения']
        common_data = self.data
        restriction_function = self.data.loc[restriction_function_criterion]
        self.data = restriction_function
        related_information['restriction_function'] = restriction_function

        if parameters['optimization_principle'] == "Принцип идеальной точки":
            target_idp = {criterion: value for criterion, value in parameters['ideal_point'].items() if criterion in target_function_criterion}
            restriction_idp = {criterion: value for criterion, value in parameters['ideal_point'].items() if criterion in restriction_function_criterion}
            _, related_information['restriction'] = self.__ideal_point__(restriction_idp)

            restriction_values = related_information['restriction']['data_with_distances_to_ideal_point']
            relevant_alternatives = restriction_values.columns[restriction_values.loc['Расстояния до идеальной точки'] < parameters['constraint_value']]
            
            target_function = common_data.loc[target_function_criterion, relevant_alternatives]
            self.data = target_function
            related_information['target_function'] = target_function

            optimal_alternatives, related_information['target'] = self.__ideal_point__(target_idp)

        elif parameters['optimization_principle'] == "Принцип антиидеальной точки":
            target_aidp = {criterion: value for criterion, value in parameters['anti_ideal_point'].items() if criterion in target_function_criterion}
            restriction_aidp = {criterion: value for criterion, value in parameters['anti_ideal_point'].items() if criterion in restriction_function_criterion}
            _, related_information['restriction'] = self.__antiideal_point__(restriction_aidp)

            restriction_values = related_information['restriction']['data_with_distances_to_anti_ideal_point']
            relevant_alternatives = restriction_values.columns[restriction_values.loc['Расстояния до антиидеальной точки'] > parameters['constraint_value']]
            
            target_function = common_data.loc[target_function_criterion, relevant_alternatives]
            self.data = target_function
            related_information['target_function'] = target_function

            optimal_alternatives, related_information['target'] = self.__antiideal_point__(target_aidp)

        elif parameters['optimization_principle'] == "Принцип абсолютной уступки":
            _, related_information['restriction'] = self.__absolute_concession__()

            restriction_values = related_information['restriction']['data_with_common_criterion']
            relevant_alternatives = restriction_values.columns[restriction_values.loc['Взвешенная сумма критериев'] > parameters['constraint_value']]
            
            target_function = common_data.loc[target_function_criterion, relevant_alternatives]
            self.data = target_function
            related_information['target_function'] = target_function

            optimal_alternatives, related_information['target'] = self.__absolute_concession__()

        elif parameters['optimization_principle'] == "Принцип относительной уступки":
            _, related_information['restriction'] = self.__relative_concession__()

            restriction_values = related_information['restriction']['data_with_common_criterion']
            relevant_alternatives = restriction_values.columns[restriction_values.loc['Взвешенное произведение критериев'] > parameters['constraint_value']]
            
            target_function = common_data.loc[target_function_criterion, relevant_alternatives]
            self.data = target_function
            related_information['target_function'] = target_function

            optimal_alternatives, related_information['target'] = self.__relative_concession__()

        else:
            raise ValueError("Некорректный метод оптимизации")
        
        related_information['optimal_alternatives'] = optimal_alternatives

        return optimal_alternatives, related_information
