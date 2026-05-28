# data = """POC
# 4.323327    4.639594
# 1.065856    2.236856
# 0.471521    0.491244
# 0.493647    0.421295
# 2.4211    1.77162
# 1.734333    1.892556
# 0.816586    0.316992
# 1.259447    0.294744
# MAOC
# 21.78516    19.86458
# 19.82231    19.45821
# 16.2653    17.19559
# 14.88192    15.06126
# 18.2625    17.07143
# 16.85833    17.21541
# 19.48228    10.93467
# 13.50523    11.80729"""

# data = """1.994    1.896
# 1.614    1.638
# 1.146    1.237
# 1.139    1.136
# 1.569    1.456
# 1.462    1.401
# 0.908    1.369
# 1.012    0.81"""
#
# data = """3.601067    2.897733
# 2.1944    2.503867
# 3.010267    2.7852
# 2.081867    1.462933
# 2.475733    1.8568
# 0.956533    1.0972
# 0.872133    1.294133
# 0.872133    0.647067"""

# data = """9.935838    12.20381
# 44.27946    33.69557
# 67.0672    75.16711"""



data = """11.9068032    15.2292288
4.0017216    6.7704096
7.2286752    4.0399104
6.0639168    6.2548608"""

BITS = 53  # float64 尾数精度上限
MAX_INT = (1 << BITS) - 1  # 2^53 - 1

import secrets

def secure_random_in_extended_range(a: float, b: float) -> float:
    low = min(a, b)
    high = max(a, b)
    distance = high - low

    # 向两侧各扩展半个区间的宽度
    extended_low  = low  - distance / 2
    extended_high = high + distance / 2

    random_int = secrets.randbits(BITS)

    # 2. 映射为 [0, 1) 的浮点数（避免浮点精度陷阱）
    fraction = random_int / (MAX_INT + 1)

    # 3. 线性映射到目标区间
    result = extended_low + fraction * (extended_high - extended_low)

    return result


for item in data.split("\n"):
    line = item.split(" ")

    clean_line = []
    for line_item in line:
        if line_item:
            clean_line.append(line_item)

    if len(clean_line) != 2:
        print(item)
        continue

    clean_line = [float(i) for i in clean_line]
    output = secure_random_in_extended_range(*clean_line)
    final_list = clean_line + [round(output, 7)]
    print("   ".join([str(i) for i in final_list]))
    # print(f"f={clean_line}")
