from paddlex import create_pipeline
import pandas as pd

def perform_ocr(image_path, output_folder="./output5.0/"):
    # 创建 OCR pipeline
    pipeline = create_pipeline(pipeline="table_recognition")
    # 执行 OCR
    output = pipeline.predict(image_path)

    # 保存 OCR 结果
    for res in output:
        res.save_to_img(output_folder)  # 保存检测图像
        res.save_to_xlsx(output_folder)  # 保存表格

    # 加载生成的表格数据
    xlsx_path = f"{output_folder}/result.xlsx"  # 假设生成的表格名为 result.xlsx
    df = pd.read_excel(xlsx_path)
    return df
