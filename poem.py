import random

poems = [
    "Mal pipee suwanda dei,\nSulang awith ewa aran yai,\nHitha mage oyawa hoyai,\nOya koheda manda dan nidiyai!",
    "Kalu wara ahasata handa payanawa,\nTharu tika eha meha yanawa,\nMage hitha oyata kawi liyanawa,\nEth oya kora kora nidi yanawa.",
    "Punchi punchi tharu ahasa puraa,\nLassanay reyak gane balan unama,\nOya inna thena kiyanna eda,\nMan ennam igilila heta."
]

def get_random_poem():
    return random.choice(poems)
