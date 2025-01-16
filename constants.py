PACKAGE_TO_PALLETS = {
    48: 124,  # 12*0.4 KG
    1204: 124,  # 12*0.4 KG
    12: 48,
    15: 39,  # 3*5L
    16: 36,
    18: 24,
    20: 24,
    209: 4,
    180: 4,
    208: 4,
    2081: 4,
    170: 4,
    190: 3
}


def get_package_to_pallets(is_HK_or_Europe=False):
    """
    根据 is_hk (香港/欧洲) 动态生成 PACKAGE_TO_PALLETS。
    如果是香港模式，则 180 对应 3，否则（默认欧洲模式）就是 4。
    """
    package_dict = PACKAGE_TO_PALLETS.copy()
    if is_HK_or_Europe:
        package_dict[180] = 3 #香港
    else:
        package_dict[180] = 4 #欧洲
    return package_dict