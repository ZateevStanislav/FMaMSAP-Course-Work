import pandas as pd
import numpy as np
from math import log
from copy import copy


class UncertaintyRemoving: 
    def  __init__(self, certain_data, uncertain_data, uncertainty_settings, uncertainty_methods, normalization_methods, direcion_settings):
        self.uncertain_data = uncertain_data
        self.certain_data = certain_data
        self.uncertainty_settings = uncertainty_settings
        self.uncertainty_methods = uncertainty_methods
        self.direcion_settings = direcion_settings
        self.normalization_methods = normalization_methods

    """Смена направления"""
    def __direction_changing__(self):
        direction_changes = self.direcion_settings['direction_changes']
        savige_max_value = self.direcion_settings['savige_max_values']

        for criterion in direction_changes:
            if direction_changes[criterion] == 'negation':
                if criterion in self.uncertain_data:
                    self.uncertain_data[criterion] = (-1) * self.uncertain_data[criterion]
                else:
                    self.certain_data.loc[criterion] = (-1) * self.certain_data.loc[criterion]
            elif direction_changes[criterion] == 'savige':
                if criterion in self.uncertain_data:
                    self.uncertain_data[criterion] = savige_max_value[criterion] - self.uncertain_data[criterion]
                else:
                    self.certain_data.loc[criterion] = savige_max_value[criterion] - self.certain_data.loc[criterion]
            else:
                raise ValueError("Некорректный способ смены направления")

    """Нормализация критериев"""    
    def __relative__(self, data):
        if isinstance(data, pd.DataFrame):
            value = (abs(data.max().max()) if data.max().max() > 0.0  else abs(data.min().min()) if data.max().max() < 0.0 
                        else abs(data.min().min()) if data.min().min() != 0.0 else data.max().max() + 10**(-6))
        else: 
            value = (abs(data.max()) if data.max() > 0.0  else abs(data.min()) if data.max() < 0.0 
                        else abs(data.min()) if data.min() != 0.0 else data.max() + 10**(-6))
        return data.div(value)
    
    def __comparative__(self, data):
        if isinstance(data, pd.DataFrame):
            return data.sub(data.min().min())
        else:
            return data.sub(data.min())
    
    def __natural__(self, data):
        if isinstance(data, pd.DataFrame):
            value = data.max().max() - data.min().min() if data.max().max() - data.min().min() != 0 else data.max().max() if data.max().max() != 0 else data.max().max() + 10**(-6)
        else:
            value = data.max() - data.min() if data.max() - data.min() != 0 else data.max() if data.max() != 0 else data.max() + 10**(-6)
        return data.div(value)

    def __full__(self, data):
        if isinstance(data, pd.DataFrame):
            min_value = data.min().min()
            value = data.max().max() - data.min().min() if data.max().max() - data.min().min() != 0 else data.max().max() if data.max().max() != 0 else data.max().max() + 10**(-6)
        else:
            min_value = data.min()
            value = data.max() - data.min() if data.max() - data.min() != 0 else data.max() if data.max() != 0 else data.max() + 10**(-6)
        return data.sub(min_value).div(value)

    def __uncertain_criterion_normalize__(self):
        for criterion in self.uncertain_data:
            if self.normalization_methods[criterion] == 'Относительная нормализация':
                self.uncertain_data[criterion] = self.__relative__(self.uncertain_data[criterion])
            elif self.normalization_methods[criterion] == 'Сравнительная нормализация':                
                self.uncertain_data[criterion] = self.__comparative__(self.uncertain_data[criterion])
            elif self.normalization_methods[criterion] == 'Естественная нормализация':
                self.uncertain_data[criterion] = self.__natural__(self.uncertain_data[criterion])
            elif self.normalization_methods[criterion] == 'Полная нормализация':
                self.uncertain_data[criterion] = self.__full__(self.uncertain_data[criterion])
            elif self.normalization_methods[criterion] == "Нет нормализации":
                pass
            else:
                raise ValueError("Некорректный метод нормализации")
            
            threshold_value = self.uncertain_data[criterion].max().max() * 10 ** (-4)
            self.uncertain_data[criterion] = self.uncertain_data[criterion].mask(self.uncertain_data[criterion].abs() <= threshold_value, threshold_value)
            print(self.uncertain_data[criterion])
    
    def __certain_criterion_normalize__(self):
        for criterion in self.certain_data.index:
            if self.normalization_methods[criterion] == 'Относительная нормализация':
                self.certain_data.loc[criterion] = self.__relative__(self.certain_data.loc[criterion])
            elif self.normalization_methods[criterion] == 'Сравнительная нормализация':                
                self.certain_data.loc[criterion] = self.__comparative__(self.certain_data.loc[criterion])
            elif self.normalization_methods[criterion] == 'Естественная нормализация':
                self.certain_data.loc[criterion] = self.__natural__(self.certain_data.loc[criterion])
            elif self.normalization_methods[criterion] == 'Полная нормализация':
                self.certain_data.loc[criterion] = self.__full__(self.certain_data.loc[criterion])
            elif self.normalization_methods[criterion] == "Нет нормализации":
                pass
            else:
                raise ValueError("Некорректный метод нормализации")
            
        self.certain_data = self.certain_data.apply(lambda row: row.mask(row.abs() <= row.max() * 10**(-4), row.max() * 10**(-4)), axis=1)
        #print(self.certain_data)

    def __normalize__(self):
        self.__uncertain_criterion_normalize__()
        self.__certain_criterion_normalize__()

    """Снятие неопределенности"""
    def __BayesLaplace__(self, criterion, probabilities):
        result = pd.DataFrame(self.uncertain_data[criterion].mul(pd.Series(probabilities), axis=0).sum()).T
        result.index = [criterion]

        return result, {'result': result}

    def __MSE__(self, criterion, probabilities, value_type):
        
        weighted_data = pd.DataFrame(self.uncertain_data[criterion].mul(pd.Series(probabilities), axis=0).sum()).T
        weighted_data.index = [criterion]

        differences = self.uncertain_data[criterion].sub(weighted_data.iloc[criterion]).pow(2)

        result = pd.DataFrame(differences.mul(pd.Series(probabilities), axis=0).sum()).T.pow(0.5)
        result.index = [criterion]

        dump = {
            'weighted_data': weighted_data,
            'differences': differences, 
            'result': result
        }

        return result, dump

    def __MSE_mod__(self, criterion, probabilities, value_type):
        
        weighted_data = pd.DataFrame(self.uncertain_data[criterion].mul(pd.Series(probabilities), axis=0).sum()).T
        weighted_data.index = [criterion]

        differences = self.uncertain_data[criterion].sub(weighted_data.max(axis=1).loc[criterion] if value_type == 'непрерывная' else weighted_data.mean(axis=1).loc[criterion]).pow(2)

        result = pd.DataFrame(differences.mul(pd.Series(probabilities), axis=0).sum()).T.pow(0.5)
        result = result.max().max() - result
        result.index = [criterion]

        dump = {
            'value_type': value_type,
            'weighted_data': weighted_data,
            'differences': differences, 
            'result': result
        }

        return result, dump

    def __probability_maximizing__(self, criterion, probabilities, threshold):

        states_probability_with_condition = (self.uncertain_data[criterion] >= threshold).mul(pd.Series(probabilities), axis=0)
        result = pd.DataFrame(states_probability_with_condition.sum()).T
        result.index = [criterion]
        
        dump = {
            'threshold': threshold,
            'states_probability_with_condition': states_probability_with_condition,
            'result': result
        }

        return result, dump

    def __modal__(self, criterion, probabilities):
        best_states = [state for state, value in probabilities.items() if value == max(probabilities.values())]

        result = pd.DataFrame(self.uncertain_data[criterion].loc[best_states].mean()).T
        result.index = [criterion]

        dump = {
            'best_states': best_states,
            'result': result
        }

        return result, dump

    def __entropy__(self, criterion, probabilities):
        condition = (self.uncertain_data[criterion] > 0).all().all()
        max_value = self.uncertain_data[criterion].max().max() + self.uncertain_data[criterion].max().max() * 10 ** (-4)
        matrix = self.uncertain_data[criterion] if condition else self.uncertain_data[criterion].apply(lambda x: max_value - x)

        weighted_matrix = matrix.mul(pd.Series(probabilities), axis=0).div(matrix.mul(pd.Series(probabilities), axis=0).sum())
        result = pd.DataFrame((weighted_matrix * weighted_matrix.apply(lambda x: x.apply(lambda y: log(y,2)))).mul(-1).sum()).T
        result = result.max().max() - result
        result.index = [criterion]

        dump = {
            'condition': condition,
            'max_value': max_value,
            'fixed_data': matrix,
            'weighted_matrix': weighted_matrix,
            'result': result
        }
        return result, dump

    def __Hermeyer__(self, criterion, probabilities):
        condition = (self.uncertain_data[criterion] < 0).all().all()
        max_value = self.uncertain_data[criterion].max().max() + self.uncertain_data[criterion].max().max() * 10 ** (-4)
        matrix = self.uncertain_data[criterion] if condition else self.uncertain_data[criterion].apply(lambda x: x - max_value)
        
        result = pd.DataFrame((matrix).mul(pd.Series(probabilities), axis=0).min()).T
        result.index = [criterion]

        dump = {
            'condition': condition,
            'max_value': max_value,
            'fixed_data': matrix,
            'result': result
        }
        return result, dump

    def __Vald__(self, criterion): 
        result = pd.DataFrame(self.uncertain_data[criterion].min()).T
        result.index = [criterion]

        return result, {'result': result}

    def __MinMaxSevidzh__(self, criterion):
        penalty_matrix = self.uncertain_data[criterion].apply(lambda x: self.uncertain_data[criterion].max(axis=1) - x)

        result = pd.DataFrame(penalty_matrix.max()).T
        result = result.max().max() - result
        result.index = [criterion]

        dump = {
            'penalty_matrix': penalty_matrix,
            'result': result
        }

        return result, dump

    def __Gurvic__(self, criterion, probabilities, risk_attitude):
        result = pd.DataFrame((1 - risk_attitude) * self.uncertain_data[criterion].max() + risk_attitude * self.uncertain_data[criterion].min()).T
        result.index = [criterion]

        return result, {'result': result, 'risk_attitude': risk_attitude}

    def __HodgesLehman__(self, criterion, probabilities, hl_parameter):
        weighted_data = pd.DataFrame(self.uncertain_data[criterion].mul(pd.Series(probabilities), axis=0).sum()).T
        min_data = pd.DataFrame(self.uncertain_data[criterion].min()).T

        result = hl_parameter * weighted_data + (1 - hl_parameter) * min_data
        result.index = [criterion]

        dump = {
            'hl_parameter': hl_parameter,
            'weighted_data': weighted_data,
            'min_data': min_data,
            'result': result
        }

        return result, dump

    def __additional_criterion__(self, criterion, probabilities, additional_param):
        weighted_data = pd.DataFrame(self.uncertain_data[criterion].mul(pd.Series(probabilities), axis=0).sum()).T
        weighted_data.index = [criterion]
        
        sigma_data = pd.DataFrame(self.uncertain_data[criterion].sub(weighted_data.iloc[0]).pow(2).mul(pd.Series(probabilities), axis=0).sum()).T.pow(0.5)
        #sigma_data = self.__MSE_mod__(criterion, probabilities, 'дискретная')[0]
        sigma_data.index = [criterion]

        result = (1 - additional_param) * weighted_data - additional_param * sigma_data
        result.index = [criterion]

        dump = {
            'additional_param': additional_param,
            'weighted_data': weighted_data,
            'sigma_data': sigma_data,
            'result': result
        }

        return result, dump

    def __universal_criterion__(self, criterion, probabilities, additional_param, risk_attitude, trust_level):
        gurcvitz_criteria, dump_gur = self.__Gurvic__(criterion, probabilities, risk_attitude)

        if probabilities is None:
            dump_gur['trust_level'] = trust_level
            dump_gur['additional_param'] = additional_param
            return gurcvitz_criteria, dump_gur
        
        additional_criteria, dump_add = self.__additional_criterion__(criterion, probabilities, additional_param)
        result = (1 - trust_level) * additional_criteria + trust_level * gurcvitz_criteria
        result.index = [criterion]

        dump = {
            'additional_param': additional_param, 
            'risk_attitude': risk_attitude,
            'trust_level': trust_level,
            'gurcvitz_criteria': gurcvitz_criteria,
            'weighted_data': dump_add['weighted_data'],
            'sigma_data': dump_add['sigma_data'],
            'additional_criteria': additional_criteria,
            'result': result
        }

        return result, dump
    
    def __get_parameters__(self):
        parameters = {
            criterion: {
                'criterion': criterion,
                **self.uncertainty_methods[criterion]['parameters']
            }
            for criterion in self.uncertain_data
        }

        for criterion in self.uncertain_data:
            situation = self.uncertainty_methods[criterion]['situation_type']
            if situation in ['Ситуация 1: Полная определенность', 'Ситуация 3: Риск']:
                parameters[criterion]['probabilities'] = self.uncertainty_settings['probabilities'][criterion]
            elif self.uncertainty_methods[criterion]['method_name'] == 'Универсальный критерий':                
                parameters[criterion]['probabilities'] = None
            if self.uncertainty_methods[criterion]['method_name'] == 'Универсальный критерий':
                if situation == 'Ситуация 1: Полная определенность':
                    parameters[criterion]['trust_level'] = 0.0
                    parameters[criterion]['risk_attitude'] = 0.0
                if situation == 'Ситуация 2: Неопределенность':
                    parameters[criterion]['trust_level'] = 1.0
                    parameters[criterion]['additional_param'] = 0.0

        return parameters

    def __uncertainty_removing__(self):
        related_information = {}
        result_string = {}

        parameters = self.__get_parameters__()
        #print(parameters)

        for criterion in self.uncertain_data:
            if self.uncertainty_settings['prior_information'][criterion] == 'Ситуация 1: Полная определенность':
                if self.uncertainty_methods[criterion]['method_name'] == 'Критерий Байеса-Лапласа':
                    result_string[criterion], related_information[criterion] = self.__BayesLaplace__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Критерий минимальной среднеквадратичной ошибки':
                    result_string[criterion], related_information[criterion] = self.__MSE_mod__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Критерий максимальной вероятности':
                    result_string[criterion], related_information[criterion] = self.__probability_maximizing__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Модальный критерий':
                    result_string[criterion], related_information[criterion] = self.__modal__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Критерий минимума энтропии':
                    result_string[criterion], related_information[criterion] = self.__entropy__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Критерий Гермейера':
                    result_string[criterion], related_information[criterion] = self.__Hermeyer__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Универсальный критерий':
                    result_string[criterion], related_information[criterion] = self.__universal_criterion__(**parameters[criterion])
                else:
                    raise ValueError("Некорректный метод снятия неопределенности")
            elif self.uncertainty_settings['prior_information'][criterion] == 'Ситуация 2: Неопределенность':
                if self.uncertainty_methods[criterion]['method_name'] == 'Критерий Вальда':
                    result_string[criterion], related_information[criterion] = self.__Vald__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Критерий минимаксного Сэвиджа':
                    result_string[criterion], related_information[criterion] = self.__MinMaxSevidzh__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Универсальный критерий':
                    result_string[criterion], related_information[criterion] = self.__universal_criterion__(**parameters[criterion])
                else:
                    raise ValueError("Некорректный метод снятия неопределенности")
            elif self.uncertainty_settings['prior_information'][criterion] == 'Ситуация 3: Риск':
                if self.uncertainty_methods[criterion]['method_name'] == 'Критерий Гурвица':
                    result_string[criterion], related_information[criterion] = self.__Gurvic__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Критерий Ходжеса-Лемана':
                    result_string[criterion], related_information[criterion] = self.__HodgesLehman__(**parameters[criterion])
                elif self.uncertainty_methods[criterion]['method_name'] == 'Универсальный критерий':
                    result_string[criterion], related_information[criterion] = self.__universal_criterion__(**parameters[criterion])
                else:
                    raise ValueError("Некорректный метод снятия неопределенности")
            else:
                raise ValueError("Некорректная ситуация априорной информированности")
            
        
        return pd.concat([result_string[criterion] for criterion in result_string]), related_information
    
    """Обработка данных"""
    def get_processed_data(self):
        related_information = {
            "uncertainty_removing": {}
        }

        self.__direction_changing__()
        related_information['direction_changing_result'] = {
            'certain' : copy(self.certain_data),
            'uncertain': copy(self.uncertain_data)
        }

        self.__normalize__()
        related_information['normalization_result'] = {
            'certain' : copy(self.certain_data),
            'uncertain': copy(self.uncertain_data)
        }

        generalized_certain_ratings, related_information["uncertainty_removing"]["data"] = self.__uncertainty_removing__()
        related_information["uncertainty_removing"]["methods"] = self.uncertainty_methods
        
        evaluating_alternatives = pd.concat([self.certain_data, generalized_certain_ratings])
        related_information['result_criterions_values'] = evaluating_alternatives

        return evaluating_alternatives, related_information
