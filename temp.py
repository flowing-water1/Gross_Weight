import json
import random
import copy

import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

from original_data import For_Update_Original_data

config = {
    "MAX_TRAYS": 40,
    "MAX_WEIGHT": 24500,
    "SMALL_MAX_TRAYS": 20,
    "SMALL_MAX_WEIGHT": 21000,
    "COST_SMALL": 1500,
    "COST_LARGE": 2500,
    "WEIGHT_UTILIZATION_WEIGHT": 0.6,
    "COST_WEIGHT": 0.2,
    "MUTATION_RATE": 0.8,
    "POPULATION_SIZE": 25,
    "NUM_GENERATIONS": 50,
    "MUTATION_RATE_BASE": 0.8,
    "MUTATION_RATE_MIN": 0.2,
    "TOURNAMENT_SIZE": 3,
    "ELITISM": True,

}


# 1.初代方案生成（目前只使用贪心算法）


def generate_initial_population(products, population_size=10):
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
    return greedy_allocate(shuffled_products)


def sort_by_weight_desc_greedy(products):
    """
    按重量降序排序产品后使用贪心策略生成解决方案。

    :param products: 产品列表。
    :return: 解决方案（柜子列表）。
    """
    sorted_products = sorted(products, key=lambda p: p["weight"], reverse=True)
    return greedy_allocate(sorted_products)


def sort_by_trays_desc_greedy(products):
    """
    按托盘数降序排序产品后使用贪心策略生成解决方案。

    :param products: 产品列表。
    :return: 解决方案（柜子列表）。
    """
    sorted_products = sorted(products, key=lambda p: p["trays"], reverse=True)
    return greedy_allocate(sorted_products)


def sort_by_ratio_desc_greedy(products):
    """
    按托盘数与重量的比率降序排序产品后使用贪心策略生成解决方案。

    :param products: 产品列表。
    :return: 解决方案（柜子列表）。
    """
    # 比率可以根据具体需求调整，这里以托盘数/重量作为比率
    sorted_products = sorted(products, key=lambda p: (p["trays"] / p["weight"]), reverse=True)
    return greedy_allocate(sorted_products)


def greedy_allocate(sorted_products):
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
                products_in_cabinet.append(product)
                trays_left -= product["trays"]
                weight_left -= product["weight"]
                remaining_products.remove(product)

        if products_in_cabinet:
            current_cabinets.append(products_in_cabinet)
        else:
            # 如果没有产品符合条件，可能有产品超过柜子限制
            # 将最重或托盘数最多的产品单独放入一个柜子
            product = remaining_products.pop(0)
            current_cabinets.append([product])

    return current_cabinets


# # 生成初始种群
# initial_population = generate_initial_population(products, population_size=10)

# # 打印初始种群
# for idx, solution in enumerate(initial_population, start=1):
#     print(f"方案 {idx}:")
#     for cabinet_idx, cabinet in enumerate(solution, start=1):
#         total_trays = sum(p["trays"] for p in cabinet)
#         total_weight = sum(p["weight"] for p in cabinet)
#         print(f"  柜子 {cabinet_idx}: 托盘数: {total_trays}, 重量: {total_weight}kg")
#         for product in cabinet:
#             print(f"    产品 {product['id']}, 托盘数: {product['trays']}, 重量: {product['weight']}kg")
#     print("\n")


# 2.适应度
def calculate_fitness(solution, config):
    total_cost = 0.0
    total_weight_utilization = 0.0
    over_capacity_penalty = 0.0

    for cabinet in solution:
        total_trays = sum(p["trays"] for p in cabinet)
        total_weight = sum(p["weight"] for p in cabinet)

        # 判断使用大柜子还是小柜子
        if total_trays <= config["SMALL_MAX_TRAYS"] and total_weight <= config["SMALL_MAX_WEIGHT"]:
            # 使用小柜子
            cabinet_cost = config["COST_SMALL"]
            max_trays = config["SMALL_MAX_TRAYS"]
            max_weight = config["SMALL_MAX_WEIGHT"]
        else:
            # 使用大柜子
            cabinet_cost = config["COST_LARGE"]
            max_trays = config["MAX_TRAYS"]
            max_weight = config["MAX_WEIGHT"]

            # 如果超过大柜子的限制，增加惩罚
            if total_trays > max_trays or total_weight > max_weight:
                tray_overflow = max(0, total_trays - max_trays) / max_trays
                weight_overflow = max(0, total_weight - max_weight) / max_weight
                over_capacity_penalty += (tray_overflow + weight_overflow) * 10  # 惩罚系数可调整

        total_cost += cabinet_cost

        # 计算重量利用率（使用平方，强调高利用率）
        weight_utilization = (total_weight / max_weight) ** 2
        total_weight_utilization += weight_utilization

    # 计算平均重量利用率
    avg_weight_utilization = total_weight_utilization / len(solution)

    # 为了最小化成本，我们在适应度函数中对成本取负值
    fitness = (avg_weight_utilization * config["WEIGHT_UTILIZATION_WEIGHT"]) - (
            total_cost / (len(solution) * config["COST_LARGE"]) * config["COST_WEIGHT"])

    # 总适应度 = 适应度 - 超过限制的惩罚
    total_fitness = fitness - over_capacity_penalty

    return total_fitness


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


def pmx_crossover(parent1, parent2, products):
    # 将方案转换为产品到柜子的映射
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
def perform_crossover(population, fitness_values, products, num_offspring=5):
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
        child1, child2 = pmx_crossover(parent1, parent2, products)

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


def mutate(solution, mutation_rate, config):
    """
    对给定的解决方案应用变异操作，包括 'swap', 'move', 'merge', 'split' 四种类型。
    每种变异操作尽量保持解决方案的有效性，减少修复需求。

    :param solution: 当前的解决方案（柜子列表）
    :param mutation_rate: 变异发生的概率
    :return: 变异后的解决方案
    """
    mutated_solution = copy.deepcopy(solution)
    mutation_performed = 0  # 初始化为未进行变异

    if random.random() < mutation_rate:
        mutation_type = random.choice(['swap', 'move', 'merge', 'split', 'reallocate', 'adjust'])

        if mutation_type == 'swap':
            # 获取所有产品
            all_products = [p for cabinet in mutated_solution for p in cabinet]

            # 随机选择两个不同的产品
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

                # 判断交换后是否仍在限制内
                if ((new_trays1 <= config["MAX_TRAYS"] and new_weight1 <= config["MAX_WEIGHT"]) and
                        (new_trays2 <= config["MAX_TRAYS"] and new_weight2 <= config["MAX_WEIGHT"])):
                    # 执行交换
                    cabinet1.remove(product1)
                    cabinet2.remove(product2)
                    cabinet1.append(product2)
                    cabinet2.append(product1)

        elif mutation_type == 'move':
            # 获取所有产品
            all_products = [p for cabinet in mutated_solution for p in cabinet]

            if len(all_products) >= 1:
                # 随机选择一个产品
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

        elif mutation_type == 'merge':
            # 尝试合并两个随机选择的柜子
            if len(mutated_solution) >= 2:
                cabinet1_idx, cabinet2_idx = random.sample(range(len(mutated_solution)), 2)
                cabinet1 = mutated_solution[cabinet1_idx]
                cabinet2 = mutated_solution[cabinet2_idx]

                # 检查合并后的柜子是否满足限制
                combined_trays = sum(p["trays"] for p in cabinet1 + cabinet2)
                combined_weight = sum(p["weight"] for p in cabinet1 + cabinet2)

                if combined_trays <= config["MAX_TRAYS"] and combined_weight <= config["MAX_WEIGHT"]:
                    # 合并柜子
                    mutated_solution[cabinet1_idx] = cabinet1 + cabinet2
                    # 删除第二个柜子
                    mutated_solution.pop(cabinet2_idx)

        elif mutation_type == 'split':
            # 尝试将一个柜子拆分为两个
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


        elif mutation_type == 'reallocate':
            # 随机选择几个产品并重新分配
            num_reallocations = random.randint(1, 3)
            products = [p for cabinet in mutated_solution for p in cabinet]
            if len(products) >= num_reallocations:
                selected_products = random.sample(products, num_reallocations)
                for product in selected_products:
                    from_cabinet_idx = next(idx for idx, cabinet in enumerate(mutated_solution) if product in cabinet)
                    mutated_solution[from_cabinet_idx].remove(product)

                    # 找到合适的柜子
                    feasible_cabinets = [idx for idx, cabinet in enumerate(mutated_solution)
                                         if
                                         sum(p["trays"] for p in cabinet) + product["trays"] <= config["MAX_TRAYS"] and
                                         sum(p["weight"] for p in cabinet) + product["weight"] <= config["MAX_WEIGHT"]]
                    if feasible_cabinets:
                        target_idx = random.choice(feasible_cabinets)
                        mutated_solution[target_idx].append(product)
                    else:
                        # 创建新柜子
                        mutated_solution.append([product])

        elif mutation_type == 'adjust':
            # 微调柜子中的产品
            cabinet_idx = random.randint(0, len(mutated_solution) - 1)
            cabinet = mutated_solution[cabinet_idx]
            if len(cabinet) > 1:
                product = random.choice(cabinet)
                cabinet.remove(product)

                feasible_cabinets = [idx for idx, c in enumerate(mutated_solution)
                                     if sum(p["trays"] for p in c) + product["trays"] <= config["MAX_TRAYS"] and
                                     sum(p["weight"] for p in c) + product["weight"] <= config["MAX_WEIGHT"]]
                if feasible_cabinets:
                    target_idx = random.choice(feasible_cabinets)
                    mutated_solution[target_idx].append(product)
                else:
                    # 创建新柜子
                    mutated_solution.append([product])

        mutation_performed = 1  # 标记为进行了变异

        # 修复柜子
        mutated_solution = fix_cabinets(mutated_solution)

    return mutated_solution, mutation_performed


def fix_cabinets(solution):
    new_solution = []
    overflow_products = []

    for cabinet in solution:
        total_trays = sum(p["trays"] for p in cabinet)
        total_weight = sum(p["weight"] for p in cabinet)

        # 判断是否超过大柜子的限制
        if total_trays > config["MAX_TRAYS"] or total_weight > config["MAX_WEIGHT"]:
            overflow_products.extend(cabinet)
        else:
            new_solution.append(cabinet)

    # 处理溢出产品
    for product in overflow_products:
        placed = False
        # 尝试放入已有的柜子
        for cabinet in new_solution:
            total_trays = sum(p["trays"] for p in cabinet)
            total_weight = sum(p["weight"] for p in cabinet)

            # 确定当前柜子的限制
            if total_trays <= config["SMALL_MAX_TRAYS"] and total_weight <= config["SMALL_MAX_WEIGHT"]:
                max_trays = config["SMALL_MAX_TRAYS"]
                max_weight = config["SMALL_MAX_WEIGHT"]
            else:
                max_trays = config["MAX_TRAYS"]
                max_weight = config["MAX_WEIGHT"]

            if total_trays + product["trays"] <= max_trays and total_weight + product["weight"] <= max_weight:
                cabinet.append(product)
                placed = True
                break

        # 如果无法放入已有的柜子，创建新柜子
        if not placed:
            new_solution.append([product])

    return new_solution


def apply_mutation(population, mutation_rate):
    """
    对种群中的每个解决方案应用变异操作，并统计总的变异次数。

    :param population: 当前种群列表
    :param mutation_rate: 变异发生的概率
    :return: (变异后的种群, 总变异次数)
    """
    mutated_population = []
    total_mutations = 0
    for solution in population:
        mutated_solution, mutation = mutate(solution, mutation_rate, config)
        mutated_population.append(mutated_solution)
        total_mutations += mutation
    return mutated_population, total_mutations


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
from st_copy_to_clipboard import st_copy_to_clipboard


def tournament_selection(population, fitness_values, tournament_size):
    selected = []
    for _ in range(len(population)):
        # 随机选择 tournament_size 个体
        participants = random.sample(list(zip(population, fitness_values)), tournament_size)
        # 选择适应度最高的个体
        winner = max(participants, key=lambda x: x[1])
        selected.append(winner[0])
    return selected


# 初始化种群
def run_genetic_algorithm(products, config):
    population = generate_initial_population(products, config["POPULATION_SIZE"])

    # 初始化变异计数
    total_mutations = 0

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
    for generation in range(config["NUM_GENERATIONS"]):
        print(f"第 {generation + 1} 代:")

        # 评估适应度
        fitness_values = [calculate_fitness(solution, config) for solution in population]

        # 输出当前种群的最高适应度
        max_fitness = max(fitness_values)
        print(f"  当前最高适应度: {max_fitness:.4f}")

        # 精英保留
        if config["ELITISM"]:
            elite_index = fitness_values.index(max_fitness)
            elite_individual = population[elite_index]

        # 选择
        selected_population = tournament_selection(population, fitness_values, config["TOURNAMENT_SIZE"])

        # 交叉
        # 交叉
        offspring = []
        for i in range(0, len(selected_population), 2):
            parent1 = selected_population[i]
            parent2 = selected_population[(i + 1) % len(selected_population)]
            child1, child2 = pmx_crossover(parent1, parent2, products)
            offspring.append(child1)
            offspring.append(child2)

        # 确保种群规模一致
        if len(offspring) > config["POPULATION_SIZE"]:
            offspring = offspring[:config["POPULATION_SIZE"]]

        # 变异
        mutated_offspring, mutations = apply_mutation(offspring, config["MUTATION_RATE"])
        total_mutations += mutations

        # 修复并评估适应度
        population = mutated_offspring
        fitness_values = [calculate_fitness(solution, config) for solution in population]

        # 精英保留
        if config["ELITISM"]:
            # 替换适应度最低的个体
            min_fitness = min(fitness_values)
            min_index = fitness_values.index(min_fitness)
            population[min_index] = elite_individual
            fitness_values[min_index] = calculate_fitness(elite_individual, config)

        # 检查收敛条件（可选）
        # 如果在若干代内适应度未显著提升，可以提前终止迭代

        # 迭代结束后，找到适应度最高的方案
        fitness_values = [calculate_fitness(solution, config) for solution in population]
        best_fitness = max(fitness_values)
        best_solution_index = fitness_values.index(best_fitness)
        best_solution = population[best_solution_index]

        print("\n最优方案:")
        print(f"适应度: {best_fitness:.4f}")
        for cabinet_idx, cabinet in enumerate(best_solution, start=1):
            total_trays = sum(p["trays"] for p in cabinet)
            total_weight = sum(p["weight"] for p in cabinet)
            print(f"  柜子 {cabinet_idx}: 托盘数: {total_trays}, 重量: {total_weight}kg")
            for product in cabinet:
                print(f"    产品 {product['id']}, 托盘数: {product['trays']}, 重量: {product['weight']}kg")
            print()

        return best_solution, best_fitness, config["NUM_GENERATIONS"], total_mutations


import math

from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

from collections import defaultdict

import math

from html import escape


def allocate_cabinets_to_types(solution, small_container_limit_trays=20, small_container_limit_weight=21000):
    """
    将分配出的柜子分类为大柜子和小柜子，并基于产品名称查询规格、净重、毛重。

    :param solution: 最优方案中的柜子列表
    :param small_container_limit_trays: 小柜子的托盘数限制
    :param small_container_limit_weight: 小柜子的重量限制（kg）
    :return: 大柜子列表和小柜子列表
    """
    large_containers = []
    small_containers = []

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

    # 显示大柜子信息（原有展示）
    display_original_cabinets(large_containers, "📦 大柜子列表", "大柜子", "大柜子")

    st.divider()

    # 显示小柜子信息（原有展示）
    display_original_cabinets(small_containers, "📦 小柜子列表", "小柜子", "小柜子")

    st.divider()

    # 显示总表（新增展示）
    display_total_table(large_containers, small_containers)
