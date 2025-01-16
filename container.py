import json
import random
import copy
from collections import defaultdict
import streamlit as st
import math

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


# 4.变异


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

        final_solution, if_start_messages, post_process_messages, post_change_message = post_process_solution(
            best_solution, config)

        # 计算后处理后的适应度
        final_fitness = calculate_fitness(final_solution, config)



        return final_solution, final_fitness, generation, stats, if_start_messages, post_process_messages, post_change_message
        # return best_solution, best_fitness, generation, stats, "if_start_messages", "post_process_messages", "post_change_message"


def post_process_solution(solution, config):
    """
    后处理：仅当有恰好两个小柜子时，尝试将小柜子的产品完全转移到大柜子中，
    或者通过新增一个大柜子来消除所有小柜子。

    :param solution: 当前解决方案（柜子列表）
    :param config: 配置参数字典
    :return: (优化后的解决方案, if_start_messages, post_process_messages, post_change_message)
    """
    # 分离大柜子和小柜子
    large_containers = []
    small_containers = []
    for cab in solution:
        total_trays = sum(p["trays"] for p in cab)
        total_weight = sum(p["weight"] for p in cab)
        if total_trays <= config["SMALL_MAX_TRAYS"] and total_weight <= config["SMALL_MAX_WEIGHT"]:
            small_containers.append(cab)
        else:
            large_containers.append(cab)

    num_big = len(large_containers)
    num_small = len(small_containers)

    if num_small != 2:
        # 仅在恰好有两个小柜子时启动后处理
        if_start_messages = f"🩺 当前小柜子数量为{num_small}个，不等于2个，无需启动后处理方案。"
        return solution, if_start_messages, "后处理未启动，无需优化。", ""
    else:
        # 计算所有小柜子的总托盘数和总重量
        total_small_trays = sum(p["trays"] for cab in small_containers for p in cab)
        total_small_weight = sum(p["weight"] for cab in small_containers for p in cab)

        # 计算所有大柜子的剩余容量
        total_remaining_trays = sum(config["MAX_TRAYS"] - sum(p["trays"] for p in cab) for cab in large_containers)
        total_remaining_weight = sum(config["MAX_WEIGHT"] - sum(p["weight"] for p in cab) for cab in large_containers)

        # 计算新增一个大柜子的容量
        additional_trays = config["MAX_TRAYS"]
        additional_weight = config["MAX_WEIGHT"]

        if (total_remaining_trays + additional_trays >= total_small_trays and
                total_remaining_weight + additional_weight >= total_small_weight):
            # 可行，新增一个大柜子
            if_start_messages = f"🩺 当前小柜子数量为{num_small}个，启动后处理方案，新增一个大柜子以消除所有小柜子。"

            # 将所有小柜子的产品汇总
            small_products = [p for cab in small_containers for p in cab]

            # 将"产品数量"转化为float，确保后续计算方便
            def to_float(x):
                if isinstance(x, str):
                    try:
                        return float(x)
                    except:
                        return 0.0
                elif isinstance(x, (int, float)):
                    return float(x)
                else:
                    return float(x) if x is not None else 0.0

            # 生成子产品列表
            subproducts = []
            for product in small_products:
                trays = product["trays"]
                per_tray_weight = product["每托重量"]
                product_quantity = to_float(product["产品数量"])  # 转为float方便计算
                total_trays = trays
                # 每托的产品数量
                if total_trays > 0:
                    quantity_per_tray = product_quantity / total_trays
                else:
                    # 若 total_trays == 0理应不存在这种情况，但以防万一
                    quantity_per_tray = product_quantity

                if trays < 1:
                    # fractional_subproduct
                    frac_sub = copy.deepcopy(product)
                    frac_sub["产品数量"] = quantity_per_tray * trays
                    # weight and trays remain the fractional
                    subproducts.append(frac_sub)
                else:
                    trays_int = math.floor(trays)
                    trays_frac = trays - trays_int
                    # 整数部分拆分为多个1托子产品
                    for _ in range(trays_int):
                        sub = copy.deepcopy(product)
                        sub["trays"] = 1
                        sub["weight"] = per_tray_weight
                        sub["产品数量"] = quantity_per_tray * 1
                        subproducts.append(sub)
                    # fractional部分
                    if trays_frac > 0:
                        frac_sub = copy.deepcopy(product)
                        frac_sub["trays"] = trays_frac
                        frac_sub["weight"] = trays_frac * per_tray_weight
                        frac_sub["产品数量"] = quantity_per_tray * trays_frac
                        subproducts.append(frac_sub)

            # 为大柜子添加剩余容量信息，包括新增的大柜子
            for cab in large_containers:
                cab_total_trays = sum(p["trays"] for p in cab)
                cab_total_weight = sum(p["weight"] for p in cab)
                cab_trays_left = config["MAX_TRAYS"] - cab_total_trays
                cab_weight_left = config["MAX_WEIGHT"] - cab_total_weight
                cab.append({"_remaining_trays": cab_trays_left, "_remaining_weight": cab_weight_left})

            # 新增一个大柜子
            new_cabinet = [{"_remaining_trays": config["MAX_TRAYS"], "_remaining_weight": config["MAX_WEIGHT"]}]
            large_containers.append(new_cabinet)

            def place_subproduct_in_existing_cabinets(sp, cabinets, config):
                for cab in cabinets:
                    cab_remain = cab[-1]
                    if cab_remain["_remaining_trays"] >= sp["trays"] and cab_remain["_remaining_weight"] >= sp[
                        "weight"]:
                        cab.insert(-1, sp)
                        cab_remain["_remaining_trays"] -= sp["trays"]
                        cab_remain["_remaining_weight"] -= sp["weight"]
                        return True
                return False

            leftover_subproducts = []
            for sp in subproducts:
                placed = place_subproduct_in_existing_cabinets(sp, large_containers, config)
                if not placed:
                    leftover_subproducts.append(sp)

            # 开新大柜子装载剩余子产品，直到全部放入
            while leftover_subproducts:
                new_cabinet = []
                new_cabinet.append(
                    {"_remaining_trays": config["MAX_TRAYS"], "_remaining_weight": config["MAX_WEIGHT"]})
                large_containers.append(new_cabinet)

                still_leftover = []
                for sp in leftover_subproducts:
                    placed = place_subproduct_in_existing_cabinets(sp, [new_cabinet], config)
                    if not placed:
                        still_leftover.append(sp)
                leftover_subproducts = still_leftover

                # 理论上如果有更多剩余，又再开下一个大柜子，如此循环，直到全部分完。

            # 清除容量信息字典
            for cab in large_containers:
                if len(cab) > 0 and "_remaining_trays" in cab[-1]:
                    cab.pop()

            # 合并同一柜子内相同(产品编号, name)的产品行
            final_large_containers = []
            for cab in large_containers:
                merged_cab = merge_cabinet_products(cab, config)
                final_large_containers.append(merged_cab)

            post_process_message = "🤖 后处理完成，成功优化小柜子数量。"

            # 将数字用红色显示
            # 使用span标签并指定inline样式覆盖父级颜色
            red_num_big = f"<span style='color:red;'>{num_big}</span>"
            red_num_small = f"<span style='color:red;'>{num_small}</span>"
            red_final = f"<span style='color:red;'>{len(final_large_containers)}</span>"

            post_change_message = f"🔨由{red_num_big}个大柜子 + {red_num_small}个小柜子 ➡ {red_final}个大柜子"

            return final_large_containers, if_start_messages, post_process_message, post_change_message
        else:
            # 不可行，跳过后处理
            if_start_messages = f"🩺 当前小柜子数量为{num_small}个，但即使新增大柜也无法达到消除全部小柜的目的"
            post_process_message = "🤖 后处理未执行，以避免增加成本。"
            post_change_message = "🤔 即使拆分小柜装入目前大柜 + 新增大柜也无法消解小柜，故保持原有柜子配置。"
            return solution, if_start_messages, post_process_message, post_change_message


def merge_cabinet_products(cab, config):
    """
    合并柜子内相同(产品编号, name)的产品行。

    :param cab: 柜子中的产品列表
    :param config: 配置参数字典
    :return: 合并后的产品列表
    """
    merged = {}
    for p in cab:
        key = (p["产品编号"], p["name"])
        if key not in merged:
            merged[key] = {
                "产品编号": p["产品编号"],
                "id": p["id"],
                "name": p["name"],
                "产品数量": to_float(p["产品数量"]),
                "每托重量": p["每托重量"],
                "trays": p["trays"],
                "weight": p["weight"]
            }
        else:
            merged[key]["产品数量"] += to_float(p["产品数量"])
            merged[key]["trays"] += p["trays"]
            merged[key]["weight"] += p["weight"]
    # 更新每托重量
    # 每托重量 = 总重量 / 总托盘数（若总托盘数>0，否则保持原值）
    final_products = []
    for v in merged.values():
        if v["trays"] > 0:
            v["每托重量"] = v["weight"] / v["trays"]
        else:
            # trays=0，不应该出现这种情况，但以防万一
            v["每托重量"] = v["weight"]
        final_products.append(v)
    return final_products


def to_float(x):
    if isinstance(x, str):
        try:
            return float(x)
        except:
            return 0.0
    elif isinstance(x, (int, float)):
        return float(x)
    else:
        return float(x) if x is not None else 0.0
