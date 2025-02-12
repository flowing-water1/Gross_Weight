import copy
import json
import os
import pandas as pd
import streamlit as st
import streamlit_antd_components as sac

from constants import PACKAGE_TO_PALLETS
from container import run_genetic_algorithm, config
from container_display import allocate_cabinets_to_types
from weight_calculation import calculate_total_weight, calculate_total_weight_for_sidebar
from data_extraction import extract_product_and_quantity
from data_cleaning import clean_product_name, clean_product_specifications
from matching import find_best_match, find_best_match_by_code
from original_data import For_Update_Original_data
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from st_copy_to_clipboard import st_copy_to_clipboard
from st_on_hover_tabs import on_hover_tabs  # 导入 st_on_hover_tabs 控件
from update_notes import show_update_dialog
import streamlit_nested_layout
from split_pallets import process_container_info

import streamlit_toggle_diy as tog
import base64
import requests
from io import StringIO
from tutorials import image_tutorial, text_tutorials, question_tutorials, side_bar_tutorials

# Streamlit App Setup
st.set_page_config(layout="wide", initial_sidebar_state='collapsed')
title_col1, title_col2, title_col3 = st.columns([0.38, 1.1, 0.3])
with title_col2:
    title_help = "👻由流水开发，目前版本：{updates['version']}👻"
    st.title("🚚产品重量统计与柜重计算🚢", help=title_help)

# 初始化变量，确保它们在任何情况下都被定义
uploaded_image = None
table_text = ""

# 初始化 session_state
if "toggle_status" not in st.session_state:
    st.session_state["toggle_status"] = False

# 初始化 session_state 中的按钮状态
if "show_button_cabinet" not in st.session_state:
    st.session_state.show_button_cabinet = False

# 初始化 session_state 中的额外状态位
if "cabinet_mode" not in st.session_state:
    st.session_state["cabinet_mode"] = False  # 控制柜重计算对话框打开时的状态

if "region_toggle" not in st.session_state:
    st.session_state["region_toggle"] = False


def reset_calculation_states():
    keys_to_reset = ["calc_done", "container_info", "total_weight", "calculation_details"]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]


# 显示更新日志对话框，仅在首次加载时显示
if "update_dialog_shown" not in st.session_state:
    # show_update_dialog()
    st.session_state.update_dialog_shown = True





@st.dialog("🚚\u2003柜数计算\u2003🚚", width="large")
def cabinet(container_info):
    # best_solution, best_fitness = run_genetic_algorithm(container_info, config)
    # st.write(container_info)
    best_solution, best_fitness, generations_run, stats, if_start_messages, post_progress_messages,post_change_message = run_genetic_algorithm(container_info, config)

    allocate_cabinets_to_types(best_solution,
                               best_fitness,
                               generations_run,
                               stats,
                               if_start_messages,
                               post_progress_messages,
                               post_change_message,
                               extra_info_list)

# 加载自定义 CSS
with open("style.css", encoding="utf-8") as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


@st.fragment
def toggle_fragment():

    # 动态更新 label 文本
    label_text = "🔖 输入名称 🔖" if not st.session_state["toggle_status"] else "🧬 输入编码 🧬"

    # 切换控件
    toggle_status = tog.st_toggle_switch(
        key="input_toggle",
        label_end=label_text,  # 不显示后标签
        justify='flex-start',
        default_value=False,
        inactive_color='#cee8ff',  # 使用 --bg-300: #374357 作为未激活颜色
        active_color="#00668c",  # 使用 --accent-100: #3D5A80 作为激活颜色
        track_color="#acc2ef",  # 使用 --primary-200: #4d648d 作为轨道颜色
        label_bg_color_start='#0F1C2E',
        label_bg_color_end=None,
        background_color_near_button_start='#0F1C2E',  # 使用 --primary-200: #4d648d
        background_color_near_button_end='#1F3A5F',  # 使用 --primary-100: #1F3A5F
        border_radius='8px',
        label_start_color="blue",  # 前标签文字颜色（深灰色）
        label_end_color="white",  # 后标签文字颜色（深灰色）
        label_font_size="16px",  # 标签字体大小
        label_font_weight="bold",  # 标签字体粗细
        switch_size="medium",  # Switch 尺寸
    )

    # 检测切换状态并更新，不需要刷新整个页面
    if toggle_status != st.session_state["toggle_status"]:
        st.session_state["toggle_status"] = toggle_status
        st.rerun()

@st.fragment
def region_toggle_fragment():
    """
    根据切换状态展示不同的标签，比如: 香港模式 / 欧洲模式
    将值存储在 st.session_state["region_toggle"] 里
    """
    # 获取当前区域模式
    current_val = st.session_state["region_toggle"]
    label_text = "香港模式" if current_val else "欧洲模式"

    # 传入自定义参数，优化视觉效果
    toggle_status = tog.st_toggle_switch(
        key="region_toggle_key",
        label_start=None,          # 不显示前标签
        label_end=label_text,      # 显示后标签
        justify="flex-left",          # 标签与开关居中对齐
        default_value=current_val, # 当前状态

        # ========== 优化后的配色 ==========
        inactive_color="#B0BEC5",    # 未激活状态：蓝灰色
        active_color="#1976D2",      # 激活状态：深蓝色
        track_color="#90CAF9",       # 轨道颜色：浅蓝色
        label_bg_color_start="#BBDEFB",  # 标签背景起始色：浅蓝色
        label_bg_color_end="#64B5F6",    # 标签背景结束色：中蓝色
        background_color_near_button_start="#BBDEFB",  # 开关附近背景起始色：非常浅蓝色
        background_color_near_button_end="#FFFFFF",    # 开关附近背景结束色：浅蓝色
        border_radius="20px",       # 圆角：20px

        # 标签文字样式
        label_start_color="#333333", # 前标签文字颜色：深灰色
        label_end_color="#333333",   # 后标签文字颜色：深灰色
        label_font_size="18px",      # 标签字体大小：18px
        label_font_weight="bold",    # 标签字体粗细：加粗

        switch_size="medium",        # Switch 尺寸：中等
    )

    # 检测是否发生了切换
    if toggle_status != current_val:
        st.session_state["region_toggle"] = toggle_status
        # 为了让标签在一次点击后就立刻更新，需要强制重跑
        st.rerun()



    # 检测是否发生了切换
    if toggle_status != current_val:
        st.session_state["region_toggle"] = toggle_status
        # 为了让标签在一次点击后就立刻更新，需要强制重跑
        st.rerun()


# 侧边栏简易功能
with st.sidebar:
    tabs = on_hover_tabs(
        tabName=['简易匹配工具'],
        iconName=['🚴'],  # 使用适当的图标
        default_choice=0,
        styles={'navtab': {'background-color': '#0F1C2E',
                           'color': 'white',
                           'font-size': '20px',
},
                },
    )

    if tabs == '简易匹配工具':
        # 将所有内容包装在一个具有特定类名的容器中，方便CSS控制显示与隐藏
        st.markdown('<div class="sidebar-content">', unsafe_allow_html=True)

        # 包装 toggle_fragment 在一个额外的 div 中，以便更好地控制
        toggle_fragment()

        if not st.session_state["toggle_status"]:  # False 表示输入名称
            sidebar_product_name = st.text_input("🔖 输入产品名称", key="name_input")
            sidebar_product_code = st.text_input("🧬 输入产品编码", disabled=True, key="code_input")
        else:  # True 表示输入编码
            sidebar_product_name = st.text_input("🔖 输入产品名称", disabled=True, key="name_input_disabled")
            sidebar_product_code = st.text_input("🧬 输入产品编码", key="code_input")

        sidebar_quantity = st.number_input("🛒 输入数量", min_value=0, step=1)

        if (sidebar_product_name or sidebar_product_code) and sidebar_quantity > 0:
            # 清洗产品名称或编码
            cleaned_name = clean_product_name(sidebar_product_name) if sidebar_product_name else None
            cleaned_code = sidebar_product_code.strip() if sidebar_product_code else None

            # 从匹配文件中读取产品数据
            matching_file_path = 'cleaned_data.xlsx'  # 需要在同一目录下提供该文件
            df = pd.read_excel(matching_file_path, sheet_name='境外贸易商品名称')

            product_names = df['型号'].dropna().astype(str).tolist()
            original_product_names = df['型号'].dropna().astype(str).tolist()  # 假设这个列表包含原始未清洗的名称
            product_weights = df['毛重（箱/桶）'].dropna().astype(float).tolist()
            product_codes = df['产品编码(金蝶云)'].dropna().astype(str).tolist()

            # 匹配产品
            if cleaned_name:
                match_result = find_best_match(
                    cleaned_name,
                    product_names,
                    product_weights,
                    product_codes,
                )
            elif cleaned_code:
                match_result = find_best_match_by_code(
                    cleaned_code,
                    product_codes,
                    product_weights,
                    product_names,
                    original_product_names,
                )
            best_match = match_result["best_match"]
            all_matches = match_result["all_matches"]

            if best_match["similarity"] < 99:
                # 提供前 5 个匹配项供选择
                options = [
                    f"编号：{match['code']} | 产品名称： {For_Update_Original_data.loc[For_Update_Original_data['产品编号（金蝶云）'] == match['code'].strip(), '产品名称'].values[0]} | 相似度: {match['similarity']:.2f} | 毛重: {match['weight']:.2f} KG"
                    for match in all_matches
                ]

                user_selection = st.selectbox(
                    "选择最佳匹配项",
                    options,
                    index=0,
                    key="sidebar_selection"
                )

                # 使用产品编号匹配
                original_product_name = user_selection.split("|")[1].strip().replace("产品名称：", "").strip()
                selected_product_code = user_selection.split("|")[0].strip().replace("编号：", "").strip()
                selected_match = next(
                    (match for match in all_matches if match["code"].strip() == selected_product_code), None
                )

                if selected_match:
                    product_spec = For_Update_Original_data.loc[
                        For_Update_Original_data['产品编号（金蝶云）'] == selected_match['code'].strip(), '产品规格'].values[0]
                    cleaned_spec = clean_product_specifications(product_spec)  # 清洗规格

                    region_is_hk = st.session_state.get("region_toggle", False)

                    # 计算总毛重（假设函数已定义）
                    total_weight = calculate_total_weight_for_sidebar(
                        product_names=[original_product_name],  # 使用原始产品名称
                        quantities=[sidebar_quantity],
                        cleaned_product_specifications_names=[cleaned_spec],  # 传入清洗后的规格
                        matched_product_weights=[selected_match['weight']],
                        matched_product_codes=[selected_match['code']],
                        is_hk=region_is_hk
                    )

                    # 条件渲染自定义提示框
                    st.markdown(f"""
                        <div class="custom-info">
                            产品名字：{original_product_name}  <br>
                            产品编码：{selected_match['code']}  <br>
                            产品规格：{product_spec}  <br>
                            毛重：{selected_match['weight']:.2f} KG
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                        <div class="custom-success">
                            总毛重: {total_weight:.2f} KG
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    # 条件渲染自定义警告框
                    st.markdown(f"""
                        <div class="custom-warning">
                            未找到符合条件的匹配项，请检查数据或重新选择。
                        </div>
                    """, unsafe_allow_html=True)
            else:
                # 使用未清洗的产品名称来展示最佳匹配
                original_best_product_name = For_Update_Original_data.loc[
                    For_Update_Original_data['产品编号（金蝶云）'] == best_match['code'].strip(), '产品名称'].values[0]
                product_spec = For_Update_Original_data.loc[
                    For_Update_Original_data['产品编号（金蝶云）'] == best_match['code'].strip(), '产品规格'].values[0]
                cleaned_spec = clean_product_specifications(product_spec)  # 清洗规格

                region_is_hk = st.session_state.get("region_toggle", False)

                # 计算总毛重（假设函数已定义）
                total_weight = calculate_total_weight_for_sidebar(
                    product_names=[original_best_product_name],  # 使用原始产品名称
                    quantities=[sidebar_quantity],
                    cleaned_product_specifications_names=[cleaned_spec],  # 传入清洗后的规格
                    matched_product_weights=[best_match['weight']],
                    matched_product_codes=[best_match['code']],
                    is_hk=region_is_hk

                )

                # 条件渲染自定义提示框

                st.markdown(f"""
                    <div class="custom-info">
                        最佳匹配项名称：<br>{original_best_product_name}  <br>
                        最佳匹配项编码：{best_match['code']}  <br>
                        产品规格：{product_spec}  <br>
                        毛重：{best_match['weight']:.2f} KG
                    </div>
                """, unsafe_allow_html=True)

                st.markdown(f"""
                    <div class="custom-success">
                        总毛重: {total_weight:.2f} KG
                    </div>
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
if "last_upload_method" not in st.session_state:
    st.session_state["last_upload_method"] = None

method_col, mid_empty_col, region_col = st.columns([2, 1.5,1])
with region_col:
    # 放置我们的区域切换
    region_toggle_fragment()
with method_col:
    upload_method = st.radio("🗿请选择上传方式🗿", ("📷图片上传📷", "✍粘贴文本✍"))


# 在模式切换后重置状态的通用逻辑函数
def reset_states_on_method_change():
    # 如果上传方式发生变化，则调用 reset_calculation_states 以及清空相关 session_state
    if st.session_state["last_upload_method"] is not None and st.session_state["last_upload_method"] != upload_method:
        reset_calculation_states()

    # 更新上一次选择的模式
    st.session_state["last_upload_method"] = upload_method


# 调用该函数，使其根据模式变化进行清理
reset_states_on_method_change()

if upload_method == "📷图片上传📷":

    if 'calc_done' not in st.session_state:
        reset_calculation_states()
    # 当进入图片上传模式时，清空文本模式的数据
    if 'ocr_result_df_text' in st.session_state:
        del st.session_state['ocr_result_df_text']



    # 同时清空用户选择的记录
    if 'user_selection_flag' in st.session_state:
        del st.session_state['user_selection_flag']

    if 'user_previous_selection' in st.session_state:
        del st.session_state['user_previous_selection']

    # 上传图片
    uploaded_image = st.file_uploader("上传产品图片📷", type=["png", "jpg", "jpeg"])

    if uploaded_image:
        # 清空旧的表格数据，确保上传新的数据时可以更新

        # 初始化 session_state 变量
        if 'previous_uploaded_file_name' not in st.session_state:
            st.session_state['previous_uploaded_file_name'] = uploaded_image.name

        # 如果上传了新的文件，与之前的文件不同，则清空 session_state 中除 `previous_uploaded_file_name` 以外的数据
        if st.session_state['previous_uploaded_file_name'] != uploaded_image.name:
            # 保留原始的文件名以避免被清除
            previous_uploaded_file_name = st.session_state['previous_uploaded_file_name']
            # 清空所有 session_state，重新设置 `previous_uploaded_file_name`
            # 重置计算相关状态
            reset_calculation_states()
            # st.session_state.clear()

            # 如果你想重新识别，那么你可以把保存有 OCR 结果的键删掉，但不删 display_df
            if 'ocr_result_df_image' in st.session_state:
                del st.session_state['ocr_result_df_image']
            if 'display_df' in st.session_state:
                del st.session_state['display_df']

            st.session_state['previous_uploaded_file_name'] = previous_uploaded_file_name
            st.session_state['previous_uploaded_file_name'] = uploaded_image.name

        # st.session_state 中不存在 'ocr_result_df_image' 这个键（也就是说还没有 OCR 结果）。
        # 也就是首次运行、页面刷新后的首次上传或上传了新图片时才执行 OCR 操作。
        if 'ocr_result_df_image' not in st.session_state:
            st.toast(f"🧐你上传的图片文件是: {uploaded_image.name}")

            # 使用 NamedTemporaryFile 保存上传的文件
            original_file_name = os.path.splitext(uploaded_image.name)[0]
            standardized_filename = f"{original_file_name}_uploaded.png"
            temp_file_path = os.path.join(".", standardized_filename)
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(uploaded_image.read())

            # OCR 处理部分（使用服务端 API 替换本地模型）
            st.toast("🤔正在进行表格识别◽◽◽◽")

            try:
                # 对本地图像进行 Base64 编码
                with open(temp_file_path, "rb") as file:
                    image_bytes = file.read()
                    if not image_bytes:
                        st.error("🤨读取的图像数据为空！")
                    image_data = base64.b64encode(image_bytes).decode("ascii")

                # 调用 API
                API_URL = "https://api123.1127107.xyz/table-recognition"
                payload = {"image": image_data}

                response = requests.post(API_URL, json=payload, timeout=30)

                if response.status_code == 200:
                    result = response.json().get("result", {})
                    if not result:
                        st.error("🤨API 返回的数据为空或格式不正确。")

                    # 保存 OCR 和布局图像
                    result_dir = os.path.join(os.path.dirname(temp_file_path), "out")
                    os.makedirs(result_dir, exist_ok=True)
                    base_filename = os.path.splitext(os.path.basename(temp_file_path))[0]

                    ocr_image_path = os.path.join(result_dir, f"{base_filename}_ocr.jpg")
                    layout_image_path = os.path.join(result_dir, f"{base_filename}_layout.jpg")
                    with open(ocr_image_path, "wb") as file:
                        file.write(base64.b64decode(result.get("ocrImage", "")))
                    with open(layout_image_path, "wb") as file:
                        file.write(base64.b64decode(result.get("layoutImage", "")))

                    # 提取表格数据并保存为 Excel
                    tables = result.get("tables", [])
                    xlsx_file_path = os.path.join(result_dir, f"{base_filename}.xlsx")
                    if tables:
                        with pd.ExcelWriter(xlsx_file_path) as writer:
                            for idx, table in enumerate(tables):
                                html_content = table.get("html", "")
                                dfs = pd.read_html(StringIO(html_content))
                                if dfs:
                                    df = dfs[0]
                                    sheet_name = "Sheet"
                                    # 打印表格数据及目标文件路径
                                    df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                        # 更新 session_state
                        ocr_result_df = pd.read_excel(xlsx_file_path, header=None)
                        ocr_result_df.columns = ["产品名称", "产品规格", "数量"]
                        st.session_state['ocr_result_df_image'] = ocr_result_df
                        st.session_state['image_files'] = [layout_image_path, ocr_image_path]
                        st.session_state['xlsx_file_path'] = xlsx_file_path
                        ocr_result_original_df = ocr_result_df.copy()
                        st.session_state['ocr_result_original_df'] = ocr_result_original_df
                    else:
                        st.warning("OCR 识别失败，请重试。")
                elif response.status_code == 502:
                    st.error("🤨无法连接到本地服务。请确保本地服务已启动，并且可通过内网穿透访问。")

                else:
                    st.error(f"🤨API 调用失败，状态码: {response.status_code}")
                    with st.expander("详细报错信息"):
                        st.error(f"{response.text}")

            except Exception as e:
                # 捕获请求异常并提示服务端未启动
                st.error("🤨无法连接到服务端。请确保服务端已启动并且可以访问。")
                st.error(f"🤨详细错误信息：{str(e)}")

elif upload_method == "✍粘贴文本✍":

    table_text = st.text_area("请输入表格文本✍", value=st.session_state.get("last_confirmed_data", ""))

    if 'calc_done' not in st.session_state:
        reset_calculation_states()

    if 'ocr_result_df_image' in st.session_state:
        del st.session_state['ocr_result_df_image']

    if 'display_df' in st.session_state:
        del st.session_state['display_df']

    # 清空与用户选择相关的状态
    if 'user_selection_flag' in st.session_state:
        del st.session_state['user_selection_flag']

    if 'user_previous_selection' in st.session_state:
        del st.session_state['user_previous_selection']

    if table_text:
        # 清空旧的表格数据，确保上传新的数据时可以更新
        if 'ocr_result_df_text' in st.session_state:
            del st.session_state['ocr_result_df_text']
        if 'table_uploaded' in st.session_state:
            del st.session_state['table_uploaded']
        if 'ocr_result_original_df' in st.session_state:
            del st.session_state['ocr_result_original_df']
        if 'display_df' in st.session_state:
            del st.session_state['display_df']

        # 对比当前输入的表格文本与之前确认的数据
        previously_confirmed_data = st.session_state.get("last_confirmed_data", None)
        # 如果还没calc_done或者（已calc_done但数据与last_confirmed_data不一致），则判定为新数据
        is_really_new_data = (previously_confirmed_data is None) or (table_text != previously_confirmed_data)

        # 只有在确定之前（calc_done=False）或者在calc_done为True但数据确实发生了变化时才执行reset
        if is_really_new_data:
            reset_calculation_states()
            st.session_state['data_changed'] = True
        else:
            st.session_state['data_changed'] = False

            # 将新的数据标记为上传完成
            st.session_state['data_changed'] = True

        if st.session_state['data_changed']:
            # st.info(f"st.session_state['cabinet_mode']:{st.session_state['cabinet_mode']}")
            # if 'cabinet_mode' in st.session_state:

            # 将粘贴的表格文本按行分割，并按 tab 进行拆分
            table_lines = table_text.split("\n")
            data = [line.split("\t") for line in table_lines if line.strip()]  # 过滤掉空行

            # 将数据转换为 DataFrame
            ocr_result_df = pd.DataFrame(data)

            # 为生成的 Excel 文件指定路径
            result_dir = os.path.join(".", "out")  # 可以根据需要修改路径
            os.makedirs(result_dir, exist_ok=True)
            base_filename = "uploaded_table"
            xlsx_file_path = os.path.join(result_dir, f"{base_filename}.xlsx")

            # 将 DataFrame 保存为 Excel 文件
            with pd.ExcelWriter(xlsx_file_path) as writer:
                ocr_result_df.to_excel(writer, sheet_name="Sheet", index=False, header=False)
                # 提示用户表格已成功上传

            # 只在首次成功上传时显示
            st.toast("🧐表格已成功上传并保存为 Excel 文件！")

            # 更新 session_state
            ocr_result_df = pd.read_excel(xlsx_file_path, header=None)
            num_cols = ocr_result_df.shape[1]  # 实际列数
            if num_cols == 3:
                # 旧格式 —— 只有3列：产品名称 / 产品规格 / 数量
                ocr_result_df.columns = ["产品名称", "产品规格", "数量"]

            elif num_cols == 9:
                # 新格式 —— 9列：编码 / 供应商 / 产品编码… / 规格型号(Product) / 包装(Packing) / 数量(Quantity) / 采购单价 / 采购总价
                # 提取需要的列并重新命名
                ocr_result_df = ocr_result_df.iloc[:, [4, 5, 6]]  # 提取第5, 6, 7列
                ocr_result_df.columns = ["产品名称", "产品规格", "数量"]

            else:
                # 如果列数不为3列或9列，给出警告
                st.warning(f"⚠ 该文件有 {num_cols} 列，不是预期的3列或9列，暂未支持自动匹配。")
                st.stop()  # 停止执行，避免后面流程报错
            st.session_state['ocr_result_df_text'] = ocr_result_df
            st.session_state['xlsx_file_path'] = xlsx_file_path
            st.session_state['table_uploaded'] = True  # 标记表格已上传

            # 备份原始数据以便后续使用
            ocr_result_original_df = ocr_result_df.copy()
            st.session_state['ocr_result_original_df'] = ocr_result_original_df

            # 处理完成后数据改变状态设为False
            st.session_state['data_changed'] = False

# 从 session_state 中读取 OCR 结果
if 'ocr_result_df_text' in st.session_state or 'ocr_result_df_image' in st.session_state:
    if upload_method == "📷图片上传📷":
        if uploaded_image:
            st.image(uploaded_image, caption='上传的图片', use_container_width=True)
            ocr_result_df = st.session_state['ocr_result_df_image']
            image_files = st.session_state.get('image_files', [])
            xlsx_file_path = st.session_state['xlsx_file_path']
            ocr_result_original_df = st.session_state['ocr_result_original_df']

            # 展示识别的图片
            expander = st.expander("📸OCR 识别的图片结果：")
            for image_file in image_files:
                if os.path.exists(image_file):
                    expander.image(image_file, caption=f"识别结果: {os.path.basename(image_file)}",
                                   use_container_width=True)

            # 从 session_state 中读取 OCR 结果
            markdown_col1, markdown_col2, markdown_col3 = st.columns([1.3, 1, 1])
            with markdown_col2:
                st.markdown(f"""
                ### 📸OCR 识别结果📸
                **文件名:** `{uploaded_image.name}`
                """, unsafe_allow_html=True)

    if upload_method == "✍粘贴文本✍":
        ocr_result_df = st.session_state['ocr_result_df_text']
        xlsx_file_path = st.session_state['xlsx_file_path']
        ocr_result_original_df = st.session_state['ocr_result_original_df']

        # 展示生成的表格
        markdown_col1, markdown_col2, markdown_col3 = st.columns([1.3, 1, 1])
        with markdown_col2:
            st.markdown(f"""
            ### 📄处理结果📄
            **文件名:** `uploaded_table.xlsx`
            """, unsafe_allow_html=True)

    # 只是为了展示的表格而已，不会因为状态变更而改变，一开始什么样就是什么样
    # 因为if 'display_df' not in st.session_state:约束了只有第一次才会诞生
    # 之后display_df都在session_state里了，就算rerun也不会进入下面的代码中
    if 'display_df' not in st.session_state:
        st.session_state['display_df'] = ocr_result_df.copy()
        st.session_state['display_df'].index = st.session_state['display_df'].index + 1

    dataframe_col1, dataframe_col2 = st.columns([0.5, 1])
    with dataframe_col2:
        st.dataframe(st.session_state['display_df'])

    # 提取数据
    original_product_names, specifications, quantities, extra_info_list= extract_product_and_quantity(xlsx_file_path)
    # st.write(extra_info_list)

    # 清洗数据
    cleaned_product_names = [clean_product_name(name) for name in original_product_names]
    cleaned_product_specifications_names = [clean_product_specifications(spec) for spec in specifications]

    # 如果有 extra_info_list（新格式），使用编码匹配
    if extra_info_list and any(extra_info_list):
        # 提取编码进行精确匹配
        product_codes_for_query = [item["编码"] for item in extra_info_list]  # 提取“编码”字段
        matched_product_names = []
        matched_product_weights = []
        matched_product_codes = []  # 确保这个列表是空的，准备存储所有的匹配结果

        # 从匹配文件中读取产品数据
        matching_file_path = 'cleaned_data.xlsx'  # 需要在同一目录下提供该文件
        df = pd.read_excel(matching_file_path, sheet_name='境外贸易商品名称')

        product_names = df['型号'].dropna().astype(str).tolist()
        original_product_names = df['型号'].dropna().astype(str).tolist()  # 假设这个列表包含原始未清洗的名称
        product_weights = df['毛重（箱/桶）'].dropna().astype(float).tolist()
        product_codes = df['产品编码(金蝶云)'].dropna().astype(str).tolist()

        # 匹配逻辑
        for idx, code in enumerate(product_codes_for_query):
            match_result = find_best_match_by_code(code, product_codes, product_weights, product_names, original_product_names)

            best_match = match_result["best_match"]
            matched_product_names.append(best_match["name"])
            matched_product_weights.append(best_match["weight"])

            # 这里确保每次都把当前匹配的编码添加到列表中
            matched_product_codes.append(best_match["code"])  # 每次都添加新的编码

        # st.write(product_codes)
        # 更新结果
        # st.write(matched_product_codes)
        # st.write(matched_product_weights)
        ocr_result_df.insert(0, "产品编号(金蝶云)", matched_product_codes)
        ocr_result_df["毛重"] = matched_product_weights
        
    else:

        # 读取匹配产品的Excel文件
        matching_file_path = 'cleaned_data.xlsx'  # 需要在同一目录下提供该文件
        df = pd.read_excel(matching_file_path, sheet_name='境外贸易商品名称')

        product_names = df['型号'].dropna().astype(str).tolist()
        product_weights = df['毛重（箱/桶）'].dropna().astype(float).tolist()
        product_codes = df['产品编码(金蝶云)'].dropna().astype(str).tolist()

        # 匹配产品
        matched_product_names = []
        matched_product_weights = []
        matched_product_codes = []

        # 临时存储用户选择的结果
        # 在初次加载时，所有选择的标志位（user_selection_flag）为 False，
        # 并且 user_previous_selection 为 None，确保初次加载时不触发任何用户提示。
        if 'user_selection_flag' not in st.session_state:
            # 初始化每个选择项的标志为 False，表示用户尚未进行选择
            st.session_state['user_selection_flag'] = [False] * len(cleaned_product_names)

        if 'user_previous_selection' not in st.session_state:
            st.session_state['user_previous_selection'] = [None] * len(cleaned_product_names)

        # 临时存储用户选择的结果
        user_selected_products = {}
        with st.expander("📇选择最佳匹配项📇"):
            for idx, cleaned_name in enumerate(cleaned_product_names):
                # print(f"Loop idx: {idx}, Current selection: {st.session_state['user_previous_selection'][idx]}")

                filtered_indices = ocr_result_original_df.index[
                    ocr_result_original_df["产品名称"] == original_product_names[idx]].tolist()

                if len(filtered_indices) == 0:
                    st.warning(f"找不到与产品名称 '{original_product_names[idx]}' 相匹配的行，请检查数据。")
                    continue
                else:
                    original_row_index = filtered_indices[0]

                # 查找逻辑是先在clean_data.xlsx中用名称匹配找（find_best_match传入的都是cleaned.xlsx里面的数据）
                # 找到了以后，用code匹配在original_data.xlsx中找对应的各条目（For_Update_Original_data）
                match_result = find_best_match(
                    cleaned_name,
                    product_names,
                    product_weights,
                    product_codes,
                )

                best_match = match_result["best_match"]
                all_matches = match_result["all_matches"]

                if best_match["similarity"] < 99:
                    # 查找 cleaned_name 对应的原始产品名称
                    original_name = For_Update_Original_data.loc[
                        For_Update_Original_data["产品编号（金蝶云）"] == best_match["code"], "产品名称"].values[0]

                    # warning_message = (
                    #     f"🔽 表格{original_row_index + 1} 行： 产品：{original_product_names[idx]} 🔽"
                    #     f"对应的最佳匹配项为： 产品 '{original_name}'，"
                    #     f"相似度为 {best_match['similarity']:.2f} \n\n🔽 可能需要手动选择匹配项 🔽"
                    # ).replace("*", "\\*")  # 转义所有的 *
                    #
                    # st.warning(warning_message)


                    warning_html = f"""
                    <div style="
                        background-color: #fffce7; 
                        color: #926c05;
                        font-family: 微软雅黑, sans-serif;
                        padding: 15px;
                        font-size: 15.5px;
                        border-radius: 10px;
                        margin-top: 10px;
                        margin-bottom: 20px;
                        border-left: 5px solid #ffd966;  /* 左侧色条 */
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                    ">
                        <table style="
                            border-collapse: collapse; 
                            border: none; 
                            margin: 0 auto;      /* 表格整体居中 */
                            table-layout: fixed; 
                            width: 100%;
                            max-width: 600px;    /* 根据需要调整最大宽度 */
                        ">
                            <!-- 第一行 -->
                            <tr style="border: none;">
                                <td style="
                                    text-align: center; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    🔽
                                </td>
                                <td style="
                                    text-align: right; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    表格 {original_row_index + 1} 行：
                                </td>
                                <td style="
                                    text-align: left; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    <b>{original_product_names[idx]}</b>
                                </td>
                                <td style="
                                    text-align: center; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    🔽
                                </td>
                            </tr>
                            <!-- 第二行 -->
                            <tr style="border: none;">
                                <td style="
                                    text-align: center; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    🔽
                                </td>
                                <td style="
                                    text-align: right; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    对应的最佳匹配项为：
                                </td>
                                <td style="
                                    text-align: left; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    <b>{original_name}</b>， 相似度为 {best_match['similarity']:.2f}
                                </td>
                                <td style="
                                    text-align: center; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    🔽
                                </td>
                            </tr>
                            <!-- 第三行 -->
                            <tr style="border: none;">
                                <td style="
                                    text-align: center; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    🔽
                                </td>
                                <td colspan="2" style="
                                    text-align: center; 
                                    white-space: nowrap;
                                    padding: 1px 5px 0 5px;
                                    border: none;
                                ">
                                    可能需要手动选择匹配项
                                </td>
                                <td style="
                                    text-align: center; 
                                    vertical-align: top;
                                    white-space: nowrap;
                                    padding: 0 5px;
                                    border: none;
                                ">
                                    🔽
                                </td>
                            </tr>
                        </table>
                    </div>
                    """

                    # 使用 st.markdown 输出自定义的 HTML
                    st.markdown(warning_html, unsafe_allow_html=True)

                    # 提供前 5 个匹配项供选择
                    options = [
                        f"编号：{match['code']} | 产品名称： {For_Update_Original_data.loc[For_Update_Original_data['产品编号（金蝶云）'] == match['code'].strip(), '产品名称'].values[0]} | 相似度: {match['similarity']} | 毛重: {match['weight']} ".replace(
                            " | ", "\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0")
                        for match in all_matches
                    ]

                    # 默认值为第一个选项
                    default_option = options[0]

                    user_selection = st.selectbox(
                        "",
                        options,
                        index=0,
                        key=f"selection_{idx}",
                        label_visibility="collapsed"
                    )
                    # 使用新的分隔符来拆分选项字符串
                    split_separator = "\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0"
                    selected_product_code = user_selection.split(split_separator)[0].strip()  # 产品编号在选项的最前面

                    # 如果前缀是 "编号："（注意这里的全角符号）
                    if selected_product_code.startswith("编号："):
                        selected_product_code = selected_product_code[len("编号："):].strip()

                    # 使用产品编号匹配而不是名称匹配
                    selected_match = next(
                        (match for match in all_matches if match["code"].strip() == selected_product_code.strip()), None)

                    if selected_match is None:
                        st.warning("未找到符合条件的匹配项，请检查数据或重新选择。")
                        # 不匹配，解决这里的问题，大概率是因为格式不同，所以搜索不到。
                    else:
                        # 更新匹配结果
                        matched_product_names.append(selected_match["name"])
                        matched_product_weights.append(selected_match["weight"])
                        matched_product_codes.append(selected_match["code"])

                        # 存储用户选择结果
                        user_selected_products[cleaned_name] = selected_match
                        # """
                        # 为什么一开始不会出现st.toast呢？让我们来分析这个问题。
                        # 在一开始初始化的时候，为每一个产品名的user_selection_flag都设置为了False，user_previous_selection都是None
                        # 注意，这是为每一个产品名都赋值了
                        # Initialized user_selection_flag:
                        #  [False, False, False, False, False, False, False]
                        # Initialized user_previous_selection:
                        #  [None, None, None, None, None, None, None, None]
                        #  那比如有2个选项，2,4相似度是低于99的，那么其实我们就有两个选项会被处理。
                        #  一开始因为user_selection没被选，但是user_previous_selection是None，所以我们无论如何都会过一遍这里的代码
                        #  好，巧妙的点来了，这是利用了状态更新的滞后性来达到“初始化的时候”不会出现toast
                        #  经过了2的时候，一开始是不会进入 if user_selection_flag的，因为都是False，但是因为这里是会诞生user_selection的
                        #  （因为select_box会默认选择第一项的原因，也就是user_previous_selection都被设置为了select_box的默认值
                        #  但是由于第一次每次检测user_selection_flag都会是False，所以不会进入判断）
                        #  经过2之后，2的user_selection_flag被设定了True，但是！
                        #  但是巧妙的点来了，下一次是3了，就跳过了这次判断！。
                        #  所以整体流程是这样的
                        #  最开始：
                        # Initialized user_selection_flag:
                        #  [False, False, False, False, False, False, False]
                        # Initialized user_previous_selection:
                        #  [None, None, None, None, None, None, None, None]
                        #  经过第一次初始化遍历之后：
                        # Initialized user_selection_flag:
                        #  [False, False, True, False, True, False, False]
                        # Initialized user_previous_selection:
                        #  [None, None, 123, None, 456, None, None, None]
                        #
                        #  好，那么下次选择变更的时候，都是[idx]的user_previous_selection，此时起主要判断关键的，是的user_previous_selection
                        #  因为st.session_state['user_selection_flag'][idx]在第一次设置之后，2,4都是True了
                        #  所以只要是的user_previous_selection对应的[idx]发生变更，就会触发toast。
                        #  比如说我对2选择了别的选项，那么2的user_previous_selection变更了，变更之后会再进入for循环的，这时到轮转到第2个的时候
                        #  就发现此时的st.session_state['user_previous_selection'][idx] != user_selection，那么就会触发toast了
                        # """
                        # 没有这个的话每个匹配项都会展示一次toast
                        if st.session_state['user_previous_selection'][idx] != user_selection:

                            if st.session_state['user_selection_flag'][idx]:
                                # 仅在用户手动更改选项后显示 toast
                                print(f"now_idx:{idx}")
                                st.toast("已手动选择匹配项")

                            # 更新选择标志和上一次选择值
                            st.session_state['user_selection_flag'][idx] = True
                            print(f"Updated user_selection_flag for idx {idx}: {st.session_state['user_selection_flag']}")
                            st.session_state['user_previous_selection'][idx] = user_selection
                            print(
                                f"Updated user_previous_selection for idx {idx}: {st.session_state['user_previous_selection']}")



                else:
                    # 如果相似度 >= 99，直接使用最佳匹配
                    matched_product_names.append(best_match["name"])
                    matched_product_weights.append(best_match["weight"])
                    matched_product_codes.append(best_match["code"])

    # 当你使用 ocr_result_df.insert() 方法插入一个新列时，如果这个列已经存在于 ocr_result_df 中，会抛出一个 ValueError 错误，因为 insert()
    # 方法要求插入的列是新的且不存在的。

    # 在首次运行脚本时插入列是没有问题的，但是当用户进行交互，页面重新加载时，代码会再次尝试插入这些列，而此时这些列已经存在，这就会导致错误或者产生预期外的行为。

    if "产品编号(金蝶云)" in ocr_result_df.columns:
        ocr_result_df["产品编号(金蝶云)"] = matched_product_codes
    else:

        ocr_result_df.insert(0, "产品编号(金蝶云)", matched_product_codes)

    ocr_result_df["毛重"] = matched_product_weights

    # 下面这个更新（选项）是为了每次创建AgGrid时，能够被刷新到，不是修改编号变化（这个问题暂时没有解决）
    # 更新 ocr_result_df 表格
    for idx, row in ocr_result_df.iterrows():
        user_input_id = row["产品编号(金蝶云)"]  # 获取产品编号
        if user_input_id in For_Update_Original_data["产品编号（金蝶云）"].values:
            # 查找 `For_Update_Original_data` 中匹配的行
            correct_row = \
                For_Update_Original_data[For_Update_Original_data["产品编号（金蝶云）"] == user_input_id].iloc[0]
            # 更新 "产品名称"、"产品规格" 和 "毛重" 列
            ocr_result_df.at[idx, "产品名称"] = correct_row["产品名称"]
            ocr_result_df.at[idx, "产品规格"] = correct_row["产品规格"]
            ocr_result_df.at[idx, "毛重"] = correct_row["毛重（箱/桶）"]

    # 假设 ocr_result_df 是你的原始 DataFrame
    ocr_result_df.reset_index(drop=True, inplace=True)  # 重置索引并丢弃旧的索引列
    ocr_result_df['行'] = ocr_result_df.index + 1  # 添加一列新的行，从 1 开始

    # 将“行号”列放在第一列
    ocr_result_df = ocr_result_df[['行'] + [col for col in ocr_result_df.columns if col != '行']]

    gb = GridOptionsBuilder.from_dataframe(ocr_result_df)
    gb.configure_grid_options(domLayout='normal')

    gb.configure_column("产品编号(金蝶云)", editable=True)  # 使产品编号可编辑
    gb.configure_column("毛重", editable=True)
    gb.configure_column("产品规格", editable=True)
    gb.configure_column("数量", editable=True)  # 使数量列可编辑

    gb.configure_default_column(min_column_width=100)
    grid_options = gb.build()

    col1, col2 = st.columns(2)

    with col1:
        # 显示 AgGrid 表格并捕获用户修改
        modify_table_markdown_col1, modify_table_markdown_col2, modify_table_markdown_col3 = st.columns(
            [0.75, 1, 0.5])
        with modify_table_markdown_col2:
            st.markdown(f"""
                        ### 修改的表格✍
                        """, unsafe_allow_html=True)
        response = AgGrid(
            ocr_result_df,
            gridOptions=grid_options,
            editable=True,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            theme="alpine",
            fit_columns_on_grid_load=True
        )

        # 获取用户修改后的数据
        edited_df = pd.DataFrame(response['data'])

        # 将修改后的数据保存到 session_state 中，以便在页面刷新时保留
        st.session_state['edited_ocr_result_df'] = edited_df

    # 使用新的变量名 `updated_ocr_df` 保存修改后的数据
    if 'edited_ocr_result_df' in st.session_state:
        updated_ocr_df = st.session_state['edited_ocr_result_df']
    else:
        updated_ocr_df = edited_df

    # 下面这个是为了在AgGrid中修改数据能在“确定表格”中有所修改
    # 实时检测和部分列替换
    for index, row in edited_df.iterrows():
        user_input_id = row["产品编号(金蝶云)"]  # 只检测“产品编号”列
        if user_input_id in For_Update_Original_data["产品编号（金蝶云）"].values:
            # 查找在 cleaned_data 中匹配的行
            correct_row = \
                For_Update_Original_data[For_Update_Original_data["产品编号（金蝶云）"] == user_input_id].iloc[0]
            # 更新 "产品名称" 和 "产品规格" 列
            updated_ocr_df.at[index, "产品名称"] = correct_row["产品名称"]
            updated_ocr_df.at[index, "产品规格"] = correct_row["产品规格"]
            updated_ocr_df.at[index, "毛重"] = correct_row["毛重（箱/桶）"]

    # 显示更新后的 AgGrid 表格

    with col2:
        determine_table_markdown_col1, determine_table_markdown_col2, determine_table_markdown_col3 = st.columns(
            [0.75, 1, 0.5])
        with determine_table_markdown_col2:
            st.markdown(f"""
                        ### 确定的表格🔏
                        """, unsafe_allow_html=True)
        st.dataframe(updated_ocr_df, hide_index=True)



if 'edited_ocr_result_df' in st.session_state:
    updated_ocr_df = st.session_state['edited_ocr_result_df']

    if (uploaded_image is not None) or (table_text.strip() != ""):

        if st.button("💻确定计算💻"):

            # region_is_hk 即为 toggle 状态
            region_is_hk = st.session_state.get("region_toggle", False)

            # 检查编辑后的 DataFrame 是否存在
            # 提取更新后的数据
            updated_product_names = updated_ocr_df["产品名称"].tolist()
            updated_quantities = updated_ocr_df["数量"].tolist()
            updated_specifications = updated_ocr_df["产品规格"].tolist()

            # 清洗产品规格数据
            cleaned_updated_specifications_names = [clean_product_specifications(spec) for spec in
                                                    updated_specifications]

            # 提取毛重和产品编号
            updated_weights = updated_ocr_df["毛重"].tolist()
            updated_codes = updated_ocr_df["产品编号(金蝶云)"].tolist()

            # 调用新的计算函数, 传递 is_hk
            total_weight, container_info, calculation_details = calculate_total_weight(
                updated_product_names,
                updated_quantities,
                cleaned_updated_specifications_names,
                updated_weights,
                updated_codes,
                is_hk=region_is_hk
            )

            # 将结果存入 session_state
            st.session_state["container_info"] = container_info
            st.session_state["total_weight"] = total_weight
            st.session_state["calculation_details"] = calculation_details

            # st.session_state["confirmed_data_ready"] = True

            st.session_state["calc_done"] = True
            if upload_method == "✍粘贴文本✍":
                st.session_state["last_confirmed_data"] = table_text  # 将当前处理的table_text保存

            st.session_state.show_button_cabinet = True

        # 在按钮判断之外，根据 calc_done 状态展示结果
        if st.session_state.get("calc_done", False):
            # 使用 expander 展示计算过程详情
            with st.expander("🧮 各产品计算过程 🧮"):
                for detail in st.session_state["calculation_details"]:
                    st.info(detail)
            # 计算已完成，展示结果和计算过程
            st.success(f"✅计算完成！总毛重: {st.session_state['total_weight']:.2f} KG🧐")

            # # 此时就算之后点击柜重计算按钮，也不会丢失这些信息，因为已经在 session_state 中
            # if st.session_state.get("confirmed_data_ready", False):

            if st.session_state.show_button_cabinet:
                if st.button("🚛柜重计算🚛"):
                    # ### 新增：点击柜重计算前，将cabinet_mode = True
                    st.session_state["cabinet_mode"] = True

                    container_info_new = process_container_info(st.session_state["container_info"])

                    st.balloons()

                    for p in container_info_new:
                        p["trays"] = float(p["trays"])
                        p["weight"] = float(p["weight"])
                        p["每托重量"] = float(p["每托重量"])

                    cabinet(container_info_new)
                    st.session_state["cabinet_mode"] = False

        # 将 DataFrame 转为字符串，以便在文本区域中显示
        if 'edited_df' in locals():
            edited_df = st.session_state['edited_ocr_result_df']
            copy_text_df = edited_df.copy()
            copy_text_df["净重"] = float("nan")

            # 遍历 copy_text_df，更新“净重”列
            for index, row in copy_text_df.iterrows():
                user_input_id = row["产品编号(金蝶云)"]  # 获取用户输入的产品编号

                # 检查产品编号是否在 For_Update_Original_data 中存在
                if user_input_id in For_Update_Original_data["产品编号（金蝶云）"].values:
                    # 查找在 For_Update_Original_data 中匹配的行
                    correct_row = \
                        For_Update_Original_data[For_Update_Original_data["产品编号（金蝶云）"] == user_input_id].iloc[0]

                    # 如果“净重”列存在于 For_Update_Original_data，更新“净重”列
                    if "净重" in correct_row:
                        copy_text_df.at[index, "净重"] = correct_row["净重"]

            # 去除第一列（行号列）
            copy_text_df = copy_text_df.iloc[:, 1:]

            # 将“净重”列放在“毛重”列的左边
            columns = list(copy_text_df.columns)
            gross_weight_index = columns.index("毛重")  # 找到“毛重”列的位置
            # 将“净重”列插入到“毛重”列的左边
            columns.insert(gross_weight_index, columns.pop(columns.index("净重")))
            copy_text_df = copy_text_df[columns]

            copy_text = copy_text_df.to_csv(index=False, sep='\t')  # 使用 tab 作为分隔符，更便于复制到表格工具如 Excel
            st.divider()
            text_area = st.text_area(" ", copy_text, height=200, key="text_area")

            st_copy_to_clipboard(copy_text, "📌复制数据📌", "✅复制成功✅")
else:
    if upload_method == "📷图片上传📷":
        image_tutorial()

    if upload_method == "✍粘贴文本✍":
        text_tutorials()

    side_bar_tutorials()
    question_tutorials()

    sac.alert(label=None, description='🤔正在等待数据输入◽◽◽', size='xl', radius=20, color='warning', banner=True,
              icon=sac.AntIcon(name='LoadingOutlined', size=50, color=None))
