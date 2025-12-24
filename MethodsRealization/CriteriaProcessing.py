import numpy as np
import pandas as pd
from itertools import combinations

class CriteriaProcessing:
    expert_estimates_averaging_default_params = {
        'EK': {'e': 0.001},
        'Ryk': {
            'e': 0.01,
            'e1': 0.001,
            'p': 1,
            'mode': 'mult'
        },
        'Com': {'mode': 'median'}
    }

    def  __init__(self, numeric_data, expert_data, expert_methods, normalization_methods, direcion_settings):
        self.expert_data = expert_data
        self.numeric_data = numeric_data
        self.expert_methods = expert_methods
        self.direcion_settings = direcion_settings
        self.normalization_methods = normalization_methods

    '''Сведение/обобщение экспертных оценок'''
    def __expert_estimates_averaging__(self, criterion):
        alternatives = list(self.expert_data[criterion].columns)

        estimation = {alter: [float(self.expert_data[criterion][alter].mean())] for alter in alternatives}
        estimation['Alternatives'] = [criterion]

        return pd.DataFrame(estimation).set_index('Alternatives'), dict()
        
    def __Evlanov_Kutuzov_expert_estimates_averaging__(self, criterion, e=0.001):
            K_dump = []

            estimation = self.expert_data[criterion]

            experts_number = len(estimation.index)
            alternatives = list(estimation.columns)
            experts = list(estimation.index)

            K = {expert: 1 / experts_number for expert in experts}

            while True:
                K_dump.append(K)
                alters_t = {alter: sum([estimation[alter].loc[expert] * K[expert] for expert in experts]) for alter in alternatives}
                lambda_t = sum([alters_t[alter] * estimation[alter].loc[expert] for alter in alternatives for expert in experts])
                K_t = {expert: sum([alters_t[alter] * estimation[alter].loc[expert] for alter in alternatives]) / lambda_t for expert in experts}

                if all(abs(K[expert] - K_t[expert]) < e for expert in experts):
                    K = K_t
                    break

                K = K_t
            K_dump.append(K)

            result_estimation = {alter: [sum(estimation[alter].loc[expert] * K[expert] for expert in experts)] for alter in alternatives}
            result_estimation['Alternatives'] = [criterion]

            return pd.DataFrame(result_estimation).set_index('Alternatives'), K_dump

    def __Rykov_expert_estimates_averaging__(self, criterion, e=0.01, e1=0.001, p=1, mode='mult'):
            K_dump = []

            estimation = self.expert_data[criterion]

            experts_number = len(estimation.index)
            alternatives = list(estimation.columns)
            experts = list(estimation.index)

            K = {expert: 1 / experts_number for expert in experts}

            while True:
                K_dump.append(K)
                alters_t = {alter: sum([estimation[alter].loc[expert] * K[expert] for expert in experts]) for alter in alternatives}
                delta_K_t = {expert: 1 / (sum([abs(alters_t[alter] - estimation[alter].loc[expert]) ** p for alter in alternatives]) ** (1/p) + e) for expert in experts}
                K_t = {expert: K[expert] + delta_K_t[expert] for expert in experts} if mode == 'add' else {expert: K[expert] * delta_K_t[expert] for expert in experts}
                lambda_t = sum(K_t[expert] for expert in experts)
                K_t = {expert: K_t[expert] / lambda_t for expert in experts}

                if all(abs(K[expert] - K_t[expert]) < e1 for expert in experts):
                    K = K_t
                    break

                K = K_t
            K_dump.append(K)
            
            result_estimation = {alter: sum(estimation[alter].loc[expert] * K[expert] for expert in experts) for alter in alternatives}
            result_estimation['Alternatives'] = [criterion]

            return pd.DataFrame(result_estimation).set_index('Alternatives'), K_dump

    def __get_common_ranking__(self):
        result = {}

        for criterion in self.expert_data:
            temp_result = {}
            estimation = self.expert_data[criterion]

            alternatives = list(estimation.columns)
            experts = list(estimation.index)
            for expert in experts:
                expert_ranking = {
                    alter1:
                    [
                        -1 if estimation[alter1].loc[expert] < estimation[alter2].loc[expert] else 
                        0 if estimation[alter1].loc[expert] == estimation[alter2].loc[expert] else 1
                        for alter2 in alternatives
                    ] for alter1 in alternatives
                }
                expert_ranking['Alternatives'] = alternatives
                temp_result[expert] = pd.DataFrame(expert_ranking).set_index('Alternatives')
        
            result[criterion] = temp_result
        
        return result

    def __common_metric_median__(self, ranking1, ranking2):
        return 0.5 * sum(abs(ranking1[alter1].loc[alter2] - ranking2[alter1].loc[alter2]) for alter1 in ranking1.columns for alter2 in ranking1.index)

    def __common_metric_mean__(self, ranking1, ranking2):
        return 0.5 * sum(abs(ranking1[alter1].loc[alter2] - ranking2[alter1].loc[alter2]) ** 2 for alter1 in ranking1.columns for alter2 in ranking1.index)

    def __choose_pos__(self, array):
        neg_num = (array == -1).sum()
        zero_num = (array == 0).sum()
        pos_num = (array == 1).sum()

        return 0 if (zero_num >= pos_num and neg_num >= pos_num) else 1 if (pos_num > neg_num and pos_num > zero_num) else -1

    def __pairwise_to_ranking__(self, pairwise_matrix, alternatives=None):
        n = pairwise_matrix.shape[0]
        
        # Считаем "силу" каждой альтернативы (сумма сравнений)
        strength = np.zeros(n)
        for i in range(n):
            for j in range(n):
                if i != j:
                    strength[i] += pairwise_matrix[i, j]
        
        # Преобразуем силу в ранги (меньший ранг = лучше)
        # Сортируем по убыванию силы (большая сила = лучшая позиция)
        sorted_indices = np.argsort(-strength)  # убывающий порядок
        
        # Присваиваем ранги (1 - лучший)
        ranks = np.zeros(n, dtype=float)
        current_rank = 1
        
        for i in range(n):
            idx = sorted_indices[i]
            # Проверяем на одинаковую силу (одинаковые ранги)
            if i > 0 and strength[idx] == strength[sorted_indices[i-1]]:
                ranks[idx] = current_rank
            else:
                current_rank = i + 1
                ranks[idx] = current_rank
        
        m = int(max(ranks)) + 1
        for rank in range(m):
            numder_eq_ranks = (ranks == rank).sum()
            if numder_eq_ranks > 1:
                for i in range(len(ranks)):
                    if (ranks == rank)[i]:
                        ranks[i] = ranks[i] + 1 / numder_eq_ranks

        return {alternatives[i]: ranks[i] for i in range(len(alternatives))} #len(ranks) + 1 - 

    def __commom_ranking__(self, criterion, mode='median'):
            dump = {'mode': mode}

            expert_common_rankings = self.__get_common_ranking__()
            dump['pairs_rankings'] = expert_common_rankings[criterion]

            '''
            results = {}
            for criterion in expert_common_rankings:
                rankings = expert_common_rankings[criterion]
                alternatives = list(self.expert_data[list(self.expert_data.keys())[0]].columns)

                optimal_ranking = {
                    alter1:
                    [
                        self.__choose_pos__(np.array([rankings[expert][alter1].loc[alter2] for expert in rankings]))
                        for alter2 in alternatives
                    ] for alter1 in alternatives
                }
                optimal_ranking['Alternatives'] = alternatives

                results[criterion] = self.__pairwise_to_ranking__(pd.DataFrame(optimal_ranking).set_index('Alternatives').T.values, alternatives=alternatives)

            result_df = {alter: [results[criterion][alter] for criterion in expert_common_rankings] for alter in alternatives}
            result_df['Alternatives'] = [criterion for criterion in expert_common_rankings]
            return pd.DataFrame(result_df).set_index('Alternatives')
            '''

        #results = []
        #for criterion in expert_common_rankings:
            rankings = expert_common_rankings[criterion]

            metric = self.__common_metric_mean__ if mode == 'mean' else self.__common_metric_median__
            dump['distances'] = [[expert, expert2, metric(ranking1=rankings[expert], ranking2=rankings[expert2])] for expert, expert2 in list(combinations(list(rankings.keys()), 2))]

            distances = {expert: sum(metric(ranking1=rankings[expert], ranking2=rankings[expert2]) for expert2 in rankings) for expert in rankings}
            optimal_expert = min(distances, key = lambda k: distances[k]) 
            dump['expert'] = optimal_expert

            optimal_estimation = pd.DataFrame(self.expert_data[criterion].loc[optimal_expert]).T
            optimal_estimation['Alternatives'] = [criterion]
            optimal_estimation = optimal_estimation.set_index('Alternatives')

            #results.append(optimal_estimation)

            return optimal_estimation, dump

    def __expert_assessments_generalization__(self, params=None):
        related_information = {}
        result_string = {}
        for criterion in self.expert_methods:
            if self.expert_methods[criterion] == "Усреднение экспертных оценок":
                result_string[criterion], related_information[criterion] = self.__expert_estimates_averaging__(criterion)
            elif self.expert_methods[criterion] == "Усреднение с оценкой компетентности экспертов по алгоритму Евланова-Кутузова":
                result_string[criterion], related_information[criterion] = self.__Evlanov_Kutuzov_expert_estimates_averaging__(criterion, **params['EK'])
            elif self.expert_methods[criterion] == "Усреднение с оценкой компетентности экспертов по алгоритму Рыкова":
                result_string[criterion], related_information[criterion] = self.__Rykov_expert_estimates_averaging__(criterion, **params['Ryk'])
            elif self.expert_methods[criterion] == "Обобщенная ранжировка":
                result_string[criterion], related_information[criterion] = self.__commom_ranking__(criterion,**params['Com'])
            else:
                raise ValueError("Некорректный метод обобщения экспертных оценок")
        return pd.concat([result_string[criterion] for criterion in result_string]), related_information
    
    '''Смена направления'''
    def __negative_change_dir__(self, alters):
        return [-i for i in alters]

    def __Sevidzh__(self, alters, max_Sev):
        max_value = alters.max() if max_Sev is None else max_Sev
        return [max_value - i for i in alters]

    def __direction_changing__(self, data):
        direction_changes = self.direcion_settings['direction_changes']
        savige_max_value = self.direcion_settings['savige_max_values']

        for criterion in direction_changes:
            if direction_changes[criterion] == 'negation':
                data.loc[criterion] = self.__negative_change_dir__(data.loc[criterion])
            elif direction_changes[criterion] == 'savige':
                data.loc[criterion] = self.__Sevidzh__(data.loc[criterion], savige_max_value[criterion])
            else:
                raise ValueError("Некорректный способ смены направления")
            
        return data

    '''Нормализация критериев'''
    def __relative__(self, alters):
        value = abs(alters.max()) if alters.max() > 0.0 else abs(alters.min()) if alters.max() < 0.0 else abs(alters.min()) if alters.min() != 0.0 else alters.max() + 10**-6
        return [i / value for i in alters]

    def __comparative__(self, alters):
        min_value = alters.min()
        return [i - min_value for i in alters]
    
    def __natural__(self, alters):
        max_value = alters.max()
        min_value = alters.min()
        return [i / (max_value - min_value) if max_value != min_value else 0 for i in alters]

    def __full__(self, alters):
        max_value = alters.max()
        min_value = alters.min()
        return [(i - min_value) / (max_value - min_value) if max_value != min_value else 0 for i in alters]

    def __normalize__(self, data):
        data = data.astype(float)

        for criterion in data.index:
            if self.normalization_methods[criterion] == 'Относительная нормализация':
                data.loc[criterion] = self.__relative__(data.loc[criterion])
            elif self.normalization_methods[criterion] == 'Сравнительная нормализация':
                data.loc[criterion] = self.__comparative__(data.loc[criterion])
            elif self.normalization_methods[criterion] == 'Естественная нормализация':
                data.loc[criterion] = self.__natural__(data.loc[criterion])
            elif self.normalization_methods[criterion] == 'Полная нормализация':
                data.loc[criterion] = self.__full__(data.loc[criterion])
            elif self.normalization_methods[criterion] == "Нет нормализации":
                pass
            else:
                raise ValueError("Некорректный метод нормализации")
        return data.apply(lambda row: row.mask(row <= row.max() * 10**-4, row.max() * 10**-4), axis=1)

    '''Обработка данных'''
    def get_processed_data(self, expert_assessments_generalization_params=None):
        related_information = {
            "expert_assessments_generalization": {}
        }

        #print("Installing params")
        if expert_assessments_generalization_params is None:
            gen_params = {}
        for mode in self.expert_estimates_averaging_default_params:
            if not mode in gen_params.keys():
                gen_params[mode] = self.expert_estimates_averaging_default_params[mode]

        #print("Expert assignment generalization")
        generalized_expert_ratings, related_information["expert_assessments_generalization"]["data"] = self.__expert_assessments_generalization__(gen_params)
        related_information["expert_assessments_generalization"]["methods"] = self.expert_methods

        #print("Get common table")
        evaluating_alternatives = pd.concat([self.numeric_data, generalized_expert_ratings])
        related_information['result_criterions_values'] = evaluating_alternatives

        #print("__direction_changing__")
        evaluating_alternatives_2 = self.__direction_changing__(evaluating_alternatives)
        related_information['direction_changing_result'] = evaluating_alternatives_2

        #print("__normalize__")
        evaluating_alternatives_3 = self.__normalize__(evaluating_alternatives)
        related_information['normalization_result'] = evaluating_alternatives_3
        
        return evaluating_alternatives_3, related_information
