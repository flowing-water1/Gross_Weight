from decimal import Decimal
from constants import PACKAGE_TO_PALLETS
import streamlit as st
from constants import get_package_to_pallets


def calculate_total_weight_for_sidebar(product_names, quantities, cleaned_product_specifications_names,
                                       matched_product_weights, matched_product_codes, is_hk=False):
    total_weight = Decimal(0)

    # 根据 is_hk 决定选择哪种 pallets 映射
    package_to_pallets = get_package_to_pallets(is_hk)

    for i in range(len(matched_product_weights)):
        quantity = Decimal(quantities[i])
        spec = int(cleaned_product_specifications_names[i])
        matched_weight = Decimal(matched_product_weights[i])

        pallets_per_package = Decimal(package_to_pallets.get(spec, 1))
        tray_count = quantity / pallets_per_package
        single_product_weight = quantity * matched_weight + tray_count * Decimal(17)

        # 使用 st.markdown 模拟 st.info
        st.markdown(f"""
            <div class="custom-info">
                产品名字：<br>{product_names[i]}  <br>
                托盘计算：{quantity} / {pallets_per_package}={tray_count:.1f}  <br>
                产品总毛重:<br>
    {quantity} * {matched_weight:.1f} + {tray_count:.1f} * 17 = {single_product_weight:.1f} KG  <br>
            </div>
        """, unsafe_allow_html=True)


        total_weight += single_product_weight

    return total_weight


def calculate_total_weight(product_names, quantities, cleaned_product_specifications_names,
                           matched_product_weights, matched_product_codes,
    is_hk=False):

    total_weight = Decimal(0)
    container_info = []
    calculation_details = []  # 新增，用于存储展示用的信息字符串

    # 同样，先获取 pallets 映射
    package_to_pallets = get_package_to_pallets(is_hk)

    for i in range(len(matched_product_weights)):
        product_codes = matched_product_codes[i]
        quantity = Decimal(quantities[i])
        spec = int(cleaned_product_specifications_names[i])
        matched_weight = Decimal(matched_product_weights[i])

        pallets_per_package = Decimal(package_to_pallets.get(spec, 1))
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
