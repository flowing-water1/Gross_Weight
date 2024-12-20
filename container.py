import json
import random
import copy
from collections import defaultdict
import streamlit as st
from st_copy_to_clipboard import st_copy_to_clipboard
from html import escape
import pandas as pd
from original_data import For_Update_Original_data
import math
import streamlit_antd_components as sac

config = {
    "MAX_TRAYS": 40,
    "MAX_WEIGHT": 24500,
    "SMALL_MAX_TRAYS": 20,
    "SMALL_MAX_WEIGHT": 21000,
    "COST_SMALL": 1500,
    "COST_LARGE": 2500,
    "WEIGHT_UTILIZATION_WEIGHT": 0.6,
    "COST_WEIGHT": 0.2,

    "POPULATION_SIZE": 25,
    "NUM_GENERATIONS": 50,
    "MUTATION_RATE_BASE": 0.8,
    "MUTATION_RATE_MIN": 0.2,
    "TOURNAMENT_SIZE": 3,
    "CABINET_PENALTY": 50,  # 根据实际情况调整
    "ELITISM": True,
    "PATIENCE": 20
}

#
products = [
    {"id": "Tellus S2 VX 46 1209L", "name": "Tellus S2 VX 46 1209L", "每托重量": 791.4159999999999, "trays": 13.0,
     "weight": 10288.408},
    {"id": "Omala S4 GXV 220 1209L", "name": "Omala S4 GXV 220 1209L", "每托重量": 798.1039999999999, "trays": 1.0,
     "weight": 798.1039999999999},
    {"id": "Omala S4 GX 220 1209L", "name": "Omala S4 GX 220 1209L", "每托重量": 812.3159999999999, "trays": 5.0,
     "weight": 4061.5799999999995},
    {"id": "Gadus S2 V220 2 118KG", "name": "Gadus S2 V220 2 118KG", "每托重量": 491.72, "trays": 10.0,
     "weight": 4917.200000000001},
    {
        "id": "Omala S2 GX 100 1*209L",
        "name": "Omala S2 GX 100 1*209L",
        "每托重量": 820.68,
        "trays": 3,
        "weight": 2462.03
    },

]


# with open("container_info_new.json", "r", encoding="utf-8") as file:
#     container_info_new = json.load(file)


# 1.初代方案生成（目前只使用贪心算法）


def generate_initial_population(products, population_size):
    """
    生成初始种群，采用多种生成策略以增加多样性和解决方案质量。

    :param products: 产品列表，每个产品是一个字典，包含 'id', 'trays', 'weight' 等键。
    :param population_size: 初始种群的规模。
    :return: 初始种群列表，每个个体是一个柜子列表。
    """
    population = []
    strategies = [
        random_shuffle_greedy,
        sort_by_weight_desc_greedy,
        sort_by_trays_desc_greedy,
        sort_by_ratio_desc_greedy  # 比率排序（如重量/托盘数）
    ]
    num_strategies = len(strategies)

    for i in range(population_size):
        strategy = strategies[i % num_strategies]  # 轮流使用不同策略
        individual = strategy(products)
        population.append(individual)

    return population


def random_shuffle_greedy(products):
    """
    随机打乱产品顺序后使用贪心策略生成解决方案。

    :param products: 产品列表。
    :return: 解决方案（柜子列表）。
    """
    shuffled_products = products.copy()
    random.shuffle(shuffled_products)
    return greedy_allocate(shuffled_products, config)


def sort_by_weight_desc_greedy(products):
    """
    按重量降序排序产品后使用贪心策略生成解决方案。

    :param products: 产品列表。
    :return: 解决方案（柜子列表）。
    """
    sorted_products = sorted(products, key=lambda p: p["weight"], reverse=True)
    # key:指定一个函数，此函数会被应用到每个元素上，用于提取排序的关键字（键）。
    # lambda p：这是一个匿名函数，接受一个产品p作为输入，返回该产品的托盘数与重量的比值。
    return greedy_allocate(sorted_products, config)


def sort_by_trays_desc_greedy(products):
    """
    按托盘数降序排序产品后使用贪心策略生成解决方案。

    :param products: 产品列表。
    :return: 解决方案（柜子列表）。
    """
    sorted_products = sorted(products, key=lambda p: p["trays"], reverse=True)
    return greedy_allocate(sorted_products, config)


def sort_by_ratio_desc_greedy(products):
    """
    按托盘数与重量的比率降序排序产品后使用贪心策略生成解决方案。

    :param products: 产品列表。
    :return: 解决方案（柜子列表）。
    """
    # 比率可以根据具体需求调整，这里以托盘数/重量作为比率
    sorted_products = sorted(products, key=lambda p: (p["trays"] / p["weight"]), reverse=True)
    return greedy_allocate(sorted_products, config)


def greedy_allocate(sorted_products, config):
    """
    使用贪心策略将排序后的产品分配到柜子中。

    :param sorted_products: 排序后的产品列表。
    :return: 解决方案（柜子列表）。
    """
    current_cabinets = []
    remaining_products = sorted_products.copy()

    while remaining_products:
        trays_left = config["MAX_TRAYS"]
        weight_left = config["MAX_WEIGHT"]
        products_in_cabinet = []

        # 遍历剩余产品，尽可能多地放入当前柜子
        for product in remaining_products[:]:
            if product["trays"] <= trays_left and product["weight"] <= weight_left:
                products_in_cabinet.append(product)  # 将产品添加到当前柜子中。
                trays_left -= product["trays"]  # 减少当前柜子的剩余托盘数。
                weight_left -= product["weight"]  # 减少当前柜子的剩余重量。
                remaining_products.remove(product)  # 将产品从未分配列表中移除，表示已被分配。

        if products_in_cabinet:  # 如果当前柜子中有产品被分配（即成功分配了一些产品）
            current_cabinets.append(products_in_cabinet)  # 将当前柜子（包含已分配的产品）添加到current_cabinets列表中。
        else:
            #  如果没有任何产品符合当前柜子的剩余容量，意味着剩余的产品中可能有某些产品本身就超过了柜子的托盘数或重量限制。
            product = remaining_products.pop(0)  # 从未分配的产品列表中取出第一个产品。这通常是最重或托盘数最多的产品，因为产品已经经过排序（例如托盘数与重量比值降序）。
            current_cabinets.append([product])  # 将该产品单独放入一个新的柜子中。这确保即使某个产品本身就超过柜子的限制，它仍然被分配到一个柜子中，避免无限循环。

    return current_cabinets


# 2.适应度
def calculate_fitness(solution, config):
    total_cost = 0.0
    total_weight_utilization = 0.0
    number_of_cabinets = len(solution)
    constraints_violated = False

    for cabinet in solution:
        total_trays = sum(p["trays"] for p in cabinet)
        total_weight = sum(p["weight"] for p in cabinet)

        # 检查是否为小柜子还是大柜子
        if total_trays <= config["SMALL_MAX_TRAYS"] and total_weight <= config["SMALL_MAX_WEIGHT"]:
            cabinet_cost = config["COST_SMALL"]
            max_trays = config["SMALL_MAX_TRAYS"]
            max_weight = config["SMALL_MAX_WEIGHT"]
        else:
            cabinet_cost = config["COST_LARGE"]
            max_trays = config["MAX_TRAYS"]
            max_weight = config["MAX_WEIGHT"]

        # 检查是否超出限制
        if total_trays > max_trays or total_weight > max_weight:
            constraints_violated = True  # 标记为不可行解

        total_cost += cabinet_cost
        weight_utilization = (total_weight / max_weight) ** 2
        total_weight_utilization += weight_utilization

    avg_weight_utilization = total_weight_utilization / number_of_cabinets if number_of_cabinets > 0 else 0
    # 所有柜子的重量利用率的平均值。用于衡量整体的重量利用效率。

    if constraints_violated:
        # 对于不可行解，给予极低的适应度
        fitness = -1e6  # 非常低的值，确保不可行解不会被选择
    else:
        # 对于可行解，计算适应度
        fitness = (
                avg_weight_utilization * config["WEIGHT_UTILIZATION_WEIGHT"]
                - (total_cost / (number_of_cabinets * config["COST_LARGE"]) * config["COST_WEIGHT"])
                - (number_of_cabinets * config["CABINET_PENALTY"])
        )
        # 权重利用率越高，适应度越高。通过权重 WEIGHT_UTILIZATION_WEIGHT 平衡其在适应度中的重要性。
        # 总成本越低，适应度越高。通过归一化成本(使用了大柜子的成本作为基准)并乘以权重 COST_WEIGHT 来平衡其影响。 也就是鼓励使用大柜子
        # total_cost 实际上包含了小柜子和大柜子的成本。因此，使用小柜子可以有效地降低 total_cost
        # 使用的柜子数量越少，适应度越高。通过 CABINET_PENALTY 对每个柜子的数量进行惩罚，鼓励减少柜子的使用。
    # 标准化适应度
    normalized_fitness = (fitness + 1000) / 1001
    normalized_fitness = max(0.0, min(1.0, normalized_fitness))

    return normalized_fitness


import numpy as np


def get_fitness_statistics(fitness_values):
    """
    计算适应度的统计信息，包括最大值、最小值、平均值和特定百分位数。

    :param fitness_values: 种群中所有个体的适应度值列表
    :return: 字典，包含统计信息
    """
    stats = {
        "max": max(fitness_values),
        "min": min(fitness_values),
        "avg": sum(fitness_values) / len(fitness_values) if len(fitness_values) > 0 else 0,
        "25_percentile": np.percentile(fitness_values, 25),
        # 找到一个值，使得有25%的适应度值小于或等于这个值。
        "75_percentile": np.percentile(fitness_values, 75)
        # 找到一个值，使得有75%的适应度值小于或等于这个值。
    }
    return stats


def get_mutation_types_based_on_fitness(fitness, fitness_stats, config):
    """
    根据适应度值和适应度统计信息调整变异类型的选择概率。

    :param fitness: 当前解决方案的适应度值
    :param fitness_stats: 当前种群的适应度统计信息
    :param config: 配置参数字典
    :return: 变异类型及其对应的权重字典
    """
    # 使用相对阈值
    if fitness >= fitness_stats["75_percentile"]:
        # 高适应度，倾向于细微变异
        mutation_types = {
            'swap': 0.6,
            'move': 0.4
        }
    elif fitness >= fitness_stats["25_percentile"]:
        # 中等适应度，平衡变异
        mutation_types = {
            'swap': 0.3,
            'move': 0.3,
            'merge': 0.2,
            'split': 0.2
        }
    else:
        # 低适应度，倾向于大幅度变异
        mutation_types = {
            'split': 0.5,
            'reallocate': 0.3,
            'merge': 0.2
        }

    return mutation_types


# # 为初始种群重新计算适应度
# fitness_values = []
# for idx, solution in enumerate(initial_population, start=1):
#     fitness = calculate_fitness(solution)
#     fitness_values.append((idx, fitness))
#     print(f"方案 {idx} 的适应度: {fitness:.4f}")
#
# # 打印适应度最高的方案
# best_solution_idx = max(fitness_values, key=lambda x: x[1])[0]
# print(f"\n适应度最高的方案是方案 {best_solution_idx}\n")

# 3. 交叉


import random


def pmx_crossover(parent1, parent2, products, config):
    """
    部分映射交叉（PMX）适用于排列问题，这里需要根据分配问题进行调整。
    由于分配问题的特殊性，PMX可能不完全适用，因此可以考虑使用顺序交叉（OX）。

    :param parent1: 父代1（柜子列表）
    :param parent2: 父代2（柜子列表）
    :param config: 配置参数字典
    :return: 子代1和子代2（柜子列表）
    """

    def encode_solution(solution):
        product_to_cabinet = {}
        for cabinet_idx, cabinet in enumerate(solution):
            for product in cabinet:
                product_to_cabinet[product['id']] = cabinet_idx
        return product_to_cabinet

    # 将映射转换回方案
    def decode_solution(product_to_cabinet):
        cabinets = []
        num_cabinets = max(product_to_cabinet.values()) + 1
        for _ in range(num_cabinets):
            cabinets.append([])
        for product_id, cabinet_idx in product_to_cabinet.items():
            product = next((p for p in products if p['id'] == product_id), None)
            if product:
                cabinets[cabinet_idx].append(product)
        return cabinets

    parent1_mapping = encode_solution(parent1)
    parent2_mapping = encode_solution(parent2)
    product_ids = list(parent1_mapping.keys())

    # 随机选择两个交叉点
    crossover_points = sorted(random.sample(range(len(product_ids)), 2))
    idx1, idx2 = crossover_points

    child1_mapping = parent1_mapping.copy()
    child2_mapping = parent2_mapping.copy()

    # 交换交叉区间的柜子分配
    for i in range(idx1, idx2 + 1):
        pid = product_ids[i]
        # 交换父代的柜子分配
        child1_mapping[pid], child2_mapping[pid] = parent2_mapping[pid], parent1_mapping[pid]

    # 处理冲突
    def fix_conflicts(child_mapping, parent_mapping):
        mapping = child_mapping.copy()
        inverted_mapping = {}
        for pid, cabinet_idx in mapping.items():
            if pid in inverted_mapping:
                # 发生冲突，修正
                orig_cabinet_idx = inverted_mapping[pid]
                mapping[pid] = parent_mapping[pid]
            else:
                inverted_mapping[pid] = cabinet_idx
        return mapping

    child1_mapping = fix_conflicts(child1_mapping, parent1_mapping)
    child2_mapping = fix_conflicts(child2_mapping, parent2_mapping)

    # 将映射转换回方案
    child1 = decode_solution(child1_mapping)
    child2 = decode_solution(child2_mapping)

    return child1, child2


# 更新交叉操作函数
def perform_crossover(population, fitness_values, products, config, num_offspring=5):
    # 与之前相同的选择父代方法
    sorted_population = [solution for _, solution in
                         sorted(zip(fitness_values, population), key=lambda x: x[0], reverse=True)]

    offspring = []

    # 生成指定数量的子代
    for _ in range(num_offspring // 2):
        # 随机选择两个适应度较高的父代进行交叉
        parent1 = random.choice(sorted_population[:len(sorted_population) // 2])
        parent2 = random.choice(sorted_population[:len(sorted_population) // 2])

        # 确保两个父代不同
        while parent1 == parent2:
            parent2 = random.choice(sorted_population[:len(sorted_population) // 2])

        # 使用PMX交叉生成两个子代
        child1, child2 = pmx_crossover(parent1, parent2, products, config)

        offspring.append(child1)
        offspring.append(child2)

    return offspring


# # 进行交叉操作，生成新的子代
# offspring = perform_crossover(initial_population, [fitness for _, fitness in fitness_values], num_offspring=10)
#
# # 打印生成的子代方案
# for idx, solution in enumerate(offspring, start=1):
#     print(f"交叉子代方案 {idx}:")
#     for cabinet_idx, cabinet in enumerate(solution, start=1):
#         total_trays = sum(p["trays"] for p in cabinet)
#         total_weight = sum(p["weight"] for p in cabinet)
#         print(f"  柜子 {cabinet_idx}: 托盘数: {total_trays}, 重量: {total_weight}kg")
#         for product in cabinet:
#             print(f"    产品 {product['id']}, 托盘数: {product['trays']}, 重量: {product['weight']}kg")
#     print("\n")


#
# # 为初始种群重新计算适应度
# fitness_values = []
# for idx, solution in enumerate(offspring, start=1):
#     fitness = calculate_fitness(solution)
#     fitness_values.append((idx, fitness))
#     print(f"交叉方案 {idx} 的适应度: {fitness:.4f}")
#
# # 打印适应度最高的方案
# best_solution_idx = max(fitness_values, key=lambda x: x[1])[0]
# print(f"\n交叉环节适应度最高的方案是方案 {best_solution_idx}\n")


# 4.变异
import random
import copy

import random
import copy


def mutate(solution, fitness, current_generation, max_generations, config, fitness_stats):
    """
    对给定的解决方案应用多重变异操作，基于适应度动态调整变异类型的选择概率，
    并根据迭代进展动态调整变异率。

    :param solution: 当前的解决方案（柜子列表）
    :param fitness: 当前解决方案的适应度值
    :param current_generation: 当前代数
    :param max_generations: 最大代数
    :param config: 配置参数字典
    :return: 变异后的解决方案
    """
    mutated_solution = copy.deepcopy(solution)
    mutation_types_applied = []

    # 动态调整变异率
    mutation_rate = adjust_mutation_rate(current_generation, max_generations,
                                         config["MUTATION_RATE_BASE"], config["MUTATION_RATE_MIN"])

    print(f"Gen {current_generation + 1}: Mutation Rate = {mutation_rate:.4f}")

    # 确定变异是否发生
    if random.random() < mutation_rate:
        # 根据适应度调整变异类型的选择概率
        mutation_types = get_mutation_types_based_on_fitness(fitness, fitness_stats, config)
        print(f"Gen {current_generation + 1}: Selected Mutation Types = {mutation_types}")

        # 决定执行的变异次数（例如1到2次）
        num_mutations = random.randint(1, 2)

        for _ in range(num_mutations):
            mutation_type = random.choices(
                population=list(mutation_types.keys()),
                weights=list(mutation_types.values()),
                k=1
            )[0]
            mutation_types_applied.append(mutation_type)

            print(f"Gen {current_generation + 1}: Applying Mutation Type = {mutation_type}")

            # 执行相应的变异操作
            if mutation_type == 'swap':
                mutated_solution = mutate_swap(mutated_solution, config)
            elif mutation_type == 'move':
                mutated_solution = mutate_move(mutated_solution, config)
            elif mutation_type == 'merge':
                mutated_solution = mutate_merge(mutated_solution, config)
            elif mutation_type == 'split':
                mutated_solution = mutate_split(mutated_solution, config)
            elif mutation_type == 'reallocate':
                mutated_solution = mutate_reallocate(mutated_solution, config)
            elif mutation_type == 'adjust':
                mutated_solution = mutate_adjust(mutated_solution, config)

        # 最后修复柜子，确保所有柜子满足限制
        mutated_solution = fix_cabinets(mutated_solution, config)

        print(f"Gen {current_generation + 1}: Mutation Applied and Solution Fixed")

    else:
        print(f"Gen {current_generation + 1}: Mutation Not Applied")

    print(f"!!!!!!!!!!!!!Gen {current_generation + 1}!!!!!!!!!!!")
    return mutated_solution, current_generation + 1, mutation_types_applied


def adjust_mutation_rate(current_generation, max_generations, base_rate=0.7, min_rate=0.1):
    """
    动态调整变异率，采用线性衰减策略。

    :param current_generation: 当前代数
    :param max_generations: 最大代数
    :param base_rate: 初始变异率
    :param min_rate: 最低变异率
    :return: 调整后的变异率
    """
    rate = base_rate - (base_rate - min_rate) * (current_generation / max_generations)
    return max(rate, min_rate)


def mutate_swap(mutated_solution, config):
    """
    执行 'swap' 变异操作：交换两个不同柜子中的产品。

    :param mutated_solution: 当前解决方案（柜子列表）
    :param config: 配置参数字典
    :return: 变异后的解决方案
    """
    all_products = [p for cabinet in mutated_solution for p in cabinet]

    if len(all_products) >= 2:
        product1, product2 = random.sample(all_products, 2)

        # 找到它们所在的柜子
        cabinet1_idx = next(idx for idx, cabinet in enumerate(mutated_solution) if product1 in cabinet)
        cabinet2_idx = next(idx for idx, cabinet in enumerate(mutated_solution) if product2 in cabinet)

        # 检查交换后柜子的限制是否满足
        cabinet1 = mutated_solution[cabinet1_idx]
        cabinet2 = mutated_solution[cabinet2_idx]

        new_trays1 = sum(p["trays"] for p in cabinet1) - product1["trays"] + product2["trays"]
        new_weight1 = sum(p["weight"] for p in cabinet1) - product1["weight"] + product2["weight"]

        new_trays2 = sum(p["trays"] for p in cabinet2) - product2["trays"] + product1["trays"]
        new_weight2 = sum(p["weight"] for p in cabinet2) - product2["weight"] + product1["weight"]

        if ((new_trays1 <= config["MAX_TRAYS"] and new_weight1 <= config["MAX_WEIGHT"]) and
                (new_trays2 <= config["MAX_TRAYS"] and new_weight2 <= config["MAX_WEIGHT"])):
            # 执行交换
            cabinet1.remove(product1)
            cabinet2.remove(product2)
            cabinet1.append(product2)
            cabinet2.append(product1)

    return mutated_solution


def mutate_move(mutated_solution, config):
    """
    执行 'move' 变异操作：将一个产品移动到另一个柜子或新柜子。

    :param mutated_solution: 当前解决方案（柜子列表）
    :param config: 配置参数字典
    :return: 变异后的解决方案
    """
    all_products = [p for cabinet in mutated_solution for p in cabinet]

    if len(all_products) >= 1:
        product = random.choice(all_products)

        # 找到产品所在的柜子
        from_cabinet_idx = next(idx for idx, cabinet in enumerate(mutated_solution) if product in cabinet)

        # 尝试将产品移到其他柜子
        possible_cabinets = list(range(len(mutated_solution))) + [len(mutated_solution)]  # 包括新柜子的索引

        # 过滤出可以容纳该产品的柜子
        feasible_cabinets = []
        for idx in possible_cabinets:
            if idx == len(mutated_solution):
                # 新柜子，不需要检查限制
                feasible_cabinets.append(idx)
            else:
                cabinet = mutated_solution[idx]
                total_trays = sum(p["trays"] for p in cabinet) + product["trays"]
                total_weight = sum(p["weight"] for p in cabinet) + product["weight"]
                if total_trays <= config["MAX_TRAYS"] and total_weight <= config["MAX_WEIGHT"]:
                    feasible_cabinets.append(idx)

        if feasible_cabinets:
            target_cabinet_idx = random.choice(feasible_cabinets)

            # 移除产品
            mutated_solution[from_cabinet_idx].remove(product)

            # 添加产品到目标柜子
            if target_cabinet_idx == len(mutated_solution):
                # 新建柜子
                mutated_solution.append([product])
            else:
                mutated_solution[target_cabinet_idx].append(product)

    return mutated_solution


def mutate_merge(mutated_solution, config):
    """
    执行 'merge' 变异操作：合并两个柜子。

    :param mutated_solution: 当前解决方案（柜子列表）
    :param config: 配置参数字典
    :return: 变异后的解决方案
    """
    if len(mutated_solution) >= 2:
        cabinet1_idx, cabinet2_idx = random.sample(range(len(mutated_solution)), 2)
        cabinet1 = mutated_solution[cabinet1_idx]
        cabinet2 = mutated_solution[cabinet2_idx]

        combined_trays = sum(p["trays"] for p in cabinet1 + cabinet2)
        combined_weight = sum(p["weight"] for p in cabinet1 + cabinet2)

        if combined_trays <= config["MAX_TRAYS"] and combined_weight <= config["MAX_WEIGHT"]:
            # 合并柜子
            mutated_solution[cabinet1_idx] = cabinet1 + cabinet2
            # 删除第二个柜子
            mutated_solution.pop(cabinet2_idx)

    return mutated_solution


def mutate_split(mutated_solution, config):
    """
    执行 'split' 变异操作：将一个柜子中的某个产品移出，形成一个新柜子。

    :param mutated_solution: 当前解决方案（柜子列表）
    :param config: 配置参数字典
    :return: 变异后的解决方案
    """
    if len(mutated_solution) >= 1:
        # 随机选择一个柜子进行拆分
        cabinet_idx = random.randint(0, len(mutated_solution) - 1)
        cabinet = mutated_solution[cabinet_idx]

        if len(cabinet) >= 2:
            # 随机选择一个产品进行拆分
            product_to_split = random.choice(cabinet)

            # 尝试将该产品移出，形成一个新柜子
            mutated_solution[cabinet_idx].remove(product_to_split)

            # 检查新柜子是否满足限制
            if (product_to_split["trays"] <= config["MAX_TRAYS"] and
                    product_to_split["weight"] <= config["MAX_WEIGHT"]):
                mutated_solution.append([product_to_split])
            else:
                # 如果单个产品超过限制，重新添加回原柜子
                mutated_solution[cabinet_idx].append(product_to_split)

    return mutated_solution


def mutate_reallocate(mutated_solution, config):
    """
    执行 'reallocate' 变异操作：重新分配几个随机选择的产品。

    :param mutated_solution: 当前解决方案（柜子列表）
    :param config: 配置参数字典
    :return: 变异后的解决方案
    """
    num_reallocations = random.randint(1, 3)
    products = [p for cabinet in mutated_solution for p in cabinet]

    if len(products) >= num_reallocations:
        selected_products = random.sample(products, num_reallocations)
        for product in selected_products:
            from_cabinet_idx = next(idx for idx, cabinet in enumerate(mutated_solution) if product in cabinet)
            mutated_solution[from_cabinet_idx].remove(product)

            # 找到合适的柜子
            feasible_cabinets = [idx for idx, cabinet in enumerate(mutated_solution)
                                 if sum(p["trays"] for p in cabinet) + product["trays"] <= config["MAX_TRAYS"] and
                                 sum(p["weight"] for p in cabinet) + product["weight"] <= config["MAX_WEIGHT"]]
            if feasible_cabinets:
                target_idx = random.choice(feasible_cabinets)
                mutated_solution[target_idx].append(product)
            else:
                # 创建新柜子
                mutated_solution.append([product])

    return mutated_solution


def mutate_adjust(mutated_solution, config):
    """
    执行 'adjust' 变异操作：微调柜子中的产品。

    :param mutated_solution: 当前解决方案（柜子列表）
    :param config: 配置参数字典
    :return: 变异后的解决方案
    """
    cabinet_idx = random.randint(0, len(mutated_solution) - 1)
    cabinet = mutated_solution[cabinet_idx]

    if len(cabinet) > 1:
        product = random.choice(cabinet)
        mutated_solution[cabinet_idx].remove(product)

        feasible_cabinets = [idx for idx, c in enumerate(mutated_solution)
                             if sum(p["trays"] for p in c) + product["trays"] <= config["MAX_TRAYS"] and
                             sum(p["weight"] for p in c) + product["weight"] <= config["MAX_WEIGHT"]]
        if feasible_cabinets:
            target_idx = random.choice(feasible_cabinets)
            mutated_solution[target_idx].append(product)
        else:
            # 创建新柜子
            mutated_solution.append([product])

    return mutated_solution


def fix_cabinets(solution, config):
    new_solution = []
    overflow_products = []

    for cabinet in solution:
        total_trays = sum(p["trays"] for p in cabinet)
        total_weight = sum(p["weight"] for p in cabinet)

        if total_trays > config["MAX_TRAYS"] or total_weight > config["MAX_WEIGHT"]:
            # 如果超限，尝试拆分柜子
            overflow_products.extend(cabinet)
        else:
            new_solution.append(cabinet)

    # 尝试重新分配溢出的产品
    for product in overflow_products:
        placed = False
        # 尝试放入已有的柜子
        for cabinet in new_solution:
            total_trays = sum(p["trays"] for p in cabinet)
            total_weight = sum(p["weight"] for p in cabinet)
            if total_trays + product["trays"] <= config["MAX_TRAYS"] and total_weight + product["weight"] <= config[
                "MAX_WEIGHT"]:
                cabinet.append(product)
                placed = True
                break
        if not placed:
            # 如果无法放入任何现有柜子，创建新柜子
            new_solution.append([product])

    # 最后，确保所有柜子满足限制
    final_solution = []
    for cabinet in new_solution:
        total_trays = sum(p["trays"] for p in cabinet)
        total_weight = sum(p["weight"] for p in cabinet)
        if total_trays <= config["MAX_TRAYS"] and total_weight <= config["MAX_WEIGHT"]:
            final_solution.append(cabinet)
        else:
            # 如果仍然超限，可能需要进一步拆分
            sorted_products = sorted(cabinet, key=lambda p: p["trays"] + p["weight"], reverse=True)
            temp_cabinet = []
            for product in sorted_products:
                if sum(p["trays"] for p in temp_cabinet) + product["trays"] <= config["MAX_TRAYS"] and \
                        sum(p["weight"] for p in temp_cabinet) + product["weight"] <= config["MAX_WEIGHT"]:
                    temp_cabinet.append(product)
                else:
                    final_solution.append(temp_cabinet)
                    temp_cabinet = [product]
            if temp_cabinet:
                final_solution.append(temp_cabinet)

    return final_solution


def apply_mutation(population, fitness_values, current_generation, max_generations, config, fitness_stats):
    """
    对种群中的每个解决方案应用变异操作，并统计总的变异次数。

    :param population: 当前种群列表
    :param fitness_values: 当前种群对应的适应度值列表
    :param current_generation: 当前代数
    :param max_generations: 最大代数
    :param config: 配置参数字典
    :param fitness_stats: 当前种群的适应度统计信息
    :return: (变异后的种群, 总变异次数)
    """
    mutated_population = []
    total_mutations = 0
    mutation_type_counts = defaultdict(int)

    for solution, fitness in zip(population, fitness_values):
        mutated_solution, mutation, mutation_types_applied = mutate(solution, fitness, current_generation,
                                                                    max_generations, config, fitness_stats)
        mutated_population.append(mutated_solution)
        total_mutations += mutation
        for m_type in mutation_types_applied:
            mutation_type_counts[m_type] += 1
    print(f"mutation:{total_mutations}")
    return mutated_population, total_mutations, mutation_type_counts


#
# # 1. 对子代应用变异操作
# mutated_offspring = apply_mutation(offspring, 0.7)
#
# # 2. 打印变异后的子代方案
# for idx, solution in enumerate(mutated_offspring, start=1):
#     print(f"变异后子代方案 {idx}:")
#     for cabinet_idx, cabinet in enumerate(solution, start=1):
#         total_trays = sum(p["trays"] for p in cabinet)
#         total_weight = sum(p["weight"] for p in cabinet)
#         print(f"  柜子 {cabinet_idx}: 托盘数: {total_trays}, 重量: {total_weight}kg")
#         for product in cabinet:
#             print(f"    产品 {product['id']}, 托盘数: {product['trays']}, 重量: {product['weight']}kg")
#     print("\n")
#
# # 3. 使用calculate_fitness_new计算适应度
# fitness_values_mutated = []
# for idx, solution in enumerate(mutated_offspring, start=1):
#     fitness = calculate_fitness(solution)
#     fitness_values_mutated.append((idx, fitness))
#     print(f"变异后方案 {idx} 的适应度: {fitness:.4f}")
#
# # 找出适应度最高的方案
# best_solution_idx = max(fitness_values_mutated, key=lambda x: x[1])[0]
# print(f"\n变异后适应度最高的方案是方案 {best_solution_idx}\n")

# 5.迭代
import random
import copy


def tournament_selection(population, fitness_values, tournament_size):
    """
    锦标赛选择策略。

    :param population: 当前种群列表
    :param fitness_values: 当前种群对应的适应度值列表
    :param tournament_size: 锦标赛规模
    :return: 选择后的种群列表
    """
    selected = []
    for _ in range(len(population)):
        # 随机选择 tournament_size 个个体
        participants = random.sample(list(zip(population, fitness_values)), tournament_size)
        # 选择适应度最高的个体
        winner = max(participants, key=lambda x: x[1])
        selected.append(winner[0])
    return selected


# 初始化种群
def run_genetic_algorithm(products, config):
    # 生成初始种群
    population = generate_initial_population(products, config["POPULATION_SIZE"])

    # 初始化统计数据
    stats = {
        "total_mutations": 0,
        "total_crossovers": 0,
        "total_tournaments": 0,
        "fitness_history": [],
        "mutation_type_counts": defaultdict(int),
        "crossover_history": [],
        "tournament_history": []
    }

    # 打印初始种群
    for idx, solution in enumerate(population, start=1):
        print(f"方案 {idx}:")
        for cabinet_idx, cabinet in enumerate(solution, start=1):
            total_trays = sum(p["trays"] for p in cabinet)
            total_weight = sum(p["weight"] for p in cabinet)
            print(f"  柜子 {cabinet_idx}: 托盘数: {total_trays}, 重量: {total_weight}kg")
            for product in cabinet:
                print(f"    产品 {product['id']}, 托盘数: {product['trays']}, 重量: {product['weight']}kg")
        print("\n")

    # 开始迭代
    best_fitness = float('-inf')
    best_solution = None
    no_improvement_generations = 0

    # 生成初始种群
    # population = generate_initial_population(products, config["POPULATION_SIZE"])

    for generation in range(config["NUM_GENERATIONS"]):
        # 评估适应度
        fitness_values = [calculate_fitness(solution, config) for solution in population]
        fitness_stats = get_fitness_statistics(fitness_values)

        # 记录适应度统计
        stats["fitness_history"].append({
            "generation": generation + 1,
            "max_fitness": fitness_stats["max"],
            "min_fitness": fitness_stats["min"],
            "avg_fitness": fitness_stats["avg"],
            "median_fitness": np.median(fitness_values)
        })

        # 找到当前代的最优个体
        current_best_fitness = max(fitness_values)
        current_best_solution = population[fitness_values.index(current_best_fitness)]

        # 计算平均和中位适应度
        avg_fitness = fitness_stats["avg"]
        median_fitness = np.median(fitness_values)

        # 更新全局最优解
        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_solution = copy.deepcopy(current_best_solution)
            no_improvement_generations = 0
        else:
            no_improvement_generations += 1

        print(f"第 {generation + 1} 代: 最高适应度 = {current_best_fitness:.4f}")

        # 检查早停条件
        if no_improvement_generations >= config["PATIENCE"]:
            print("适应度在连续几代内没有提升，提前终止迭代。")
            break

        # 精英保留
        elites = []
        if config["ELITISM"]:
            elite_idx = fitness_values.index(current_best_fitness)
            elites.append(copy.deepcopy(population[elite_idx]))

        # 选择
        selected_population = tournament_selection(population, fitness_values, config["TOURNAMENT_SIZE"])
        stats["total_tournaments"] += config["POPULATION_SIZE"]
        stats["tournament_history"].append({
            "generation": generation + 1,
            "tournaments": config["POPULATION_SIZE"]
        })
        print(f"第 {generation + 1} 代: 进行 {config['POPULATION_SIZE']} 次锦标赛选择")

        # 交叉
        offspring = []
        crossovers_this_generation = 0
        for i in range(0, len(selected_population), 2):
            parent1 = selected_population[i]
            if i + 1 < len(selected_population):
                parent2 = selected_population[i + 1]
            else:
                parent2 = selected_population[0]  # 如果是奇数个，则最后一个与第一个交叉
            child1, child2 = pmx_crossover(parent1, parent2, products, config)
            offspring.append(child1)
            offspring.append(child2)
            crossovers_this_generation += 1  # 每次交叉生成两个子代，计数一次

        stats["total_crossovers"] += crossovers_this_generation
        stats["crossover_history"].append({
            "generation": generation + 1,
            "crossovers": crossovers_this_generation
        })

        # 确保种群规模一致
        offspring = offspring[:config["POPULATION_SIZE"] - len(elites)]

        # 变异
        # 变异
        mutated_offspring, mutations, mutation_type_counts = apply_mutation(
            population=offspring,
            fitness_values=[calculate_fitness(sol, config) for sol in offspring],
            current_generation=generation,
            max_generations=config["NUM_GENERATIONS"],
            config=config,
            fitness_stats=fitness_stats
        )
        stats["total_mutations"] = mutations
        # 更新变异类型统计
        for m_type, count in mutation_type_counts.items():
            stats["mutation_type_counts"][m_type] += count
        # 形成新的种群
        population = elites + mutated_offspring

    # 输出最优解
    print("\n最优方案:")
    print(f"适应度: {best_fitness:.4f}")
    for cabinet_idx, cabinet in enumerate(best_solution, start=1):
        total_trays = sum(p["trays"] for p in cabinet)
        total_weight = sum(p["weight"] for p in cabinet)
        print(f"  柜子 {cabinet_idx}: 托盘数: {total_trays}, 重量: {total_weight}kg")
        for product in cabinet:
            print(f"    产品 {product['id']}, 托盘数: {product['trays']}, 重量: {product['weight']}kg")
        print("\n")

    return best_solution, best_fitness, generation, stats


#
# best_solution, best_fitness, generation, stats = run_genetic_algorithm(products, config)
# max_length = max(len(mutation_type) for mutation_type in stats['mutation_type_counts'].keys())
#
# print(
#     f"✅ 计算完成！ 🧐\n\n"
#     f"🔄 本次迭代次数: {generation + 1} 次\n\n"
#     f"🧬 本次变异次数: {stats['total_mutations']} 次\n\n"
#     f"🔀 本次交叉次数: {stats['total_crossovers']} 次\n\n"
#     f"🏁 总锦标赛次数: {stats['total_tournaments']} 次\n\n"
#     f"🥇 本次运行中使用的变异类型分布:\n" +
#     "\n".join([f"- {mutation_type.ljust(max_length)} : {count} 次" for mutation_type, count in
#                stats['mutation_type_counts'].items()]) +
#     f"\n\n🏆 最终适应度为: {best_fitness:.4f} "
#
# )


def allocate_cabinets_to_types(solution, best_fitness, generations_run, stats):
    """
    将分配出的柜子分类为大柜子和小柜子，并基于产品名称查询规格、净重、毛重。

    :param best_fitness: 最终适应度
    :param stats: 迭代过程中的各项数据记录
    :param generations_run: 迭代次数
    :param solution: 最优方案中的柜子列表
    :param small_container_limit_trays: 小柜子的托盘数限制
    :param small_container_limit_weight: 小柜子的重量限制（kg）
    :return: 大柜子列表和小柜子列表
    """
    large_containers = []
    small_containers = []
    small_container_limit_trays = 20
    small_container_limit_weight = 21000

    for cabinet in solution:
        total_trays = sum(p["trays"] for p in cabinet)
        total_weight = sum(p["weight"] for p in cabinet)

        if total_trays <= small_container_limit_trays and total_weight <= small_container_limit_weight:
            small_containers.append(cabinet)
        else:
            large_containers.append(cabinet)

    def get_product_details(product):
        """
        根据产品名称查询规格、净重、毛重。

        :param product: 产品字典
        :return: 包含规格、净重、毛重的新字典
        """
        name = product.get("产品编号")
        # 查找对应的产品信息
        match = For_Update_Original_data[For_Update_Original_data["产品编号（金蝶云）"] == name]
        if not match.empty:
            product_details = match.iloc[0]
            return {
                "规格": product_details["产品规格"],
                "毛重 (kg)": product_details["毛重（箱/桶）"]
            }
        else:
            # 如果找不到匹配的产品，返回原有信息或默认值
            return {
                "规格": "未知",
                "毛重 (kg)": "未知"
            }

    def create_display_table(cabinet):
        """
        创建用于展示的产品信息表格，包含规格、净重、毛重。

        :param cabinet: 柜子中的产品列表
        :return: pandas DataFrame
        """
        display_data = []
        for product in cabinet:
            details = get_product_details(product)
            # 格式化数值，限制小数位数
            try:
                毛重 = f"{float(details['毛重 (kg)']):.2f}"
            except (ValueError, TypeError):
                毛重 = details['毛重 (kg)']
            try:
                总重量 = f"{float(product.get('weight', 0)):.2f}"
            except (ValueError, TypeError):
                总重量 = product.get('weight', '未知')

            display_data.append({
                "编号": product.get("产品编号"),
                "产品名称": product.get("name"),
                "规格": details["规格"],
                "数量": product.get("产品数量"),
                "毛重 (kg)": 毛重,
                "托盘数": product.get("trays"),
                "总重量 (kg)": 总重量
            })
        return pd.DataFrame(display_data)

    def create_html_table(large_cabinets, small_cabinets):
        """
        创建用于展示的所有柜子的HTML表格，包含合并单元格的“柜型”列。

        :param large_cabinets: 大柜子列表
        :param small_cabinets: 小柜子列表
        :return: HTML 字符串
        """
        html = """
        <style>
            .cabinet-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                table-layout: auto;
            }
            .cabinet-table th, .cabinet-table td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: center;
                vertical-align: middle;
                word-wrap: break-word;
                max-width: 150px;
            }
            .cabinet-table th {
                background-color: #f2f2f2;
                position: sticky;
                top: 0;
                z-index: 1;
            }
            .table-container {
                overflow-x: auto;
                max-height: 600px;
            }
            /* 优化表格字体和间距 */
            .cabinet-table {
                font-size: 14px;
            }
            .cabinet-table th, .cabinet-table td {
                padding: 10px;
            }
        </style>
        <div class="table-container">
            <table class="cabinet-table">
                <thead>
                    <tr>
                        <th>编号</th>
                        <th>产品名称</th>
                        <th>规格</th>
                        <th>数量</th>
                        <th>毛重 (kg)</th>
                        <th>托盘数</th>
                        <th>总重量 (kg)</th>
                        <th>柜型</th>
                    </tr>
                </thead>
                <tbody>
        """

        def add_cabinets_to_html(cabinets, cabinet_type):
            nonlocal html
            for cabinet in cabinets:
                display_data = []
                for product in cabinet:
                    details = get_product_details(product)
                    # 格式化数值，限制小数位数
                    try:
                        毛重 = f"{float(details['毛重 (kg)']):.2f}"
                    except (ValueError, TypeError):
                        毛重 = details['毛重 (kg)']
                    try:
                        总重量 = f"{float(product.get('weight', 0)):.2f}"
                    except (ValueError, TypeError):
                        总重量 = product.get('weight', '未知')

                    display_data.append({
                        "编号": product.get("产品编号"),
                        "产品名称": product.get("name"),
                        "规格": details["规格"],
                        "数量": product.get("产品数量"),
                        "毛重 (kg)": 毛重,
                        "托盘数": product.get("trays"),
                        "总重量 (kg)": 总重量
                    })
                num_products = len(display_data)
                for idx, row in enumerate(display_data):
                    html += "<tr>"
                    html += f"<td>{escape(str(row['编号']))}</td>"
                    html += f"<td>{escape(str(row['产品名称']))}</td>"
                    html += f"<td>{escape(str(row['规格']))}</td>"
                    html += f"<td>{escape(str(row['数量']))}</td>"
                    html += f"<td>{escape(str(row['毛重 (kg)']))}</td>"
                    html += f"<td>{escape(str(row['托盘数']))}</td>"
                    html += f"<td>{escape(str(row['总重量 (kg)']))}</td>"
                    if idx == 0:
                        html += f"<td rowspan='{num_products}'>{escape(cabinet_type)}</td>"
                    html += "</tr>"

        # 添加大柜子
        add_cabinets_to_html(large_cabinets, "40HQ")
        # 添加小柜子
        add_cabinets_to_html(small_cabinets, "20GP")

        html += """
                </tbody>
            </table>
        </div>
        """
        return html

    def display_original_cabinets(cabinets, cabinet_label, no_cabinet_label, cabinet_type):
        """
        显示柜子信息，使用原有的st.header和st.expander展示。

        :param no_cabinet_label: 没有柜子时的显示信息
        :param cabinets: 柜子列表
        :param cabinet_label: 表格标题
        :param cabinet_type: 柜型 ("40HQ" 或 "20GP")
        """
        st.header(cabinet_label)
        if cabinets:
            for idx, cabinet in enumerate(cabinets, start=1):
                total_trays = sum(p["trays"] for p in cabinet)
                total_weight = sum(p["weight"] for p in cabinet)
                rounded_trays = math.ceil(total_trays)  # 向上取整托盘数

                with st.expander(
                        f"📦 {cabinet_type} {idx} \u2001 🧰 托盘数: {rounded_trays} \u2001 🛒 重量: {total_weight:.2f}kg"):
                    display_df = create_display_table(cabinet)
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info(f"🈚{no_cabinet_label}◽◽◽◽")

    def display_total_table(large_cabinets, small_cabinets):

        html_table = create_html_table(large_cabinets, small_cabinets)

        st.header("📦 总表")

        st.markdown(html_table, unsafe_allow_html=True)
        st_copy_to_clipboard(text=html_table, before_copy_label="🚚复制总表🚚", after_copy_label="✅复制成功")

    max_length = max(len(mutation_type) for mutation_type in stats['mutation_type_counts'].keys())

    st.markdown("""
        <style>
        .success-box-top {
            background-color: #E8F9EE;
            color: #1D7E64;
            padding: 5px;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            font-family: Arial, sans-serif;
        }
        .success-box-middle {
            background-color: #E8F9EE;
            color: #1D7E64;
            padding: 5px;
            font-family: Arial, sans-serif;
        }
        .success-box-bottom {
            background-color: #E8F9EE;
            color: #1D7E64;
            padding: 5px;
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
            font-family: Arial, sans-serif;
        }
        .center-text {
            text-align: center;

        }
        .left-right {
            display: flex;
            justify-content: space-between;

        }
        .left, .right {
            width: 26%;
        }
        .mutation-list {
            margin-top: 8px;

        }
        </style>
    """, unsafe_allow_html=True)

    # 模拟st.success的效果
    st.markdown(f"""
        <div class="success-box-top">
            <div class="center-text">
                <strong> ✅ 计算完成！ 🧐 </strong>
            </div>
        </div>

        <div class="success-box-middle">
            <div class="left-right">
                <div class="left">
                    🔄 本次迭代次数: {generations_run + 1} 次<br>
                    🧬 本次变异次数: {stats['total_mutations']} 次
                </div>
                <div class="right">
                    🔀 本次交叉次数: {stats['total_crossovers']} 次<br>
                    🏁 总锦标赛次数: {stats['total_tournaments']} 次
                </div>
            </div>
        </div>

        <div class="success-box-middle">
            <div class="center-text">
                🥇 本次运行中使用的变异类型分布:
                <div class="mutation-list">
                    {'<br>'.join([f"- {mutation_type.ljust(max_length)} : {count} 次" for mutation_type, count in stats['mutation_type_counts'].items()])}
                </div>
            </div>
        </div>

        <div class="success-box-middle">
            <div class="center-text">
                🏆 最终适应度为:<strong> {best_fitness:.4f} <br> </strong>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div class="success-box-bottom">
            <div class="left-right">
                <div class="left">
                    <strong>📦 大柜子数量: {len(large_containers)} 个<br> </strong>
                </div>
                <div class="right">
                    <strong>📦 小柜子数量: {len(small_containers)} 个<br> </strong>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)



    # 显示大柜子信息（原有展示）
    display_original_cabinets(large_containers, "📦 大柜子列表", "大柜子", "大柜子")

    st.divider()

    # 显示小柜子信息（原有展示）
    display_original_cabinets(small_containers, "📦 小柜子列表", "小柜子", "小柜子")

    st.divider()

    # 显示总表（新增展示）
    display_total_table(large_containers, small_containers)
