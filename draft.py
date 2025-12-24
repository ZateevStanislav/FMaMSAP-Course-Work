from copy import copy
import numpy as np
import pandas as pd
from math import isclose, log
import itertools
import pickle
import ast

states = pd.DataFrame({
    's1': [-2.59],
    's2': [24.93],
    's3': [23.55]
}, index=['value'])
states.to_csv('states.csv')

md = pd.DataFrame({
    'Критерий1': [0.3],
    'Критерий2': [0.9]
}, index=['Альтернатива'])

comp = pd.DataFrame({
    'Плохая': [0, 0, 0.5],
    'Удовлетворительная': [0, 0.5, 1],
    'Хорошая': [0.5, 1, 1]
}, index=['Старт', 'Пик', 'Конец'])

rul = pd.DataFrame({
    'Критерий1': ['Плохая', 'Удовлетворительная', 'Плохая', 'Удовлетворительная', 'Хорошая'],
    'Критерий2': ['Плохая', 'Удовлетворительная', 'Удовлетворительная', 'Хорошая', 'Хорошая'],
    'result': ['Плохая', 'Удовлетворительная', 'Удовлетворительная', 'Хорошая', 'Хорошая']
})


from MethodsRealization.FuzzyLogic import FuzzyLogic
fuzzyw1 = {'C1': 0.2, 'C2': 0.18, 'C3': 0.17, 'C4': 0.16, 'C5': 0.15, 'C6': 0.14}
fuzzym1 = pd.DataFrame({
    'a1': [0.9, 0.8, 0.7, 0.9, 0.9, 0.9],
    'a2': [0.9, 0.9, 0.9, 0.8, 0.9, 0.4],
    'a3': [0.6, 0.5, 0.8, 0.5, 0.4, 0.8],
    'a4': [0.8, 0.7, 0.5, 0.6, 0.7, 0.7],
    'a5': [0.5, 0.6, 0.3, 0.5, 0.6, 0.7]
}, index=['C1', 'C2', 'C3', 'C4', 'C5', 'C6'])

#FL = FuzzyLogic({
#    'task_type': 'Принятие решения в условиях аддитивности критериев',
#    'evaluation_method': 'Нечеткие числа',
#    'weights': fuzzyw1,
#    'table_data': fuzzym1
#})

fuzzyw2 = pd.DataFrame({'ok': [0.6, 0.9, 1], 'nok': [0.3, 0.6, 0.8]}, index=['s', 'p', 'e'])
fuzzyc2 = pd.Series({'Z1': 'ok', 'Z2': 'nok'})
fuzzye2 = pd.DataFrame({'ot': [0.7, 1, 1], 'hor': [0.4, 0.7, 1], 'pl': [0, 0, 0.5]}, index=['s', 'p', 'e'])
fuzzym2 = pd.DataFrame({
    'A1': ['ot', 'pl'],
    'A2': ['hor', 'hor']
}, index=['Z1', 'Z2'])


fuzzyw3 = pd.DataFrame({'ok': [0.8, 1, 1], 'nok': [0, 0.2, 0.4]}, index=['s', 'p', 'e'])
fuzzyc3 = pd.Series({'Z1': 'ok', 'Z2': 'nok'})
fuzzye3 = pd.DataFrame({'hor': [0.6, 0.8, 1], 'ud': [0.4, 0.6, 0.8]}, index=['s', 'p', 'e'])
fuzzym3 = pd.DataFrame({
    'A1': ['hor', 'ud'],
    'A2': ['ud', 'hor']
}, index=['Z1', 'Z2'])

"""
FL = FuzzyLogic({
    'task_type': 'Принятие решения в условиях аддитивности критериев',
    'evaluation_method': 'Функции принадлежности',
    'criteria_weights': fuzzyc3,
    'alternative_ratings': fuzzym3.T,
    'membership_functions': {
        'compliance': fuzzye3,
        'importance': fuzzyw3
    },
    'defuzzification_method': 'Метод центра площади'
})
"""
md = pd.DataFrame({
    'Критерий1': [0.3],
    'Критерий2': [0.9]
}, index=['Альтернатива'])

comp = pd.DataFrame({
    'Плохая': [0, 0, 0.5],
    'Удовлетворительная': [0, 0.5, 1],
    'Хорошая': [0.5, 1, 1]
}, index=['Старт', 'Пик', 'Конец'])

rul = pd.DataFrame({
    'Критерий1': ['Плохая', 'Удовлетворительная', 'Плохая', 'Удовлетворительная', 'Хорошая'],
    'Критерий2': ['Плохая', 'Удовлетворительная', 'Удовлетворительная', 'Хорошая', 'Хорошая'],
    'result': ['Плохая', 'Удовлетворительная', 'Удовлетворительная', 'Хорошая', 'Хорошая']
})

def function_creator(x, compliance):
    if x <= comp[compliance].loc[peak] and x >= comp[compliance].loc[start]:
        if comp[compliance].loc[peak] == comp[compliance].loc[start]:
            return 1
        else:
            return (x - comp[compliance].loc[start]) / (comp[compliance].loc[peak] - comp[compliance].loc[start])
    elif x <= comp[compliance].loc[end] and x >= comp[compliance].loc[peak]:
        if comp[compliance].loc[end] == comp[compliance].loc[start]:
            return 1
        else:
            return (comp[compliance].loc[end] - x) / (comp[compliance].loc[end] - comp[compliance].loc[peak])
    else:
        return 0
    
start = comp.index[0]
peak = comp.index[1]
end = comp.index[2]
compliance_functions = {compliance: lambda x, com=compliance: function_creator(x, compliance=com) for compliance in comp.columns}

#print(compliance_functions['Плохая'](x=0))
#print(function_creator(0.5, 'Плохая'))
#print(0 <= comp['Плохая'].loc[peak])
#print(0 >= comp['Плохая'].loc[start])
#print(0 <= comp['Плохая'].loc[peak] and 0 >= comp['Плохая'].loc[start] and comp['Плохая'].loc[peak] == comp['Плохая'].loc[start])
#print((0 - comp['Плохая'].loc[start]) / (comp['Плохая'].loc[peak] - comp['Плохая'].loc[start]))
#print(0/0)
FL = FuzzyLogic({
    'task_type': 'Принятие решения на основе нечетких систем',
    'membership_data': md,
    'compliance_characteristics': comp,
    'rules': rul
})
#for rule in rul.index:
#    print(f"\tЕСЛИ {' И '.join(f'{criterion} имеет оценку {rul[criterion].loc[rule]}' for criterion in rul.columns if criterion != 'result')} ТО Общая оценка {rul['result'].loc[rule]}; \n")
#print(FL.calculate())
#df = pd.read_csv('res_big_conv6.csv')
#print(df[['Size', 'Score', 'Depth']])
'''
from MethodsRealization.UncertaintyRemoving import UncertaintyRemoving

data = pd.DataFrame({
    '': ['C1', 'C2', 'C3', 'C4', 'C5', 'C6'],
    'a1': [0.9, 0.8, 0.7, 0.9, 0.9, 0.9],
    'a2': [0.9, 0.9, 0.9, 0.8, 0.9, 0.4],
    'a3': [0.6, 0.5, 0.8, 0.5, 0.4, 0.8],
    'a4': [0.8, 0.7, 0.5, 0.6, 0.7, 0.7],
    'a5': [0.5, 0.6, 0.3, 0.5, 0.6, 0.7]
})
data = data.set_index('')

#print(data)
#print(data * 0.5)
#print(data.max() + data.min())
data.to_csv("nonadditive.csv")
'''
'''
profit_matrix = pd.DataFrame({
    '': ['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10'],
    's1': [50, 40, 80, 60, 70, 50, 90, 30, 100, 70],
    's2': [50, 30, 80, 30, 70, 40, 90, 50, 90, 60],
    's3': [40, 80, 70, 40, 60, 50, 60, 40, 50, 90],
    's4': [50, 40, 70, 50, 80, 60, 60, 50, 60, 60],
    's5': [30, 30, 50, 40, 40, 30, 80, 30, 70, 40],
    's6': [30, 40, 50, 60, 60, 30, 80, 40, 80, 70],
    's7': [60, 50, 70, 30, 50, 50, 70, 60, 90, 50],
    's8': [70, 50, 80, 30, 60, 50, 90, 60, 90, 60]
})
profit_matrix = profit_matrix.set_index('').T
print(profit_matrix)
print(profit_matrix.index)
print(100 - profit_matrix.loc['s1'])
'''
'''
data = {
    'ex1': profit_matrix
}

states_probability  = {'s1': 0.1, 's2': 0.05, 's3': 0.15, 's4': 0.17, 's5': 0.15, 's6': 0.13, 's7': 0.2, 's8': 0.05}

uncertainty_settings = {
    'prior_information': {
        'ex1': 'Ситуация 3: Риск'
    },
    'probabilities': {
        'ex1': states_probability
    }
}

uncertainty_methods = {
    'ex1': {
        'method_name': 'Универсальный критерий', 
        'situation_type': 'Ситуация 3: Риск', 
        'parameters': {'trust_level': 0.7, 'additional_param': 0.6, 'risk_attitude':0.3}
    }
}


un = UncertaintyRemoving(certain_data=None, uncertain_data=data, uncertainty_settings=uncertainty_settings, uncertainty_methods=uncertainty_methods, normalization_methods=None, direcion_settings=None)
un.get_processed_data()
'''
#data = pd.DataFrame({
#    f"alt{i}": [0.3*i + 0.1*j for j in range(3)] for i in range(3)
#})

#print(data)
#print(data * 0.5)
#print(data.max() + data.min())
#data.to_csv("degrees.csv")
#data2 = pd.DataFrame({
#    f"alt{i}": [0.1 * i] for i in range(1, 8)
#})

#print(data.sub(data2.loc[0]).pow(2))
#print(data)
"""
data = pd.read_csv('Data/Task1/exp1.csv').drop('Unnamed: 0', axis=1)
print(data)
mr = 12
S = ((1 + 2.5 + 4.5 - mr) ** 2 + (2.5 + 2.5 + 4.5 - mr) ** 2 
     + (7 + 4.5 + 6.5 - mr) ** 2 + (2.5 + 6 + 4.5 - mr) ** 2
     + (6 + 7 + 6.5 - mr) ** 2 + (1 + 2.5 + 2.5 - mr) ** 2 
     + (1 + 4.5 + 4.5 - mr) ** 2)
print(S)
W = 12 * S / 9 / (7**3 - 7)
print(W)

def __convert_to_ranks__(list_of_estimates):
    rel_values = copy(list_of_estimates)
    ranks = np.zeros_like(list_of_estimates)
    ranks = ranks.astype(float)
    current_rank = 0
    while len(rel_values) > 0:
        print(current_rank)
        print(rel_values)
        max_value = max(rel_values)
        maxes = [i for i, est in enumerate(list_of_estimates) if est == max_value]
        print(maxes)
        rank = sum(range(current_rank+1, current_rank+1+len(maxes))) / len(maxes)
        print(rank)
        for i in maxes:
            ranks[i] = rank
        print(ranks)

        current_rank += len(maxes)
        rel_values = [j for j in rel_values if j < max_value]
        print('--------')

    return ranks
print([] is None)

print(__convert_to_ranks__([10,8,6,9,7,9,8]))
"""


        

'''
from CriteriaProcessing import CriteriaProcessing

data = {
    'ex1': pd.DataFrame({'col1': [1, 2, 1], 'col2': [5, 3, 4], 'col3': [1, 5, 2], 'col4': [1, 3, 4], 'rows': ['row1', 'row2', 'row3']}).set_index('rows'),
    'ex2': pd.DataFrame({'col1': [5, 6, 6], 'col2': [7, 7, 8], 'col3': [1, 2, 3], 'col4': [9, 6, 5], 'rows': ['row1', 'row2', 'row3']}).set_index('rows')
}

num_data = {
    'Alternatives': ['col1', 'col2', 'col3', 'col4'],
    'num1': [12, 34, 56, 43],
    'num2': [100,100,100,0]#[14, 36, 57, 83]
}
num_data = pd.DataFrame(num_data).set_index('Alternatives').T

direction_settings = {
    'direction_changes': {
        'num1': 'negation',
        'num2': 'savige'
    },
    'savige_max_values': {
        'num2': 100
    }
}

normalization_methods = [
    "Нет нормализации",
    "Сравнительная нормализация",
    "Относительная нормализация",
    "Естественная нормализация",
    "Полная нормализация"
]

criteria_normalization_methods = {
    'ex1': normalization_methods[4],
    'ex2': normalization_methods[4],
    'num1': normalization_methods[4],
    'num2': normalization_methods[4]
}

expert_methods = {
    'ex1': "Усреднение экспертных оценок",
    'ex2': "Обобщенная ранжировка"
}

num_data_2 = {
    'Alternatives': ['col1', 'col2', 'col3', 'col4'],
    'num1': [14, 56, 56, 43],
    'num2': [14, 33, 57, 83]
}
num_data_2 = pd.DataFrame(num_data_2).set_index('Alternatives').T
c = CriteriaProcessing(numeric_data=num_data, expert_data=data, expert_methods=expert_methods,normalization_methods=criteria_normalization_methods, direcion_settings=direction_settings)
table, info = c.get_processed_data()
print(table)
print(info)
print(table['col1'].loc['num2'])
'''


'''
from DecisionMaking import DecisionMaking

df = pd.DataFrame({
        'A1': [9, 5],
        'A2': [5, 7],
        'A3': [6, 4],
        'A4': [7, 6],
        'A5': [4, 6],
        'A6': [2, 8],
        'A7': [2, 5],
        'A8': [5, 7],
        'A9': [3, 7],
        '': ['z1', 'z2']
    })
df = df.set_index('')

weights = {'z1': 0.3, 'z2': 0.7}

parameters = {
    'idp': {'z1': 10, 'z2': 10},
    'aidp': {'z1': 0, 'z2': 0},
    'metric': None,
    'sigma': pd.DataFrame({
            '': ['z1', 'z2'],
            'z1': [0, 1.5],
            'z2': [1.5, 0]
        }).set_index(''),
    'main_thresholds': {'z1': np.mean(df.loc['z1'])},
    'quasi_equal_thresholds': {'z1': 2.2, 'z2': 1.2}
}

DM = DecisionMaking(df, weights)
res, info = DM.calculate(parameters)
print(res)
print(info['result'])
print(info['idp']['data_with_distances_to_ideal_point'])
print(info['aidp']['data_with_distances_to_anti_ideal_point'])
print(info['pareto']['result_data'])
print(info['equal']['weighted_values'])
print(info['qequal']['weighted_values'])
print(info['absolute']['data_with_common_criterion'])
print(info['relative']['data_with_common_criterion'])
print(info['main']['relevent_alternatives_data'])
print(info['lex_equal']['criterions_history'])
print(info['lex_qequal']['criterions_history'])

'''