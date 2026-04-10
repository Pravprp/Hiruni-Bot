import random

jokes = [
    "Teacher: Lamayine, pol gahak udin yana satekuge namak kiyanna.\nStudent: Malu wekko miss!\nTeacher: Uba dakkada maluwek ahasen yanawa?\nStudent: Na miss, mn dakketh na pol gahe udin yanawa.",
    "Oya dannawada aliya amathaka unama wena de? ... Uta kalisama adinna wenne na!",
    "Doktor: Oyage as penima godak aduy.\nLeda: Eka hodai doctor, me kale dakkama mata loka winaase mathak wenawa!",
    "Kellek kollat: Oya mata adareida?\nKolla: Ow!\nKella: Ehenam tharuwak genath denna.\nKolla: Tharu genna man superman nemei. Oya poddak kannaadiyen balanna, eke thiyena tharuwa hodatama athi."
]

def get_random_joke():
    return random.choice(jokes)
