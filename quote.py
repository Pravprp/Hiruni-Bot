import random

quotes = [
    "Jeewithe kiyanne hari puduma deyak, amathaka karanna bari eka thanak.",
    "Weredda wena tharamata, eken igena ganna dewal godai.",
    "Sathuta kiyanne salli nemei, hitha sanasimen inna eka.",
    "Pitu passe katha karana aya gana wada wenna epa, eyala kohomath oyata wada pitipasse inne."
]

def get_random_quote():
    return random.choice(quotes)
