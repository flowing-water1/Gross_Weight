import pandas as pd

# 实时监测，前置处理
file_path = 'original_data.xlsx'  # 替换为你的文件路径
df = pd.read_excel(file_path, sheet_name='境外贸易商品名称')

df['毛重（箱/桶）'] = df['毛重（箱/桶）'].fillna("NaN")  # 可以使用适当的值来填充，例如 0 或者其他默认值
df['净重'] = df['净重'].fillna("NaN")  # 可以使用适当的值来填充，例如 0 或者其他默认值


# 提取产品名列、毛重列和产品编号列
For_Update_Product_names = df['型号'].dropna().astype(str).tolist()
For_Update_Product_weights = df['毛重（箱/桶）'].dropna().astype(float).tolist()
For_Update_Product_codes = df['产品编码(金蝶云)'].dropna().astype(str).tolist()
For_Update_Specifications = df['规格'].dropna().astype(str).tolist()
For_Update_Net_Weight = df['净重'].dropna().astype(float).tolist()

# 将产品数据存储到DataFrame中
For_Update_Original_data = pd.DataFrame({
    "产品编号（金蝶云）": For_Update_Product_codes,
    "产品名称": For_Update_Product_names,
    "产品规格": For_Update_Specifications,
    "毛重（箱/桶）": For_Update_Product_weights,
    "净重": For_Update_Net_Weight
})

