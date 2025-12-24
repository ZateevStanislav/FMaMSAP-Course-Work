import pandas as pd
import numpy as np
from scipy.optimize import fsolve
from scipy import integrate

class FuzzyLogic:
    def __init__(self, data):
        self.task_type = data['task_type']

        if self.task_type == 'Принятие решения в условиях неаддитивности критериев':
            self.weights = data['weights']
            self.belonging_data = data['table_data']

        elif self.task_type == 'Принятие решения в условиях аддитивности критериев':
            self.evaluation_method = data['evaluation_method']

            if self.evaluation_method == 'Нечеткие числа':
                self.weights = data['weights']
                self.belonging_data = data['table_data']

            elif self.evaluation_method == 'Функции принадлежности':
                self.defuzzification_method = data['defuzzification_method']
                self.compliance = data['membership_functions']['compliance']
                self.importance = data['membership_functions']['importance']
                self.weights = data['criteria_weights']
                self.belonging_data = data['alternative_ratings'].T

        elif self.task_type == 'Принятие решения на основе нечетких систем':
            self.membership_data = data['membership_data']
            self.compliance = data['compliance_characteristics']
            self.rules = data['rules']

    def calculate(self):
        if self.task_type == 'Принятие решения в условиях неаддитивности критериев':
            return self.__nonadditive__()
        elif self.task_type == 'Принятие решения в условиях аддитивности критериев':
            return self.__additive__()
        elif self.task_type == 'Принятие решения на основе нечетких систем':
            return self.__fuzzy_systems__()

        return 

    def __nonadditive__(self):
        weights = {criterion: 1 for criterion in self.belonging_data.index} if self.weights is None else self.weights
        
        weighted_data = self.belonging_data.pow(pd.Series(weights), axis=0)
        data_with_belonging = weighted_data.copy()
        data_with_belonging.loc['Худший показатель', :] = [weighted_data[alternative].min() for alternative in weighted_data.columns]
        optimal_alternatives = data_with_belonging.columns[data_with_belonging.loc['Худший показатель'] == data_with_belonging.loc['Худший показатель'].max()].tolist()
        
        dump = {
            'data_with_belonging': data_with_belonging,
            'optimal_alternatives': optimal_alternatives
        }

        return dump

    def __additive__(self):
        if self.evaluation_method == 'Нечеткие числа':
            weights = {criterion: 1 for criterion in self.belonging_data.index} if self.weights is None else self.weights

            weighted_data = self.belonging_data.mul(pd.Series(weights), axis=0)
        
            data_with_belonging = weighted_data.copy()
            data_with_belonging.loc['Усредненный показатель', :] = [weighted_data[alternative].sum() / sum(weights.values()) for alternative in weighted_data.columns]
            optimal_alternatives = data_with_belonging.columns[data_with_belonging.loc['Усредненный показатель'] == data_with_belonging.loc['Усредненный показатель'].max()].tolist()
        
            dump = {
                'data_with_belonging': data_with_belonging,
                'optimal_alternatives': optimal_alternatives
            }

            return dump
        
        else:
            alternatives = pd.DataFrame({
                alternative: sum(self.compliance[self.belonging_data[alternative].loc[criterion]] * self.importance[self.weights.loc[criterion]]
                                 for criterion in self.belonging_data.index)
                for alternative in self.belonging_data.columns
            })
            
            if self.defuzzification_method == 'Метод максимума':
                defazzified_data = self.__max_method__(alternatives)
            elif self.defuzzification_method == 'Метод центра тяжести':
                defazzified_data = self.__centre_gravity_method__(alternatives)
            elif self.defuzzification_method == 'Метод центра площади':
                defazzified_data = self.__square_centre_method__(alternatives)
            
            optimal_alternatives = defazzified_data.columns[defazzified_data.loc['Показатель'] == defazzified_data.loc['Показатель'].max()].tolist()

            dump = {
                'defazzified_data': defazzified_data,
                'optimal_alternatives': optimal_alternatives
            }

            return dump

    def __max_method__(self, matrix):
        matrix.loc['Показатель', :] = [matrix[alternative].loc[self.compliance.index[1]] for alternative in matrix.columns]
        return matrix
    
    def __get_gravity_centre__(self, triangle):
        start = self.compliance.index[0]
        peak = self.compliance.index[1]
        end = self.compliance.index[2]
        
        left_weighted_square = (2 * triangle.loc[peak] ** 2 - triangle.loc[peak] * triangle.loc[start] - triangle.loc[start] ** 2) / 6
        right_weighted_square = (triangle.loc[end] ** 2 + triangle.loc[end] * triangle.loc[peak] - 2 * triangle.loc[peak] ** 2) / 6
        left_square = (triangle.loc[peak] - triangle.loc[start]) / 2
        right_square = (triangle.loc[end] - triangle.loc[peak]) / 2

        return (left_weighted_square + right_weighted_square) / (left_square + right_square)

    def __centre_gravity_method__(self, matrix):
        matrix.loc['Показатель', :] = [self.__get_gravity_centre__(matrix[alternative]) for alternative in matrix.columns]
        return matrix
    
    def __get_square_centre__(self, triangle):
        start = self.compliance.index[0]
        peak = self.compliance.index[1]
        end = self.compliance.index[2]

        left_weighted_square = (2 * triangle.loc[peak] ** 2 - triangle.loc[peak] * triangle.loc[start] - triangle.loc[start] ** 2) / 6
        right_weighted_square = (triangle.loc[end] ** 2 + triangle.loc[end] * triangle.loc[peak] - 2 * triangle.loc[peak] ** 2) / 6
        weighted_square = (left_weighted_square + right_weighted_square)

        if left_weighted_square >= weighted_square * 0.5:
            return fsolve(lambda x: 2 * x ** 3 - 3 * triangle.loc[start] * x ** 2 + triangle.loc[start] ** 3 - 3 * (triangle.loc[peak] - triangle.loc[start]) * weighted_square, 1.0)[0]
        else:
            return fsolve(lambda x: 2 * x ** 3 - 3 * triangle.loc[end] * x ** 2 + triangle.loc[end] ** 3 - 3 * (triangle.loc[end] - triangle.loc[peak]) * weighted_square, 1.0)[0]
    
    def __square_centre_method__(self, matrix):
        matrix.loc['Показатель', :] = [self.__get_square_centre__(matrix[alternative]) for alternative in matrix.columns]
        return matrix

    def __fuzzy_systems__(self):
        start = self.compliance.index[0]
        peak = self.compliance.index[1]
        end = self.compliance.index[2]

        compliances = self.compliance.columns
        criterions = self.membership_data.columns
        alternatives = self.membership_data.index
        compliance_functions = {
            compliance: lambda x, comp=compliance: (
                1 if x <= self.compliance[comp].loc[peak] and x >= self.compliance[comp].loc[start] and self.compliance[comp].loc[peak] == self.compliance[comp].loc[start] else
                (x - self.compliance[comp].loc[start]) / (self.compliance[comp].loc[peak] - self.compliance[comp].loc[start]) if x <= self.compliance[comp].loc[peak] and x >= self.compliance[comp].loc[start] else
                1 if x <= self.compliance[comp].loc[end] and x >= self.compliance[comp].loc[peak] and self.compliance[comp].loc[end] == self.compliance[comp].loc[peak] else
                (self.compliance[comp].loc[end] - x) / (self.compliance[comp].loc[end] - self.compliance[comp].loc[peak]) if x <= self.compliance[comp].loc[end] and x >= self.compliance[comp].loc[peak] else 0
            )
            for compliance in compliances
        }

        alter_values = {}
        for alternative in alternatives:
            rules_values = {
                f'rule{i}': [
                    self.rules['result'].loc[i], 
                    min(compliance_functions[self.rules[criterion].loc[i]](self.membership_data[criterion].loc[alternative]) for criterion in criterions)
                ] for i in self.rules.index
                if min(compliance_functions[self.rules[criterion].loc[i]](self.membership_data[criterion].loc[alternative]) for criterion in criterions) > 0
            }
            result_function = lambda x: max(compliance_functions[value[0]](x) * value[1] for _, value in rules_values.items())
            
            weighted_integrate_value, _ = integrate.quad(lambda x: x * result_function(x), 0, 1)
            integrate_value, _ = integrate.quad(result_function, 0, 1)

            alter_values[alternative] = [weighted_integrate_value / integrate_value]

        data_with_measure = pd.DataFrame(alter_values, index=['Показатель'])

        dump = {
            'data_with_measure': data_with_measure,
            'optimal_alternatives': data_with_measure.columns[data_with_measure.loc['Показатель'] == data_with_measure.loc['Показатель'].max()].tolist()
        }

        return dump



