# split_pallets.py
import json
from decimal import Decimal, getcontext
from collections import defaultdict
import streamlit as st

# 设置高精度以确保计算准确
getcontext().prec = 10


def rename_keys(container_info):
    """
    将产品信息中的键替换为新的键名：
    - 对于名称唯一的产品，使用 "产品名称" 作为 "id"
    - 对于名称重复的产品，为其 "id" 添加唯一后缀
    - 保留 "产品名称" 作为 "name"
    - 替换 "托盘数" 为 "trays"
    - 替换 "单个产品总毛重" 为 "weight"
    - 新增 "single_pallet_weight" 对应 "每托重量"
    """
    # 统计每个产品名称的出现次数
    name_counts = defaultdict(int)
    for product in container_info:
        name = product.get("产品名称")
        name_counts[name] += 1

    # 记录每个重复名称已分配的数量
    name_indices = defaultdict(int)

    renamed_container_info = []

    for product in container_info:
        name = product.get("产品名称")
        if name_counts[name] > 1:
            # 有重复名称，添加后缀
            name_indices[name] += 1
            unique_id = f"{name}_{name_indices[name]}"
        else:
            # 唯一名称，直接使用名称作为ID
            unique_id = name

        renamed_product = {
            "产品编号": product.get("产品编号"),
            "id": unique_id,  # 唯一ID
            "name": name,  # 保留名称
            "产品数量": product.get("产品数量"),
            "每托重量": product.get("每托重量"),
            "trays": product.get("托盘数"),
            "weight": product.get("单个产品总毛重")
        }
        renamed_container_info.append(renamed_product)

    return renamed_container_info


def split_pallets_general(total_pallets, total_weight, target_weight, max_pallets_per_part, single_pallet_weight):
    """
    将总托数和总重量分配到多个部分，每部分尽量接近其目标重量，并满足最大托数限制。
    """
    single_pallet_weight = Decimal(single_pallet_weight)

    allocation = []
    remaining_pallets = Decimal(total_pallets)
    remaining_weight = Decimal(total_weight)
    part_index = 1

    while remaining_pallets > 0 and remaining_weight > 0:
        part_name = f"{part_index}"

        # 尝试计算当前部分分配的托数
        pallets = min(int((Decimal(target_weight) // single_pallet_weight)),
                      max_pallets_per_part,
                      int(remaining_pallets))

        # 如计算出的托数为0，则至少分配1托
        if pallets == 0:
            pallets = 1
            weight = single_pallet_weight
        else:
            weight = Decimal(pallets) * single_pallet_weight

        allocation.append({
            "part_name": part_name,
            "托盘数": pallets,
            "重量": float(weight)  # 转换回 float 类型用于结果输出
        })

        # 更新剩余托数和重量
        remaining_pallets -= pallets
        remaining_weight -= weight

        part_index += 1

    return allocation


def process_container_info(container_info):
    """
    处理原始container_info列表：
    1. 首先通过 rename_keys 统一键值和处理重复产品ID
    2. 对超过限制的产品进行拆分
    """
    # 首先重命名键并为重复的产品生成唯一ID
    container_info = rename_keys(container_info)

    container_info_new = []
    max_weight = Decimal('24500')
    max_pallets = 40

    for index, product in enumerate(container_info):
        # 类型检查
        if not isinstance(product, dict):
            raise TypeError(f"Expected a dictionary at index {index}, but got {type(product)}.")

        # 检查所需键
        required_keys = ['产品编号', 'id', 'name', '产品数量', '每托重量', 'trays', 'weight']
        for key in required_keys:
            if key not in product:
                raise KeyError(f"Missing key '{key}' in product at index {index}: {product}")

        product_id = product['id']
        product_name = product['name']
        product_quantity = product['产品数量']
        single_pallet_weight = product['每托重量']
        total_pallets = product['trays']
        total_weight = product['weight']

        # 检查托盘数和重量是否超过限制
        if total_pallets > max_pallets or total_weight > float(max_weight):
            # 拆分产品
            split_result = split_pallets_general(
                total_pallets,
                total_weight,
                max_weight,
                max_pallets,
                single_pallet_weight
            )

            # 将拆分后的部分加入新的container_info_new
            for part in split_result:
                part_id = f"{product_id}_Part{part['part_name']}"
                part_name = f"{product_name} - Part {part['part_name']}"
                container_info_new.append({
                    '产品编号': product['产品编号'],
                    'id': part_id,
                    'name': part_name,
                    '产品数量': product_quantity,
                    '每托重量': float(single_pallet_weight),  # 转换为 float
                    'trays': part['托盘数'],
                    'weight': part['重量']
                })
        else:
            # 如果没有超过限制，直接加入新的列表，并转换 '每托重量' 为 float
            container_info_new.append({
                '产品编号': product['产品编号'],
                'id': product['id'],
                'name': product['name'],
                '产品数量': product_quantity,
                '每托重量': float(product['每托重量']),  # 转换为 float
                'trays': product['trays'],
                'weight': product['weight']
            })


    return container_info_new
