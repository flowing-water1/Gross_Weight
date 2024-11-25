import pandas as pd

def extract_product_and_quantity(file_path, sheet_name="Sheet"):
    df = pd.read_excel(file_path, sheet_name=sheet_name)

    if "Description" in df.columns:
        quantities_column = df.columns[df.columns.str.contains(r'Qty|件数|（桶/箱）', case=False, regex=True)].tolist()
        specifications_column = df.columns[df.columns.str.contains(r'Volume\s?per(\sPacking)?', case=False, regex=True)].tolist()

        original_product_names = df['Description'].astype(str).tolist()
        quantities = df[quantities_column[0]].astype(int).tolist() if quantities_column else []
        specifications = df[specifications_column[0]].astype(str).tolist() if specifications_column else []

    else:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        original_product_names = df.iloc[:, 0].dropna().astype(str).tolist()
        specifications = df.iloc[:, 1].dropna().astype(str).tolist()
        quantities = df.iloc[:, -1].dropna().astype(int).tolist()

    return original_product_names, specifications, quantities
