import base64
import streamlit as st

updates = {
    "version": "2.7",
    "changes": [
        "优化UI引导，将侧边栏重构换成鼠标悬浮展开。",
        "当计算量不大时，只是为了查询单个产品时，欢迎使用简易匹配工具。",

    ]
}


def encode_image(image_path):
    """
    将图片文件转换为 Base64 编码，以便在 HTML 中嵌入显示。
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()


def show_update_dialog():
    """
    显示自定义的更新日志 Toast 弹窗。
    """
    # 编码图片
    unexpand_image = encode_image('guide/new_sidebar_unexpand.jpg')
    expand_image = encode_image('guide/new_sidebar_expand.jpg')

    # 自定义 HTML 和 CSS
    html = f"""
    <div id="update-toast" class="toast-container">
        <div class="toast-header">
            <strong>版本 {updates['version']}</strong>
        </div>
        <ul class="toast-content">
            {''.join([f"<li>{change}</li>" for change in updates['changes']])}
        </ul>
        <div class="toast-images">
            <div class="image-container">
                <img src="data:image/jpeg;base64,{unexpand_image}" alt="收缩状态">
                <p>收缩状态</p>
            </div>
            <div class="image-container">
                <img src="data:image/jpeg;base64,{expand_image}" alt="展开状态">
                <p>展开状态</p>
            </div>
        </div>
    </div>

    <style>
    /* Toast 容器样式 */
    .toast-container {{
        position: fixed;
        top: 20px;
        right: 20px;
        width: 350px;
        background-color: #ffffff;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        z-index: 1000;
        opacity: 1;
        transition: opacity 0.5s ease-in-out;
        animation: fadeout 5s forwards;
    }}

    /* Toast 头部样式 */
    .toast-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}


    /* Toast 内容样式 */
    .toast-content {{
        padding-left: 20px;
        margin: 10px 0;
    }}

    /* 图片容器样式 */
    .toast-images {{
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 10px;
    }}

    .image-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
    }}

    .image-container img {{
        max-width: 100px;
        max-height: 100px;
        width: auto;
        height: auto;
        border-radius: 4px;
    }}

    .image-container p {{
        text-align: center;
        font-size: 12px;
        margin-top: 5px;
    }}

    /* 动画效果 */
    @keyframes fadeout {{
        0% {{ opacity: 1; }}
        80% {{ opacity: 1; }}
        100% {{ opacity: 0; }}
    }}

    /* 鼠标悬停时暂停动画 */
    .toast-container:hover {{
        animation: none;
        opacity: 1 !important;
    }}
    </style>


    """

    # 使用 st.markdown 注入 HTML
    st.markdown(html, unsafe_allow_html=True)
