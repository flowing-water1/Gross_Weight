from html import escape
import streamlit_antd_components as sac
import streamlit as st
from original_data import For_Update_Original_data
import pandas as pd
import math
from st_copy_to_clipboard import st_copy_to_clipboard

import re


# 新增函数：用于提取采购单价中的数字和货币单位，并计算采购总价
def extract_price_and_calculate_total(price_str, quantity):
    """
    提取采购单价中的数字和货币单位，并计算采购总价。

    :param price_str: 采购单价字符串（例如 "USD 51.00" 或 "YUAN 51.00"）
    :param quantity: 数量
    :return: 采购总价和货币单位
    """
    # 正则表达式提取货币单位和数字部分
    match = re.match(r"([A-Za-z]+)\s*(\d+(\.\d{1,2})?)", price_str.strip())

    if match:
        currency = match.group(1)  # 提取货币单位
        price = float(match.group(2))  # 提取数字部分并转为浮动类型
        total_price = price * quantity  # 计算总价
        return f"{currency} {total_price:.2f}"  # 返回带货币单位的总价字符串
    else:
        return "Invalid Price"


def allocate_cabinets_to_types(solution, best_fitness, generations_run, stats,
                               if_start_messages,
                               post_progress_messages,
                               post_change_message,
                               extra_info_list
                               ):
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

    # 对数量、托盘数、总重量进行四舍五入
    def round_value(value, decimals=2):
        try:
            return round(float(value), decimals)
        except (ValueError, TypeError):
            return value  # 如果转换失败，返回原值

    def create_display_table(cabinet):
        """
        创建用于展示的产品信息表格，包含规格、净重、毛重。
        """
        display_data = []
        for product in cabinet:
            details = get_product_details(product)

            # 格式化毛重与重量，保留2位小数
            gross_weight_str = f"{round_value(details['毛重 (kg)']):.2f}"
            total_weight_str = f"{round_value(product.get('weight', 0)):.2f}"

            # 对托盘数也进行两位小数格式化显示
            trays_str = f"{round_value(product.get('trays', 0)):.2f}"

            display_data.append({
                "编号": product.get("产品编号"),
                "产品名称": product.get("name"),
                "规格": details["规格"],
                "数量": round_value(product.get("产品数量", 0)),  # 四舍五入数量
                "毛重 (kg)": gross_weight_str,
                "托盘数": trays_str,
                "总重量 (kg)": total_weight_str
            })
            st.write(display_data)
        return pd.DataFrame(display_data)

    def create_html_table(large_cabinets, small_cabinets, extra_info_list=None):
        """
        创建用于展示的所有柜子的HTML表格，包含合并单元格的“柜型”列。
        根据extra_info_list来动态调整列数
        """

        # 定义默认列顺序和顺序B
        default_columns = [
            "编号", "产品名称", "规格", "数量", "毛重 (kg)", "托盘数", "总重量 (kg)", "柜型"
        ]
        sequence_b_columns = [
            "编码", "供应商", "产品编码（SAP Product Code）", "SO/发票号（invoice）",
             "产品名称", "规格", "数量", "采购单价(Price)", "采购总价(TOTAL)",
            "毛重 (kg)", "托盘数", "总重量 (kg)", "柜型"
        ]


        # 根据是否有附加列来决定列顺序
        if extra_info_list and any(extra_info_list):  # 确保extra_info_list非空且有有效数据
            columns = sequence_b_columns
        else:
            columns = default_columns

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


        """
        # 创建标题行，根据列顺序来排列
        for column in columns:
            html += f"<th>{escape(column)}</th>"

        # 如果是9列数据，动态添加额外的列
        if extra_info_list:
            html += """


        </tr>
        </thead>
        <tbody>
            """
        # 如果是9列数据，动态添加额外的列
        if extra_info_list and any(extra_info_list):  # 检查是否有有效内容
            # 构建一个字典，以编号为键，extra_info_list的内容为值
            extra_info_dict = {}
            for info in extra_info_list:
                # 假设extra_info_list的每一行有"编码"字段
                if info:  # 仅当info非空时才添加到字典
                    extra_info_dict[info.get("编码")] = info

        def add_cabinets_to_html(cabinets, cabinet_type):
            nonlocal html
            for cabinet in cabinets:
                display_data = []
                for product in cabinet:
                    details = get_product_details(product)
                    gross_weight_str = f"{round_value(details['毛重 (kg)']):.2f}"
                    total_weight_str = f"{round_value(product.get('weight', 0)):.2f}"
                    trays_str = f"{round_value(product.get('trays', 0)):.2f}"

                    display_data.append({
                        "编号": product.get("产品编号"),
                        "产品名称": product.get("name"),
                        "规格": details["规格"],
                        "数量": round_value(product.get("产品数量", 0)),  # 四舍五入数量
                        "毛重 (kg)": gross_weight_str,
                        "托盘数": trays_str,
                        "总重量 (kg)": total_weight_str
                    })

                    # 如果有 extra_info_list，添加额外信息
                    if extra_info_list and any(extra_info_list):  # 仅在有效的extra_info_list时处理
                        product_code = product.get("产品编号")
                        # 获取extra_info_dict中的附加信息
                        extra_info = extra_info_dict.get(product_code, {})
                        display_data[-1].update(extra_info)

                num_products = len(display_data)
                for idx, row in enumerate(display_data):
                    html += "<tr>"
                    # 根据列顺序插入数据
                    for column in columns:
                        # 如果是“采购单价(Price)”列
                        if column == "采购单价(Price)" and extra_info_list:
                            price_str = row.get("采购单价(Price)", "")
                            html += f"<td>{escape(price_str)}</td>"

                        # 如果是“采购总价(TOTAL)”列
                        elif column == "采购总价(TOTAL)" and extra_info_list:
                            price_str = row.get("采购单价(Price)", "")
                            # 这里你可以直接用 row["数量"]，或者像你写的那样，用 product里的 "产品数量"
                            quantity = row.get("数量", 0)
                            if price_str and quantity:
                                # 改用你正确的数量

                                # st.info(f"正确数量: {quantity}")

                                total_price = extract_price_and_calculate_total(price_str, quantity)
                                # st.info(f"计算总价: {total_price}")

                                html += f"<td>{escape(total_price)}</td>"
                            else:
                                # 如果拿不到单价或数量，就留空
                                html += "<td></td>"

                        # 否则，如果这个列名正好在 row 中，就用默认逻辑
                        elif column in row:
                            html += f"<td>{escape(str(row[column]))}</td>"
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

    def display_total_table(large_cabinets, small_cabinets, extra_info_list):

        html_table = create_html_table(large_cabinets, small_cabinets, extra_info_list)

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
            width: 28%;
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

        <div class="success-box-middle">
            <div class="center-text">
                <strong> {if_start_messages} <br> </strong>
            </div>
        </div>

        <div class="success-box-middle">
            <div class="center-text">
                <strong> {post_progress_messages} <br> </strong>
            </div>
        </div>

        <div class="success-box-middle">
            <div class="center-text">
                <strong> {post_change_message} <br> </strong>
            </div>
        </div>

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
    display_total_table(large_containers, small_containers, extra_info_list)