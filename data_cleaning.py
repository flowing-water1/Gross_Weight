import re

def clean_product_specifications(spec):
    if '*' in spec:
        numbers = re.findall(r'\d+', spec)
        if len(numbers) == 2:
            return str(int(numbers[0]) * int(numbers[1]))
    return re.sub(r'\D', '', spec) if re.sub(r'\D', '', spec) else ''

def clean_product_name(product_name):
    cleaned_name = product_name.replace(" ", "").replace("1*", "").replace("#", "")
    return re.sub(r'(?i)kg', 'KG', cleaned_name)
