from decimal import Decimal
from constants import PACKAGE_TO_PALLETS
import streamlit as st


def calculate_total_weight_for_sidebar(product_names, quantities, cleaned_product_specifications_names,
                                       matched_product_weights, matched_product_codes):
    total_weight = Decimal(0)

    for i in range(len(matched_product_weights)):
        quantity = Decimal(quantities[i])
        spec = int(cleaned_product_specifications_names[i])
        matched_weight = Decimal(matched_product_weights[i])

        pallets_per_package = Decimal(PACKAGE_TO_PALLETS.get(spec, 1))
        tray_count = quantity / pallets_per_package
        single_product_weight = quantity * matched_weight + tray_count * Decimal(17)

        print(f"产品名字：{product_names[i]}:")
        print(f"  产品编号（金蝶云）：{matched_product_codes[i]}")
        print(f"  产品 {i + 1}:")
        print(f"  数量: {quantity}")
        print(f"  规格: {spec}")
        print(f"  毛重（单件）: {matched_weight:.3f} KG")
        print(f"  托盘数: {tray_count:.2f}")
        print(f"  产品总毛重: {quantity} * {matched_weight:.3f} + {tray_count} * 17 = {single_product_weight:.3f} KG\n")
        st.info(
            f"产品名字：{product_names[i]}  \n托盘计算：{quantity} / {pallets_per_package}={tray_count}  \n\
            产品总毛重: {quantity} * {matched_weight:.3f} + {tray_count} * 17 = {single_product_weight:.3f} KG")
        total_weight += single_product_weight

    return total_weight


def calculate_total_weight(product_names, quantities, cleaned_product_specifications_names,
                           matched_product_weights, matched_product_codes):
    total_weight = Decimal(0)
    container_info = []
    calculation_details = []  # 新增，用于存储展示用的信息字符串

    for i in range(len(matched_product_weights)):
        product_codes = matched_product_codes[i]
        quantity = Decimal(quantities[i])
        spec = int(cleaned_product_specifications_names[i])
        matched_weight = Decimal(matched_product_weights[i])
        pallets_per_package = Decimal(PACKAGE_TO_PALLETS.get(spec, 1))
        tray_count = quantity / pallets_per_package
        single_product_weight = quantity * matched_weight + tray_count * Decimal(17)
        weight_per_package = pallets_per_package * matched_weight + 17

        detail_str = (
            f"产品名字：{product_names[i]}  \n"
            f"托盘计算：{quantity} / {pallets_per_package}={tray_count}  \n"
            f"产品总毛重: {quantity} * {matched_weight:.3f} + {tray_count} * 17 = {single_product_weight:.3f} KG"
        )
        calculation_details.append(detail_str)
        total_weight += single_product_weight

        container_info.append({
            "产品编号": product_codes,
            "产品名称": product_names[i],
            "产品数量": quantity,
            "每托重量": weight_per_package,
            "托盘数": tray_count,
            "单个产品总毛重": single_product_weight
        })

    return total_weight, container_info, calculation_details
