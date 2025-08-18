from sentence_transformers import SentenceTransformer
import numpy as np
import json
import os

# Polut
input_path = "/Users/erikstandard/Desktop/AI-CTO/src/idea_dubster/agentic_system_1_ideal.json"
output_path = "/Users/erikstandard/Desktop/AI-CTO/src/idea_dubster/agentic_system_1_idealvectors.json"

# Ladataan malli
model = SentenceTransformer("all-mpnet-base-v2")

# Ladataan alkuperäinen ideaali/anti-ideaali -lauseiden tiedosto
with open(input_path, "r", encoding="utf-8") as f:
    all_ideals = json.load(f)

vectorized_transitions = {}

for transition_key, entry in all_ideals.items():
    print(f"Processing transition: {transition_key}")

    ideal_output = entry.get("ideal_output", [])
    anti_ideal_output = entry.get("anti_ideal_output", [])

    # Tarkistus
    if not ideal_output or not anti_ideal_output:
        print(f"Skipping {transition_key}: missing ideal or anti-ideal outputs.")
        continue

    # Upotetaan lauseet
    ideal_embeddings = model.encode(ideal_output)
    antiideal_embeddings = model.encode(anti_ideal_output)

    # Lasketaan keskiarvot ja projektioakseli
    avg_ideal = np.mean(ideal_embeddings, axis=0)
    avg_antiideal = np.mean(antiideal_embeddings, axis=0)
    semantic_axis = avg_ideal - avg_antiideal

    # Tallennetaan vektorimuodossa
    vectorized_transitions[transition_key] = {
        "avg_ideal": avg_ideal.tolist(),
        "avg_antiideal": avg_antiideal.tolist(),
        "semantic_axis_vector": semantic_axis.tolist()
    }

# Tallennetaan kaikki siirtymät yhteen tiedostoon
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(vectorized_transitions, f, indent=2)

print("✅ All semantic axes stored successfully.")
