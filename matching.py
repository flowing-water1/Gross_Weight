from rapidfuzz import process, fuzz


def find_best_match(query_product, product_names, product_weights, product_codes):
    matches = process.extract(query_product, product_names, scorer=fuzz.ratio, limit=5)

    match_details = []
    for match in matches:

        try:
            product_index = product_names.index(match[0])
            match_details.append({
                "name": match[0],
                "similarity": match[1],
                "weight": product_weights[product_index],
                "code": product_codes[product_index],
            })
        except ValueError:
            print(f"[ERROR] Match '{match[0]}' not found in product_names.")
            continue
        except IndexError as e:
            print(f"[ERROR] Index out of range for match '{match[0]}': {e}")
            continue
    best_match = matches[0]
    best_product_name = best_match[0]
    best_similarity = best_match[1]

    # 找到最佳匹配项的详细信息
    try:
        best_index = product_names.index(best_product_name)
        best_weight = product_weights[best_index]
        best_code = product_codes[best_index]
    except ValueError:
        print(f"[ERROR] Best match '{best_product_name}' not found in product_names.")
        best_weight = None
        best_code = None

    # 返回最佳匹配和所有匹配详情
    return {
        "best_match": {
            "name": best_product_name,
            "similarity": best_similarity,
            "weight": best_weight,
            "code": best_code,
        },
        "all_matches": match_details,
    }



def find_best_match_by_code(query_code, product_codes, product_weights, product_names,original_product_names):
    matches = process.extract(query_code, product_codes, scorer=fuzz.ratio, limit=5)

    match_details = []
    for match in matches:
        try:
            product_index = product_codes.index(match[0])
            match_details.append({
                "code": match[0],
                "similarity": match[1],
                "weight": product_weights[product_index],
                "name": product_names[product_index],
                "original_name": original_product_names[product_index],  # 未清洗的原始名称

            })
        except ValueError:
            print(f"[ERROR] Match '{match[0]}' not found in product_codes.")
            continue
        except IndexError as e:
            print(f"[ERROR] Index out of range for match '{match[0]}': {e}")
            continue

    best_match = matches[0]
    best_code = best_match[0]
    best_similarity = best_match[1]

    # 找到最佳匹配项的详细信息
    try:
        best_index = product_codes.index(best_code)
        best_weight = product_weights[best_index]
        best_name = product_names[best_index]

    except ValueError:
        print(f"[ERROR] Best match '{best_code}' not found in product_codes.")
        best_weight = None
        best_name = None

    # 返回最佳匹配和所有匹配详情
    return {
        "best_match": {
            "code": best_code,
            "similarity": best_similarity,
            "weight": best_weight,
            "name": best_name,
        },
        "all_matches": match_details,
    }