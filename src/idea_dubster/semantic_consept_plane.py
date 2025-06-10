import numpy as np
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer
from numpy import dot
from numpy.linalg import norm


irrelevant_concepts = [
    {
        "label": "Weather forecast",
        "definition": "Tomorrow it will be partly cloudy with a chance of rain."
    },
    {
        "label": "Laptop specifications",
        "definition": "The new model has 16 GB of RAM and a 1 TB SSD."
    },
    {
        "label": "Fruit preference",
        "definition": "Bananas are sweeter than apples and have more potassium."
    },
    {
        "label": "Furniture review",
        "definition": "This sofa is very comfortable and fits well in small spaces."
    },
    {
        "label": "Geographical fact",
        "definition": "Mount Everest is the highest mountain above sea level."
    },
    {
        "label": "Programming language",
        "definition": "Python supports both object-oriented and functional programming."
    },
    {
        "label": "Transport description",
        "definition": "The electric scooter has a range of 25 kilometers."
    },
    {
        "label": "Cooking tip",
        "definition": "Add lemon juice to avocado to prevent browning."
    },
    {
        "label": "Sporting event",
        "definition": "The final score was 3–2 after a dramatic overtime."
    },
    {
        "label": "Fashion opinion",
        "definition": "This jacket goes really well with high-waisted jeans."
    }
]
# Konseptipari
concept_pair = {
    "concept_a": "Good person",
    "definition_a": "A person who treats others kindly, helps the vulnerable, and acts justly.",
    
    "concept_b": "Bad person",
    "definition_b": "A person who mistreats others, acts selfishly, and causes harm to others."
}
# Test sentences
test_concepts = [
    {
        "label": "Violent and cruel",
        "definition": "I kick old ladies on the street and treat everyone badly."
    },
    {
        "label": "Selective helper",
        "definition": "I only help my friend Matias; I treat others badly."
    },
    {
        "label": "Selfless and helpful",
        "definition": "I help everyone who needs help."
    },
    {
        "label": "Randomly apples",
        "definition": "Apples are so good!"
    }
]



#SCP:n muodostaminen
def form_scp(concept_pair):
    model = SentenceTransformer("all-mpnet-base-v2")
    textCD_a = model.encode(model.encode(concept_pair["definition_a"]))
    textCD_b = model.encode(model.encode(concept_pair["definition_b"]))
    scp = textCD_b - textCD_a / norm(textCD_b - textCD_a)
    return scp 

def form_y_axis():
    pass



