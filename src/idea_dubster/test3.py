import numpy as np
from sentence_transformers import SentenceTransformer
from numpy import dot
from numpy.linalg import norm
import gradio as gr

# Määritellään ideaali ja anti-ideaali
IDEAL_DEFINITION = "A perfect day with calm wind, clear blue skies, no precipitation, and temperatures between 20–24°C. The air feels crisp and dry, visibility is excellent, and conditions are ideal for outdoor activities, physical well-being, and productivity."

ANTI_IDEAL_DEFINITION = "Severe weather with freezing temperatures, dangerous winds, heavy rain or snow, flooding, and extremely low visibility. Conditions may cause discomfort, health risks, property damage, and disruption to daily life or transportation."

# Ladataan malli
model = SentenceTransformer("all-mpnet-base-v2")

# Lasketaan akselin vektorit
vec_a = model.encode(IDEAL_DEFINITION)
vec_b = model.encode(ANTI_IDEAL_DEFINITION)
axis_vector = vec_b - vec_a
axis_x = axis_vector / norm(axis_vector)
axis_length = norm(axis_vector)
scaled_axis_length = axis_length / 2

def fixed_semantic_axis_score(definition):
    vec = model.encode(definition)
    relative = vec - vec_a
    x_proj = dot(relative, axis_vector)
    score = (1 - (x_proj / scaled_axis_length)) * 100
    return max(0, min(score, 100))

def visualize_score(definition):
    score = fixed_semantic_axis_score(definition)
    explanation = f"Score: {score:.2f} (0=Anti-Ideal, 100=Ideal)"
    return score, explanation

# Gradio UI
with gr.Blocks() as demo:
    gr.Markdown("""# Semantic Projection Visualizer\nType a semantic element below. The model will position it on a semantic scale from Anti-Ideal (0) to Ideal (100).""")
    
    textbox = gr.Textbox(label="Enter a 'test' phrase", placeholder="Describe your revenue model here...")
    output_score = gr.Slider(label="Semantic Score", minimum=0, maximum=100, step=0.1)
    output_text = gr.Textbox(label="Explanation")

    textbox.change(fn=visualize_score, inputs=textbox, outputs=[output_score, output_text])

demo.launch()

