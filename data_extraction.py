import pandas as pd

def extract_product_and_quantity(file_path, sheet_name="Sheet"):
    """
    该函数在保持原有返回的基础上，新增了对多余列数据的提取。
    返回四个值：
    1) original_product_names (List[str])
    2) specifications (List[str])
    3) quantities (List[str])  # 保留为字符串类型
    4) extra_info_list (List[Dict]) —— 每行一个Dict，存储该行的所有额外字段，如【编码、供应商、产品编码、发票号、采购单价、采购总价】等
    """
    df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)

    # 判断列数，选择不同的列名
    if df.shape[1] == 3:
        # 数据只有3列
        df.columns = ["产品名称", "产品规格", "数量"]
    elif df.shape[1] == 9:
        # 数据为9列
        df.columns = [
            "编码", "供应商", "产品编码（SAP Product Code）", "SO/发票号（invoice）",
            "产品名称", "产品规格", "数量", "采购单价(Price)", "采购总价(TOTAL)"
        ]
    else:
        raise ValueError(f"不支持的列数: {df.shape[1]}")

    # 提取需要的列：产品名称（第5列）、产品规格（第6列）、数量（第7列）
    original_product_names = df["产品名称"].dropna().astype(str).tolist()
    specifications = df["产品规格"].dropna().astype(str).tolist()
    quantities = df["数量"].dropna().astype(str).tolist()

    # 提取额外信息，保留其他列数据
    extra_info_list = []
    for idx, row in df.iterrows():
        row_dict = {}
        for col in df.columns:
            # 将每个字段（不在5, 6, 7列中的）存入字典
            if col not in ["产品名称", "产品规格", "数量"]:
                row_dict[col] = row[col] if pd.notnull(row[col]) else ""
        extra_info_list.append(row_dict)

    return original_product_names, specifications, quantities, extra_info_list
