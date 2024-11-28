

def allocate_products_to_containers(products, small_container_limit_pallets=20, large_container_limit_pallets=40,
                                    large_container_limit_weight=24000):
    # 用来保存大柜子和小柜子的划分
    large_containers = []
    small_containers = []

    # 初始化变量：当前大柜子的托盘数、毛重和装载范围
    current_pallets = 0
    current_weight = 0
    current_products = []

    # 2.currrent_products表示的是当前大柜子中的产品。
    # large_containers表示的是大柜子这个整体。

    # 用来跟踪每个产品是否已分配
    allocated = [False] * len(products)
    # 创建的是一个列表，里面的False被复制了len(products)次

    # 首先进行整体遍历
    for i, product in enumerate(products):
        # 如果当前产品已经被分配，则跳过
        if allocated[i]:
            continue

        # 计算当前产品加上后是否符合大柜子限制
        if current_pallets + product['托盘数'] <= large_container_limit_pallets and current_weight + product[
            '单个产品总毛重'] <= large_container_limit_weight:
            # 如果可以加入当前大柜子，继续加入
            current_pallets += product['托盘数']
            current_weight += product['单个产品总毛重']
            current_products.append(product)
            allocated[i] = True
        else:
            # 如果当前大柜子已满，开始分配到下一个大柜子
            if current_products:
                # 将已装满的大柜子放入列表
                large_containers.append(current_products)
                # 在循环过程中，每当一个大柜子被装满（或者无法再加入更多产品），就会触发 else 部分，
                # 把当前的大柜子（current_products）加入到 large_containers 列表中。然而，当最后一个大柜子未满时，循环结束后 它没有被加入。

            # 重置当前大柜子，开始装载新产品
            current_pallets = product['托盘数']
            current_weight = product['单个产品总毛重']
            current_products = [product]
            allocated[i] = True

    # 最后一个大柜子仍然处于current_products中待处理(for已经结束，不会通过else中的if判断加入到large_containers中)，而if判断就是为了处理最后这一个大柜子
    if current_products:
        large_containers.append(current_products)

    # 优化：回头检查是否有符合小柜子条件的装载
    # 尝试将符合小柜子条件的产品从大柜子转移到小柜子
    new_large_containers = []  # 清洗之前的large_containers
    for container in large_containers:
        total_pallets = sum(item['托盘数'] for item in container)
        total_weight = sum(item['单个产品总毛重'] for item in container)

        # 如果该大柜子符合小柜子的条件，直接装入小柜子
        if total_pallets < small_container_limit_pallets and total_weight < 21000:
            small_containers.append(container)
        else:
            new_large_containers.append(container)

    large_containers = new_large_containers

    return large_containers, small_containers

