import math

v3_scores = [33174, 52798, 18664, 31748, 20485, 47278, 49818, 36762, 40130, 43757, 47400, 35432, 13202, 26458, 46008, 44298, 43603, 47854, 27751, 45997]
a2_scores = [40888, 12753, 39295, 53922, 3093, 15688, 39969, 10726, 17894, 59624, 43486, 42845, 3969, 9907, 27381, 45142, 17708, 37614, 30610, 29915]

v3_revs = [70468, 95766, 55674, 74265, 61241, 89394, 96401, 74036, 83346, 81929, 85688, 74751, 52027, 68748, 87191, 84434, 83900, 89693, 76367, 84449]
a2_revs = [76864, 43848, 81341, 94739, 39890, 61669, 84383, 50697, 57485, 110227, 88711, 86415, 42196, 48891, 70478, 81238, 55260, 80087, 69675, 68648]

v3_prods = [1828, 1744, 1716, 1753, 2013, 1891, 1850, 1638, 1793, 1796, 1777, 1719, 1753, 2079, 1865, 1853, 1813, 1797, 1982, 1789]
a2_prods = [1915, 1515, 2052, 2054, 2041, 2366, 2386, 2044, 2009, 2437, 2160, 2119, 1841, 2021, 2262, 1908, 2069, 2144, 1937, 2230]

def calc(v3, a2, name):
    n = len(v3)
    diff = [a - v for a, v in zip(a2, v3)]
    mean_diff = sum(diff) / n
    variance = sum((d - mean_diff) ** 2 for d in diff) / (n - 1)
    std_diff = math.sqrt(variance)
    se = std_diff / math.sqrt(n)
    
    # 95% CI for df=19 is roughly t=2.093
    ci_half = 2.093 * se
    ci = (mean_diff - ci_half, mean_diff + ci_half)
    
    # Cohen's d
    cohens_d = mean_diff / std_diff if std_diff != 0 else 0
    
    # t-stat
    t_stat = mean_diff / se if se != 0 else 0
    
    print(f"--- {name} ---")
    print(f"v17.3 Mean: {sum(v3)/n:.1f}")
    print(f"A.2 Mean:   {sum(a2)/n:.1f}")
    print(f"Mean Diff:  {mean_diff:.1f}")
    print(f"95% CI:     [{ci[0]:.1f}, {ci[1]:.1f}]")
    print(f"Cohen's d:  {cohens_d:.3f}")
    print(f"t-stat:     {t_stat:.3f}\n")

calc(v3_scores, a2_scores, "Score")
calc(v3_revs, a2_revs, "Revenue")
calc(v3_prods, a2_prods, "Productive Actions")
