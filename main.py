import json
import os
import pandas as pd
import streamlit as st
from weight_calculation import calculate_total_weight, calculate_total_weight_for_sidebar
from data_extraction import extract_product_and_quantity
from data_cleaning import clean_product_name, clean_product_specifications
from matching import find_best_match, find_best_match_by_code
from original_data import For_Update_Product_names, For_Update_Product_weights, For_Update_Product_codes, \
    For_Update_Specifications, For_Update_Original_data
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from st_copy_to_clipboard import st_copy_to_clipboard
from container_calculation import allocate_products_to_containers
import streamlit_toggle as tog
import base64
from io import StringIO
import requests
import streamlit_nested_layout
# 将粘贴的文本转换为 DataFrame
from io import StringIO
import pandas as pd

# Streamlit App Setup
st.set_page_config(layout="wide", initial_sidebar_state='collapsed')
title_col1, title_col2, title_col3 = st.columns([0.6, 1, 0.5])
with title_col2:
    st.title("产品数据提取与重量计算")

# 初始化 session_state
if "toggle_status" not in st.session_state:
    st.session_state["toggle_status"] = False

# 初始化 session_state 中的按钮状态
if "show_button_cabinet" not in st.session_state:
    st.session_state.show_button_cabinet = False

# 初始化 session_state 中的额外状态位
if "cabinet_mode" not in st.session_state:
    st.session_state["cabinet_mode"] = False  # 控制柜重计算对话框打开时的状态


def reset_calculation_states():
    keys_to_reset = ["calc_done", "container_info", "total_weight", "calculation_details"]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]


@st.dialog("🚚\u2003柜数计算\u2003🚚", width="large")
def cabinet(container_info):
    large_containers, small_containers = allocate_products_to_containers(container_info)

    df_container = pd.DataFrame(container_info)
    # 输出总毛重
    with st.expander("各产品托数与毛重表格"):
        st.dataframe(df_container, hide_index=True)

    # 存储大柜子和小柜子的详细信息
    big_containers_info = []
    small_containers_info = []

    # 收集大柜子装载范围信息
    container_count_big = 1
    for container in large_containers:
        container_info = f"大柜子{container_count_big}装载范围："
        container_products_info = []
        # 遍历大柜子中的每个产品，储存详细信息
        for product in container:
            product_name = product['产品名称']
            tray_count = product['托盘数']
            single_product_weight = product['单个产品总毛重']
            # 格式化输出每个产品的详细信息
            product_info = f"产品名字：{product_name}\n托盘数: {tray_count:.2f}\n产品总毛重: {single_product_weight:.3f} KG"
            container_products_info.append(product_info)

        # 将每个柜子的信息添加到大柜子列表中
        big_containers_info.append((container_info, container_products_info))
        container_count_big += 1

    # 收集小柜子装载范围信息
    container_count_small = 1
    for container in small_containers:
        container_info = f"\n小柜子{container_count_small}装载范围："
        container_products_info = []

        for product in container:
            product_name = product['产品名称']
            tray_count = product['托盘数']
            single_product_weight = product['单个产品总毛重']
            # 格式化输出每个产品的详细信息
            product_info = f"产品名字：{product_name}\n托盘数: {tray_count:.2f}\n产品总毛重: {single_product_weight:.3f} KG"
            container_products_info.append(product_info)

        # 将每个柜子的信息添加到小柜子列表中
        small_containers_info.append((container_info, container_products_info))
        container_count_small += 1

    # 优先展示总共需要的柜子数
    st.info(f"总共需要{container_count_big - 1}个大柜子，{container_count_small - 1}个小柜子")

    # 展示大柜子和小柜子的详细信息

    for container_info, products_info in big_containers_info:
        with st.expander(container_info):
            for product_info in products_info:
                st.info(product_info)

    for container_info, products_info in small_containers_info:
        with st.expander(container_info):
            for product_info in products_info:
                st.info(product_info)


@st.fragment
def toggle_fragment():
    # 动态更新 label 文本
    label_text = "🔖 输入名称 🔖" if not st.session_state["toggle_status"] else "🧬 输入编码 🧬"

    # 切换控件
    toggle_status = tog.st_toggle_switch(
        label=label_text,  # 使用动态文本
        key="input_toggle",
        default_value=st.session_state["toggle_status"],
        label_after=True,
        inactive_color='#95e1d3',
        active_color="#f38181",
        track_color="#f38181"
    )

    # 检测切换状态并更新，不需要刷新整个页面
    if toggle_status != st.session_state["toggle_status"]:
        st.session_state["toggle_status"] = toggle_status
        st.rerun()


# 侧边栏简易功能
with st.sidebar:
    st.header("简易匹配工具")

    toggle_fragment()

    if not st.session_state["toggle_status"]:  # False 表示输入名称

        sidebar_product_name = st.text_input("输入产品名称", key="nam🧬e_input")
        sidebar_product_code = st.text_input("输入产品编码", disabled=True, key="code_input")
    else:  # True 表示输入编码
        sidebar_product_name = st.text_input("输入产品名称", disabled=True, key="name_input")
        sidebar_product_code = st.text_input("输入产品编码", key="code_input")

    sidebar_quantity = st.number_input("输入数量", min_value=0, step=1)

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
                f"编号：{match['code']} | 产品名称： {For_Update_Original_data.loc[For_Update_Original_data['产品编号（金蝶云）'] == match['code'].strip(), '产品名称'].values[0]} | 相似度: {match['similarity']} | 毛重: {match['weight']}"
                for match in all_matches
            ]

            user_selection = st.selectbox(
                "选择最佳匹配项",
                options,
                index=0,
                key="sidebar_selection"
            )

            # 使用产品编号匹配
            original_product_name = user_selection.split("|")[1].strip().replace("产品名称：", "").strip()  # 获取未清洗的产品名称
            selected_product_code = user_selection.split("|")[0].strip().replace("编号：", "").strip()
            selected_match = next(
                (match for match in all_matches if match["code"].strip() == selected_product_code), None
            )

            product_spec = For_Update_Original_data.loc[
                For_Update_Original_data['产品编号（金蝶云）'] == selected_match['code'].strip(), '产品规格'].values[0]
            cleaned_spec = clean_product_specifications(product_spec)  # 清洗规格

            if selected_match is None:
                st.warning("未找到符合条件的匹配项，请检查数据或重新选择。")
            else:
                st.info(
                    f"选择的产品名称: {original_product_name}  \n选择的产品编码: {selected_match['code']}  \n产品规格：{product_spec}  \n毛重: {selected_match['weight']} KG")
                total_weight = calculate_total_weight_for_sidebar(
                    product_names=[original_product_name],  # 使用原始产品名称
                    quantities=[sidebar_quantity],
                    cleaned_product_specifications_names=[cleaned_spec],  # 传入清洗后的规格
                    matched_product_weights=[selected_match['weight']],
                    matched_product_codes=[selected_match['code']]
                )
                st.success(f"总毛重: {total_weight:.2f} KG")
        else:
            # 使用未清洗的产品名称来展示最佳匹配
            original_best_product_name = For_Update_Original_data.loc[
                For_Update_Original_data['产品编号（金蝶云）'] == best_match['code'].strip(), '产品名称'].values[0]
            product_spec = For_Update_Original_data.loc[
                For_Update_Original_data['产品编号（金蝶云）'] == best_match['code'].strip(), '产品规格'].values[0]
            cleaned_spec = clean_product_specifications(product_spec)  # 清洗规格

            # 转义，避免文字变成斜体
            original_best_product_name_escaped = original_best_product_name.replace("*", "\\*")
            product_spec_escaped = product_spec.replace("*", "\\*")
            st.info(
                f"最佳匹配项名称: {original_best_product_name_escaped}  \n最佳匹配项编码: {best_match['code']}  \n产品规格：{product_spec_escaped}  \n毛重: {best_match['weight']} KG")

            total_weight = calculate_total_weight_for_sidebar(
                product_names=[original_best_product_name],  # 使用原始产品名称
                quantities=[sidebar_quantity],
                cleaned_product_specifications_names=[cleaned_spec],  # 传入清洗后的规格
                matched_product_weights=[best_match['weight']],
                matched_product_codes=[best_match['code']]
            )
            st.success(f"总毛重: {total_weight:.2f} KG")


upload_method = st.radio("请选择上传方式", ("图片上传", "粘贴表格文本"))

if upload_method == "图片上传":
    if 'calc_done' not in st.session_state:
        reset_calculation_states()
    # 当进入图片上传模式时，清空文本模式的数据
    if 'ocr_result_df_text' in st.session_state:
        del st.session_state['ocr_result_df_text']

    if 'display_df' in st.session_state:
        del st.session_state['display_df']

    # 同时清空用户选择的记录
    if 'user_selection_flag' in st.session_state:
        del st.session_state['user_selection_flag']

    if 'user_previous_selection' in st.session_state:
        del st.session_state['user_previous_selection']

    # 上传图片
    uploaded_image = st.file_uploader("上传产品图片", type=["png", "jpg", "jpeg"])

    if uploaded_image:
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
            st.session_state.clear()

            st.session_state['previous_uploaded_file_name'] = previous_uploaded_file_name
            st.session_state['previous_uploaded_file_name'] = uploaded_image.name

        # st.session_state 中不存在 'ocr_result_df_image' 这个键（也就是说还没有 OCR 结果）。
        # 也就是首次运行、页面刷新后的首次上传或上传了新图片时才执行 OCR 操作。
        if 'ocr_result_df_image' not in st.session_state:
            st.toast(f"你上传的图片文件是: {uploaded_image.name}")

            # 使用 NamedTemporaryFile 保存上传的文件
            original_file_name = os.path.splitext(uploaded_image.name)[0]
            standardized_filename = f"{original_file_name}_uploaded.png"
            temp_file_path = os.path.join(".", standardized_filename)
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(uploaded_image.read())

            # OCR 处理部分（使用服务端 API 替换本地模型）
            st.toast("正在进行表格识别...")

            try:
                # 对本地图像进行 Base64 编码
                with open(temp_file_path, "rb") as file:
                    image_bytes = file.read()
                    if not image_bytes:
                        st.error("读取的图像数据为空！")
                    image_data = base64.b64encode(image_bytes).decode("ascii")

                # 调用 API
                API_URL = "https://api123.1127107.xyz/table-recognition"
                payload = {"image": image_data}

                response = requests.post(API_URL, json=payload, timeout=30)

                if response.status_code == 200:
                    result = response.json().get("result", {})
                    if not result:
                        st.error("API 返回的数据为空或格式不正确。")

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
                    st.error("无法连接到本地服务。请确保本地服务已启动，并且可通过内网穿透访问。")

                else:
                    st.error(f"API 调用失败，状态码: {response.status_code}")
                    with st.expander("详细报错信息"):
                        st.error(f"{response.text}")

            except Exception as e:
                # 捕获请求异常并提示服务端未启动
                st.error("无法连接到服务端。请确保服务端已启动并且可以访问。")
                st.error(f"详细错误信息：{str(e)}")

elif upload_method == "粘贴表格文本":

    table_text = st.text_area("请输入表格文本", value=st.session_state.get("last_confirmed_data", ""))

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
            st.toast("表格已成功上传并保存为 Excel 文件！")

            # 更新 session_state
            ocr_result_df = pd.read_excel(xlsx_file_path, header=None)
            ocr_result_df.columns = ["产品名称", "产品规格", "数量"]
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
    if upload_method == "图片上传":
        if uploaded_image:
            st.image(uploaded_image, caption='上传的图片', use_container_width=True)
            ocr_result_df = st.session_state['ocr_result_df_image']
            image_files = st.session_state.get('image_files', [])
            xlsx_file_path = st.session_state['xlsx_file_path']
            ocr_result_original_df = st.session_state['ocr_result_original_df']

            # 展示识别的图片
            expander = st.expander("OCR 识别的图片结果：")
            for image_file in image_files:
                if os.path.exists(image_file):
                    expander.image(image_file, caption=f"识别结果: {os.path.basename(image_file)}",
                                   use_container_width=True)

            # 从 session_state 中读取 OCR 结果
            markdown_col1, markdown_col2, markdown_col3 = st.columns([1.5, 1, 1])
            with markdown_col2:
                st.markdown(f"""
                ### OCR 识别结果
                **文件名:** `{uploaded_image.name}`
                """, unsafe_allow_html=True)

    if upload_method == "粘贴表格文本":
        ocr_result_df = st.session_state['ocr_result_df_text']
        xlsx_file_path = st.session_state['xlsx_file_path']
        ocr_result_original_df = st.session_state['ocr_result_original_df']

        # 展示生成的表格
        markdown_col1, markdown_col2, markdown_col3 = st.columns([1.5, 1, 1])
        with markdown_col2:
            st.markdown(f"""
            ### 处理结果
            **文件名:** `uploaded_table.xlsx`
            """, unsafe_allow_html=True)

    # 只是为了展示的表格而已，不会因为状态变更而改变，一开始什么样就是什么样
    # 因为if 'display_df' not in st.session_state:约束了只有第一次才会诞生
    # 之后display_df都在session_state里了，就算rerun也不会进入下面的代码中
    if 'display_df' not in st.session_state:
        st.session_state['display_df'] = ocr_result_df.copy()
        st.session_state['display_df'].index = st.session_state['display_df'].index + 1

    dataframe_col1, dataframe_col2 = st.columns([0.45, 1])
    with dataframe_col2:
        st.dataframe(st.session_state['display_df'])

    # 提取数据
    original_product_names, specifications, quantities = extract_product_and_quantity(xlsx_file_path)

    # 清洗数据
    cleaned_product_names = [clean_product_name(name) for name in original_product_names]
    cleaned_product_specifications_names = [clean_product_specifications(spec) for spec in specifications]

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
    with st.expander("选择最佳匹配项"):
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

                warning_message = (
                    f"↓ 表格{original_row_index + 1} 行： 产品：{original_product_names[idx]}，"
                    f"对应的最佳匹配项为：产品 '{original_name}'，"
                    f"相似度为 {best_match['similarity']:.2f}，可能需要手动选择匹配项 ↓"
                ).replace("*", "\\*")  # 转义所有的 *

                st.warning(warning_message)

                # 提供前 5 个匹配项供选择
                options = [
                    f"编号：{match['code']} | 产品名称： {For_Update_Original_data.loc[For_Update_Original_data['产品编号（金蝶云）'] == match['code'].strip(), '产品名称'].values[0]} | 相似度: {match['similarity']} | 毛重: {match['weight']} ".replace(
                        " | ", "\u00A0\u00A0\u00A0|\u00A0\u00A0\u00A0")
                    for match in all_matches
                ]

                # 默认值为第一个选项
                default_option = options[0]

                user_selection = st.selectbox(
                    " ",
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
                        ### 修改的表格
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
                        ### 确定的表格
                        """, unsafe_allow_html=True)
        st.dataframe(updated_ocr_df, hide_index=True)

if 'edited_ocr_result_df' in st.session_state:
    updated_ocr_df = st.session_state['edited_ocr_result_df']

    if st.button("确定"):
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

        # 使用更新后的数据进行计算
        total_weight, container_info, calculation_details = calculate_total_weight(
            updated_product_names,
            updated_quantities,
            cleaned_updated_specifications_names,
            updated_weights,
            updated_codes
        )

        # 将结果存入 session_state
        st.session_state["container_info"] = container_info
        st.session_state["total_weight"] = total_weight
        st.session_state["calculation_details"] = calculation_details

        # st.session_state["confirmed_data_ready"] = True

        st.session_state["calc_done"] = True
        if upload_method == "粘贴表格文本":
            st.session_state["last_confirmed_data"] = table_text  # 将当前处理的table_text保存

        st.session_state.show_button_cabinet = True

    # 在按钮判断之外，根据 calc_done 状态展示结果
    if st.session_state.get("calc_done", False):
        # 使用 expander 展示计算过程详情
        with st.expander("🧮 各产品计算过程 🧮"):
            for detail in st.session_state["calculation_details"]:
                st.info(detail)
        # 计算已完成，展示结果和计算过程
        st.success(f"计算完成！总毛重: {st.session_state['total_weight']:.2f} KG")

        # # 此时就算之后点击柜重计算按钮，也不会丢失这些信息，因为已经在 session_state 中
        # if st.session_state.get("confirmed_data_ready", False):

        if st.session_state.show_button_cabinet:
            if st.button("柜重计算"):
                # ### 新增：点击柜重计算前，将cabinet_mode = True
                st.session_state["cabinet_mode"] = True
                # st.info(f"st.session_state[cabinet_mode]:{st.session_state['cabinet_mode']}")
                cabinet(st.session_state["container_info"])
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

        text_area = st.text_area(" ", copy_text, height=200, key="text_area")
        st.divider()
        st_copy_to_clipboard(copy_text)
else:
    st.warning("🤔等待数据中◽◽◽◽")
