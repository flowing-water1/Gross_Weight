from html import escape
import streamlit_antd_components as sac
import streamlit as st
from original_data import For_Update_Original_data
import pandas as pd
import math
from st_copy_to_clipboard import st_copy_to_clipboard



def allocate_cabinets_to_types(solution, best_fitness, generations_run, stats,
                               if_start_messages,
                               post_progress_messages,
                                post_change_message,
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

    def create_display_table(cabinet):
        """
        创建用于展示的产品信息表格，包含规格、净重、毛重。
        """
        display_data = []
        for product in cabinet:
            details = get_product_details(product)
            # 格式化毛重与重量，保留2位小数
            try:
                gross_weight_str = f"{float(details['毛重 (kg)']):.2f}"
            except (ValueError, TypeError):
                gross_weight_str = details['毛重 (kg)']

            try:
                total_weight_str = f"{float(product.get('weight', 0)):.2f}"
            except (ValueError, TypeError):
                total_weight_str = product.get('weight', '未知')

            # 对托盘数也进行两位小数格式化显示
            try:
                trays_value = float(product.get("trays", 0))
                trays_str = f"{trays_value:.2f}"
            except (ValueError, TypeError):
                trays_str = product.get("trays", "未知")

            display_data.append({
                "编号": product.get("产品编号"),
                "产品名称": product.get("name"),
                "规格": details["规格"],
                "数量": product.get("产品数量"),
                "毛重 (kg)": gross_weight_str,
                "托盘数": trays_str,
                "总重量 (kg)": total_weight_str
            })
        return pd.DataFrame(display_data)

    def create_html_table(large_cabinets, small_cabinets):
        """
        创建用于展示的所有柜子的HTML表格，包含合并单元格的“柜型”列。
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
                    # 格式化毛重与重量
                    try:
                        gross_weight_str = f"{float(details['毛重 (kg)']):.2f}"
                    except (ValueError, TypeError):
                        gross_weight_str = details['毛重 (kg)']

                    try:
                        total_weight_str = f"{float(product.get('weight', 0)):.2f}"
                    except (ValueError, TypeError):
                        total_weight_str = product.get('weight', '未知')

                    # 托盘数保留2位小数
                    try:
                        trays_value = float(product.get("trays", 0))
                        trays_str = f"{trays_value:.2f}"
                    except (ValueError, TypeError):
                        trays_str = product.get("trays", "未知")

                    display_data.append({
                        "编号": product.get("产品编号"),
                        "产品名称": product.get("name"),
                        "规格": details["规格"],
                        "数量": product.get("产品数量"),
                        "毛重 (kg)": gross_weight_str,
                        "托盘数": trays_str,
                        "总重量 (kg)": total_weight_str
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
                🩺<strong> {if_start_messages} <br> </strong>
            </div>
        </div>

        <div class="success-box-middle">
            <div class="center-text">
                🤖<strong> {post_progress_messages} <br> </strong>
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
    display_total_table(large_containers, small_containers)