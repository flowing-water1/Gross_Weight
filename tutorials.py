import streamlit as st
import streamlit_antd_components as sac


def image_tutorial():
    with st.expander("❕ 图片上传教程"):
        # 1.
        st.markdown("""
            <span style="font-weight:bold;">1.</span>
            点击上面的栏目之后可以上传文件，上传的图片内容只能包含 
            <span style="color:red; font-weight:bold;">“名称”，“规格”，“数量”</span> 
            这种形式， “名称”，“规格”形式不限。
        """, unsafe_allow_html=True)
        with st.expander("图片可以支持的形式"):
            st.image("guide/image_example_1.jpg", caption="支持上传图片形式①")
            sac.divider(label='分割线', align='center', color='gray', key="1")
            st.image("guide/image_example_2.jpg", caption="支持上传图片形式②")
            sac.divider(label='分割线', align='center', color='gray', key="2")
            st.image("guide/image_example_3.jpg", caption="支持上传图片形式③")
            sac.divider(label='分割线', align='center', color='gray', key="3")
            st.image("guide/image_example_4.jpg", caption="支持上传图片形式④")

            sac.divider(align='center', color='gray', key="5")

            st.image("guide/image_example_5.jpg", caption="可能失败的图片形式")
        # 2.
        st.markdown("""
                <span style="font-weight:bold;">2.</span>
                上传之后，静候识别服务完成◽◽◽
            """, unsafe_allow_html=True)
        with st.expander("上传时右上角会出现◽◽◽"):
            st.image("guide/image_upload_state.jpg", caption="识别时右上角会出现")

        # 3.
        st.markdown("""
                <span style="font-weight:bold;">3.</span>
                上传成功后，整体界面如图：
            """, unsafe_allow_html=True)
        with st.expander("上传成功后✅："):
            st.image("guide/upload_successed.jpg")

        # 4.
        st.markdown("""
                <span style="font-weight:bold;">4.</span>
                检查和修改◽◽◽
            """, unsafe_allow_html=True)
        with st.expander("初步简单修改🔍"):
            st.markdown("""
                    <span style="font-weight:bold;">如果出现下面的展开栏，就意味着有项目的匹配度低于100
                    （当然，这并不意味着错误，但是为了保险起见，还是让我们检查一下吧！）</span>
                """, unsafe_allow_html=True)
            st.image("guide/if_best_match.jpg", use_container_width=True)
            sac.divider(align='center', color='gray', key="6")

            st.markdown("""
                    <span style="font-weight:bold;">点击展开之后，我们就可以看到有哪些项目是低于100的。</span>
                    <span style="color:red; font-weight:bold;">只需要对比提示框中的左右内容即可，不需要来回滚轮回去看表格。</span>
                    <span style="font-weight:bold;">因为左边的就是</span>
                    <span style="color:red; font-weight:bold;">原始表格识别的内容，</span>
                    <span style="font-weight:bold;">右边就是</span>
                    <span style="color:red; font-weight:bold;">“认为最匹配的项目”</span>
                """, unsafe_allow_html=True
                        )
            st.image("guide/best_match_select_box.jpg")

            sac.divider(align='center', color='gray', key="7")
            st.markdown("""
                    <span style="font-weight:bold;">倘若真的有不匹配的内容，就可以点击框框进行选择。</span>
                """, unsafe_allow_html=True)
            st.image("guide/match_select.jpg")

            sac.divider(align='center', color='gray', key="8")
        with st.expander("手动详细修改✍"):
            st.markdown("""
                        <span style="font-weight:bold;">\n\n倘若上面的候选框中没有答案，或者数量识别错误了，
                        那么请在下面的表格中进行修改。<span style="font-weight:bold;">点击表格，修改后按回车即可。\n\n<span style="font-weight:bold;">左边的表格用于修改，右边的表格用于确定\n\n</span>
                        <span style="color:red; font-weight:bold;">要修改哪些，可以从刚才的候选框中看到是哪些行，然后在表格中方便定位</span>
                    """, unsafe_allow_html=True)
            st.image("guide/modified.jpg", caption="从编号和数量进行修改")
            sac.divider(align='center', color='gray', key="9")

            st.markdown("""
                    <span style="font-weight:bold;">修改示例：</span>
                """, unsafe_allow_html=True)
            st.image("guide/modified_ok.jpg", caption="修改示例")

        # 5.

        st.markdown("""
                            <span style="font-weight:bold;">5.</span>
                            确定和计算
                        """, unsafe_allow_html=True)
        with st.expander("数据无误可以确定计算"):
            st.markdown("\n")
            left_markdown_image_calculate, cent_markdown_image_calculate, last_markdown_image_calculate = st.columns(3)
            with cent_markdown_image_calculate:
                st.markdown("""
                                <span style="color:red; font-weight:bold;">❗ 注意 ❗ 每次修改后都要点击“确定计算”\n\n
                                <span style="color:red; font-weight:bold;">这样才能更新后续的计算数据</span>
                                """, unsafe_allow_html=True)
            st.markdown("""
                            <span style="font-weight:bold;">点击确定计算后，就会出现总毛重了~</span>
                            """, unsafe_allow_html=True)
            st.image("guide/caculate_success.jpg")
            sac.divider(align='center', color='gray', key="10")
            st.markdown("""
                            <span style="font-weight:bold;">也可以点开拓展框，看看详细的计算信息（预防纠错）</span>
                            """, unsafe_allow_html=True)
            st.image("guide/caculate_info.jpg")

        # 6.
        st.markdown("""
                            <span style="font-weight:bold;">6.</span>
                            柜重计算
                        """, unsafe_allow_html=True)
        with st.expander("确定数据完全无误后，可以进行柜重计算"):
            st.markdown("\n")
            left_markdown_image_container, cent_markdown_image_container, last_markdown_image_container = st.columns(3)
            with cent_markdown_image_container:
                st.markdown("""
                                <span style="color:red; font-weight:bold;">❗ 注意 ❗ 每次修改后都要点击“确定计算”\n\n
                                <span style="color:red; font-weight:bold;">这样才能更新后续的计算数据</span>
                                """, unsafe_allow_html=True)
            st.markdown("""
                            \n\n<span style="font-weight:bold;">点击柜重计算后，会出现对话框，里面是柜重的详细计算</span>
                            """, unsafe_allow_html=True)
            st.image("guide/caculate_container.jpg")
            sac.divider(align='center', color='gray', key="11")
            st.markdown("""
                            \n\n<span style="font-weight:bold;">下面有总表的汇总数据，也可以点击“复制总表”黏贴到表格中</span>
                            """, unsafe_allow_html=True)
            st.image("guide/copy_container_result.jpg")


def text_tutorials():
    with st.expander("❕ 文本上传教程"):
        # 1.
        st.markdown("""
            <span style="font-weight:bold;">1.</span>
            点击上面的栏目之后可以上传文本，上传的图片内容只能包含 
            <span style="color:red; font-weight:bold;">“名称”，“规格”，“数量”</span> 
            这种形式， “名称”，“规格”形式不限。
        """, unsafe_allow_html=True)
        with st.expander("文本复制的形式"):
            st.image("guide/test_upload_1.jpg", caption="支持上传文本形式①")
            sac.divider(label='分割线', align='center', color='gray', key="1")
            st.image("guide/test_upload_2.jpg", caption="支持上传文本形式②")
            sac.divider(label='分割线', align='center', color='gray', key="2")
            st.image("guide/test_upload_3.jpg", caption="支持上传文本形式③")
            sac.divider(label='分割线', align='center', color='gray', key="3")
            st.image("guide/test_upload_4.jpg", caption="支持上传文本形式④")

        # 2.
        st.markdown("""
                <span style="font-weight:bold;">2.</span>
                上传之后，静候识别服务完成◽◽◽
            """, unsafe_allow_html=True)
        with st.expander("上传时右上角会出现◽◽◽"):
            st.image("guide/test_uploaded_success.jpg", caption="识别时右上角会出现")

        # 3.
        st.markdown("""
                <span style="font-weight:bold;">3.</span>
                上传成功后，整体界面如图：
            """, unsafe_allow_html=True)
        with st.expander("上传成功后✅："):
            st.image("guide/test_uploaded.jpg")

        # 4.
        st.markdown("""
                <span style="font-weight:bold;">4.</span>
                检查和修改◽◽◽
            """, unsafe_allow_html=True)
        with st.expander("初步简单修改🔍"):
            st.markdown("""
                    <span style="font-weight:bold;">如果出现下面的展开栏，就意味着有项目的匹配度低于100
                    （当然，这并不意味着错误，但是为了保险起见，还是让我们检查一下吧！）</span>
                """, unsafe_allow_html=True)
            st.image("guide/text_if_best_match.jpg", use_container_width=True)
            sac.divider(align='center', color='gray', key="6")

            st.markdown("""
                    <span style="font-weight:bold;">点击展开之后，我们就可以看到有哪些项目是低于100的。</span>
                    <span style="color:red; font-weight:bold;">只需要对比提示框中的左右内容即可，不需要来回滚轮回去看表格。</span>
                    <span style="font-weight:bold;">因为左边的就是</span>
                    <span style="color:red; font-weight:bold;">原始表格识别的内容，</span>
                    <span style="font-weight:bold;">右边就是</span>
                    <span style="color:red; font-weight:bold;">“认为最匹配的项目”</span>
                """, unsafe_allow_html=True
                        )
            st.image("guide/best_match_select_box.jpg")

            sac.divider(align='center', color='gray', key="7")
            st.markdown("""
                    <span style="font-weight:bold;">倘若真的有不匹配的内容，就可以点击框框进行选择。</span>
                """, unsafe_allow_html=True)
            st.image("guide/match_select.jpg")

            sac.divider(align='center', color='gray', key="8")
        with st.expander("手动详细修改✍"):
            st.markdown("""
                        <span style="font-weight:bold;">\n\n倘若上面的候选框中没有答案，或者数量识别错误了，
                        那么请在下面的表格中进行修改。<span style="font-weight:bold;">点击表格，修改后按回车即可。\n\n<span style="font-weight:bold;">左边的表格用于修改，右边的表格用于确定\n\n</span>
                        <span style="color:red; font-weight:bold;">要修改哪些，可以从刚才的候选框中看到是哪些行，然后在表格中方便定位</span>
                    """, unsafe_allow_html=True)
            st.image("guide/modified.jpg", caption="从编号和数量进行修改")
            sac.divider(align='center', color='gray', key="9")

            st.markdown("""
                    <span style="font-weight:bold;">修改示例：</span>
                """, unsafe_allow_html=True)
            st.image("guide/modified_ok.jpg", caption="修改示例")

        # 5.
        st.markdown("""
                            <span style="font-weight:bold;">5.</span>
                            确定和计算
                        """, unsafe_allow_html=True)
        with st.expander("数据无误可以确定计算"):
            st.markdown("\n")
            left_markdown_text_calculate, cent_markdown_text_calculate, last_markdown_text_calculate = st.columns(3)
            with cent_markdown_text_calculate:
                st.markdown("""
                                <span style="color:red; font-weight:bold;">❗ 注意 ❗ 每次修改后都要点击“确定计算”\n\n
                                <span style="color:red; font-weight:bold;">这样才能更新后续的计算数据</span>
                                """, unsafe_allow_html=True)
            st.markdown("""
                            <span style="font-weight:bold;">点击确定计算后，就会出现总毛重了~</span>
                            """, unsafe_allow_html=True)
            st.image("guide/caculate_success.jpg")
            sac.divider(align='center', color='gray', key="10")
            st.markdown("""
                            <span style="font-weight:bold;">也可以点开拓展框，看看详细的计算信息（预防纠错）</span>
                            """, unsafe_allow_html=True)
            st.image("guide/caculate_info.jpg")

        # 6.
        st.markdown("""
                            <span style="font-weight:bold;">6.</span>
                            柜重计算
                        """, unsafe_allow_html=True)
        with st.expander("确定数据完全无误后，可以进行柜重计算"):
            st.markdown("\n")
            left_markdown_text_container, cent_markdown_text_container, last_markdown_text_container = st.columns(3)
            with cent_markdown_text_container:
                st.markdown("""
                                <span style="color:red; font-weight:bold;">❗ 注意 ❗ 每次修改后都要点击“确定计算”\n\n
                                <span style="color:red; font-weight:bold;">这样才能更新后续的计算数据</span>
                                """, unsafe_allow_html=True)

            st.markdown("""
                            <span style="font-weight:bold;">点击柜重计算后，会出现对话框，里面是柜重的详细计算</span>
                            """, unsafe_allow_html=True)
            st.image("guide/caculate_container.jpg")
            sac.divider(align='center', color='gray', key="11")
            st.markdown("""
                            <span style="font-weight:bold;">下面有总表的汇总数据，也可以点击“复制总表”黏贴到表格中</span>
                            """, unsafe_allow_html=True)
            st.image("guide/copy_container_result.jpg")



def side_bar_tutorials():
    with st.expander("📇侧边栏简易功能介绍（点击左上角“>”符号展开）",expanded= True):
        with st.expander("输入产品名称匹配"):
            st.markdown("\n")
            st.markdown("""
                    \n\n<span style="font-weight:bold;">当输入产品名称（支持模糊输入），并且输入数量之后，按下回车，就会出现毛重计算结果。
                    输入模糊名称也可以，同样会需要选择最佳匹配项。
                    </span>

                """, unsafe_allow_html=True)
            left_sidebar_name, cent_sidebar_name, last_sidebar_name = st.columns(3)
            with cent_sidebar_name:
                st.image("guide/side_bar_example_name.jpg", caption="产品名称匹配")


        with st.expander("输入产品编号匹配"):
            st.markdown("\n")
            st.markdown("""
                    \n\n<span style="font-weight:bold;">当输入产品编号（必须精确），并且输入数量之后，按下回车，就会出现毛重计算结果。
                    </span>

                """, unsafe_allow_html=True)
            left_sidebar_code, cent_sidebar_code, last_sidebar_code = st.columns(3)
            with cent_sidebar_code:
                st.image("guide/side_bar_example_code.jpg",caption="产品编号匹配")


def question_tutorials():
    with st.expander("❔常见问题",expanded= True):
        with st.expander("如果出现了“OCR识别失败”是为什么呢？"):
            st.markdown("\n")
            st.markdown("""
                    \n\n<span style="font-weight:bold;">当上传图片内容里
                    <span style="color:red; font-weight:bold;">表格行数过短</span> 
                    或者
                    <span style="color:red; font-weight:bold;">表格边框模糊</span> 
                    时，识别服务会失败（大约小于5行时），此时请使用“粘贴表格”模式</span>

                """, unsafe_allow_html=True)
            st.image("guide/image_example_warning.jpg", caption="失败信息")
            sac.divider(align='center', color='gray', key="51")

            st.image("guide/image_example_5.jpg", caption="可能失败的图片形式")


        with st.expander("复制按钮错位了是为什么呢？"):
            st.markdown("\n")
            st.markdown("""
                    \n\n<span style="font-weight:bold;">当复制按钮出现错位时，这是偶然会出现的问题，无法解决，可以手动复制或者重新点击别的按钮刷新状态</span>

                """, unsafe_allow_html=True)
            left_co, cent_co, last_co = st.columns(3)
            with cent_co:
                st.image("guide/copyclild_bug.jpg",caption="按钮错误")