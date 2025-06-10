import numpy as np
from sentence_transformers import SentenceTransformer
from numpy.linalg import norm
from sklearn.decomposition import PCA
import gradio as gr

# PCA-komponentin poisto:
"""📐 Miten PCA-komponentti poistetaan?
Lasketaan kaikkien embedding-vektorien matriisi, esim. lauseiden embeddingit.

Suoritetaan PCA → löydetään pääkomponentti (vektori u).

Jokaisesta embedding-vektorista v poistetaan se osa, joka projisoituu pääkomponenttiin:


Tämä toimii aivan kuten jos poistaisit varjon valosta — jäljelle jää se, mikä on semanttisesti uniikkia.
"""
def remove_pc(X):
    pca = PCA(n_components=1)
    pc = pca.fit(X).components_
    return X - X @ pc.T @ pc

# Ladataan malli
model = SentenceTransformer("all-mpnet-base-v2")

# Määritellään ideaalit ja anti-ideaalit siten että kummassakin on kolme määritelmää jotka tukevat toisiaan
IDEALS = [
    "A person who consistently acts with compassion, integrity, and a sense of justice.",
    "Someone who helps others selflessly and promotes well-being in their community.",
    "An individual who respects others, contributes positively to society, and values honesty."
]

ANTI_IDEALS = [
    "A person who causes harm intentionally, disregards others, and lies for personal gain.",
    "Someone who manipulates, exploits, or abuses others without remorse.",
    "An individual who fosters division, spreads hate, and thrives on dishonesty."
]

# Lasketaan keskivektorit yhteensä kuudelle lauseelle, jotka kuvaavat ideaalista ja anti-ideaalista semanttista akselia.
# tämä tehdään vasta kun PCA-komponentti on poistettu, jotta saadaan puhdas semanttinen akseli ilman pääkomponentin vaikutusta.
def encode_clean_mean(sentences):
    vecs = model.encode(sentences)
    vecs = remove_pc(vecs)
    return np.mean(vecs, axis=0)

vec_ideal = encode_clean_mean(IDEALS)
vec_anti = encode_clean_mean(ANTI_IDEALS)
axis_vector = vec_ideal - vec_anti
axis_vector /= norm(axis_vector)

# Tämä funktio muodostaa semanttisen projektio pinnan käyttäen projektioetäisyyttä anti-ideaalista suhteessa koko akselin pituuteen.
def fixed_semantic_axis_score(definition):
    vec = remove_pc(model.encode([definition]))[0]
    proj = np.dot(vec - vec_anti, axis_vector)
    axis_length = np.dot(vec_ideal - vec_anti, axis_vector)
    score = (proj / axis_length) * 100
    return round(np.clip(score, 0, 100), 2)

# Tämä loppuosa visualisoi tulokset ja antaa käyttäjälle selityksen siitä, miten pisteytys toimii.
def visualize_score(definition):
    score = fixed_semantic_axis_score(definition)
    explanation = f"Score: {score:.2f} (0=Anti-Ideal, 100=Ideal)"
    return score, explanation

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("""# Semantic Projection Visualizer\nType a semantic element below. The model will position it on a semantic scale from Anti-Ideal (0) to Ideal (100).""")

    textbox = gr.Textbox(label="Enter a 'test' phrase", placeholder="Describe your concept here...")
    output_score = gr.Slider(label="Semantic Score", minimum=0, maximum=100, step=0.1)
    output_text = gr.Textbox(label="Explanation")

    textbox.change(fn=visualize_score, inputs=textbox, outputs=[output_score, output_text])

demo.launch()
