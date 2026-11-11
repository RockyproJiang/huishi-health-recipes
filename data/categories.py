from data.breakfast import BREAKFAST_FOODS
from data.lunch import LUNCH_FOODS
from data.dinner import DINNER_FOODS

CATEGORIES = list(dict.fromkeys(
    ["全部"] + [f["category"] for f in BREAKFAST_FOODS + LUNCH_FOODS + DINNER_FOODS]
))
