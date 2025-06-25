import numpy as np
from sentence_transformers import SentenceTransformer
from numpy import dot
import pandas as pd
from numpy.linalg import norm
import json

#moikka

class fcp_score:
    
    def __init__(self):
        self.model = model = SentenceTransformer("all-mpnet-base-v2")
        self.bmc_semantic_vectors = {
    "business_novelty": {
        "key_partners": {
            "ideal": None,
            "anti_ideal": None
        },
        "key_activities": {
            "ideal": None,
            "anti_ideal": None
        },
        "key_resources": {
            "ideal": None,
            "anti_ideal": None
        },
        "value_propositions": {
            "ideal": None,
            "anti_ideal": None
        },
        "customer_relationships": {
            "ideal": None,
            "anti_ideal": None
        },
        "channels": {
            "ideal": None,
            "anti_ideal": None
        },
        "revenue_streams": {
            "ideal": None,
            "anti_ideal": None
        }
    },
    "customer_novelty": {
        "customer_segments": {
            "ideal": None,
            "anti_ideal": None
        },
        "value_propositions": {
            "ideal": None,
            "anti_ideal": None
        },
        "customer_relationships": {
            "ideal": None,
            "anti_ideal": None
        },
        "channels": {
            "ideal": None,
            "anti_ideal": None
        },
        "key_activities": {
            "ideal": None,
            "anti_ideal": None
        }
    },
    "impact": {
        "cost_structure": {
            "ideal": None,
            "anti_ideal": None
        },
        "revenue_streams": {
            "ideal": None,
            "anti_ideal": None
        },
        "key_resources": {
            "ideal": None,
            "anti_ideal": None
        },
        "value_propositions": {
            "ideal": None,
            "anti_ideal": None
        },
        "customer_segments": {
            "ideal": None,
            "anti_ideal": None
        }
    }
}
        #kovakoodataan ensimmäinen ideaali-anti-ideaali versio
        self.bmc_semantic_profiles1 = {
    "business_novelty": {
        "key_partners": {
            "ideal": "An ideal partner network brings strategic capabilities, co-innovation, and access to unique assets or markets that would be hard to build internally.",
            "anti_ideal": "Partnerships are generic, transactional, or redundant—offering no strategic value or differentiation from competitors."
        },
        "key_activities": {
            "ideal": "Key activities are focused, innovative, and directly tied to delivering unique value—often leveraging proprietary methods or technology.",
            "anti_ideal": "Activities are routine, operationally bloated, or irrelevant to the core value proposition—offering no competitive edge."
        },
        "key_resources": {
            "ideal": "The business leverages unique and hard-to-replicate resources—such as proprietary technology, brand equity, or specialized talent.",
            "anti_ideal": "Resources are generic, easily available in the market, and do not contribute to any unique capability or advantage."
        },
        "value_propositions": {
            "ideal": "A compelling and differentiated value proposition that solves real problems in a novel way and creates measurable customer impact.",
            "anti_ideal": "A vague, undifferentiated offering that mimics existing solutions and fails to resonate with customer needs."
        },
        "customer_relationships": {
            "ideal": "Customer relationships are personalized, trust-based, and continuously enhanced using data and feedback.",
            "anti_ideal": "Interactions are impersonal, transactional, or inconsistent—resulting in low customer retention or engagement."
        },
        "channels": {
            "ideal": "Channels are integrated, customer-centric, and optimized for convenience, efficiency, and brand coherence.",
            "anti_ideal": "Channels are fragmented, outdated, or disconnected from how customers actually prefer to interact."
        },
        "revenue_streams": {
            "ideal": "Revenue streams are diversified, recurring, and aligned with the value delivered—enabling long-term sustainability.",
            "anti_ideal": "Revenues are one-off, unreliable, or misaligned with customer value, making growth and sustainability difficult."
        }
    },
    "customer_novelty": {
        "customer_segments": {
            "ideal": "The business serves clearly defined, high-potential segments with tailored offerings and deep understanding of their needs.",
            "anti_ideal": "Customer segments are too broad, poorly defined, or selected without insight—leading to diluted focus and weak fit."
        },
        "value_propositions": {
            "ideal": "A compelling and differentiated value proposition that solves real problems in a novel way and creates measurable customer impact.",
            "anti_ideal": "A vague, undifferentiated offering that mimics existing solutions and fails to resonate with customer needs."
        },
        "customer_relationships": {
            "ideal": "Customer relationships are personalized, trust-based, and continuously enhanced using data and feedback.",
            "anti_ideal": "Interactions are impersonal, transactional, or inconsistent—resulting in low customer retention or engagement."
        },
        "channels": {
            "ideal": "Channels are integrated, customer-centric, and optimized for convenience, efficiency, and brand coherence.",
            "anti_ideal": "Channels are fragmented, outdated, or disconnected from how customers actually prefer to interact."
        },
        "key_activities": {
            "ideal": "Key activities are focused, innovative, and directly tied to delivering unique value—often leveraging proprietary methods or technology.",
            "anti_ideal": "Activities are routine, operationally bloated, or irrelevant to the core value proposition—offering no competitive edge."
        }
    },
    "impact": {
        "cost_structure": {
            "ideal": "An ideal cost structure is lean, scalable, and aligned with value creation, enabling sustainable growth and adaptability.",
            "anti_ideal": "Cost structure is inefficient, and misaligned with value creation—characterized by high fixed costs, low scalability, and spending on non-core activities."
        },
        "revenue_streams": {
            "ideal": "Revenue streams are diversified, recurring, and aligned with the value delivered—enabling long-term sustainability.",
            "anti_ideal": "Revenues are one-off, unreliable, or misaligned with customer value, making growth and sustainability difficult."
        },
        "key_resources": {
            "ideal": "Resources not only provide competitive advantage but also enable positive social or environmental impact—such as open data, clean energy, or inclusive talent.",
            "anti_ideal": "Resources are misused, unsustainable, or exploitative—damaging long-term value and stakeholder trust."
        },
        "value_propositions": {
            "ideal": "Delivers measurable improvement to lives, ecosystems, or systems—not just customer satisfaction but real-world impact.",
            "anti_ideal": "Adds no meaningful value or may even harm users, communities, or the environment."
        },
        "customer_segments": {
            "ideal": "Targets underserved or high-impact segments where positive change or systemic improvement can be achieved.",
            "anti_ideal": "Focuses only on short-term profits from overexploited, saturated, or vulnerable segments without regard for equity or need."
        }
    }
}
        
        #ladataan toinen ideaali-anti-ideaali versio
        with open("/Users/erikstandard/Desktop/AI-CTO/src/idea_dubster/semantic_profiles2.json") as f:
            self.bmc_semantic_profiles2 = json.load(f)


        #self.bmc_semantic_vectors_done = self.populate_semantic_vectors() #tämä funktio muuttaa bmc:n vektoreiksi ja tallentaa uuteen sanakirjaan
        self.bmc_semantic_profiles2_done = self.populate_semantic_vectors2() #tämä funktio muuttaa bmc:n vektoreiksi ja tallentaa uuteen sanakirjaan
    
    def populate_semantic_vectors(self):
        #init funktio 
        #tämä funktio muuttaa ideaali_bmc:n vektoreiksi ja tallentaa uuteen sanakirjaan
        #tämä tulee tehdä aina kun app käynnistetään 
        for category, items in self.bmc_semantic_vectors.items():
            for key in items:
                ideal_text = self.bmc_semantic_profiles[category][key]["ideal"]
                anti_ideal_text = self.bmc_semantic_profiles[category][key]["anti_ideal"]
                self.bmc_semantic_vectors[category][key]["ideal"] = self.model.encode(ideal_text)
                self.bmc_semantic_vectors[category][key]["anti_ideal"] = self.model.encode(anti_ideal_text)
        return self.bmc_semantic_vectors

    def populate_semantic_vectors2(self):
        """
        Tämä funktio rakentaa semanttiset projektioakselit multi-example erotusvektoreiden keskiarvona.
        """
        # Init uusi sanakirja joka tallentaa lopputuloksen
        semantic_vectors = {}

        for category, fields in self.bmc_semantic_profiles2.items():
            semantic_vectors[category] = {}

            for field, examples in fields.items():
                # Haetaan kaikki lauseparit
                ideal_list = examples["ideal"]
                anti_ideal_list = examples["anti_ideal"]

                # Enkoodataan kaikki lauseet vektoreiksi
                ideal_vectors = [self.model.encode(ideal) for ideal in ideal_list]
                anti_ideal_vectors = [self.model.encode(anti) for anti in anti_ideal_list]

                # Lasketaan erotusvektorit
                difference_vectors = [anti - ideal for ideal, anti in zip(ideal_vectors, anti_ideal_vectors)]

                # Erotusvektoreiden keskiarvo (robustimpi akseli)
                mean_difference_vector = sum(difference_vectors) / len(difference_vectors)

                # Tallennetaan tulos
                semantic_vectors[category][field] = {
                    "axis_vector": mean_difference_vector,  # tämä on nyt normalisoimaton akselivektori
                    "ideal_mean": sum(ideal_vectors) / len(ideal_vectors),  # tarvitaan pisteen projektiota varten
                }

        return semantic_vectors


    def bmc_fcp_score1(self, model, bmc_semantic_vectors, bmc_regular_form):
        """
        Laskee semanttisen pisteytyksen yhdelle BMC-rakenteelle yhden ideaali vastaideaali parin semanttiselle projektio akselille.
        Palauttaa tulokset jaoteltuna samoihin kategorioihin kuin self.bmc_semantic_profiles.
        """
        scores = {
            "business_novelty": {},
            "customer_novelty": {},
            "impact": {}
        }

        for category, fields in bmc_semantic_vectors.items():
            for field, vector_pair in fields.items():
                if field in bmc_regular_form[category] and bmc_regular_form[category][field]:
                    vec_ideal = vector_pair["ideal"]
                    vec_anti = vector_pair["anti_ideal"]
                    axis_vector = vec_anti - vec_ideal
                    axis_length = norm(axis_vector)
                    scaled_axis_length = axis_length / 2

                    if axis_length == 0:
                        scores[category][field] = 50.0
                        continue

                    axis_x = axis_vector / axis_length
                    vec_test = model.encode(bmc_regular_form[category][field])
                    relative = vec_test - vec_ideal
                    x_proj = dot(relative, axis_vector)
                    score = (1 - (x_proj / scaled_axis_length)) * 100
                    scores[category][field] = round(float(max(0, min(score, 100))), 2)
        return scores
    
    def bmc_fcp_score_multi(self, model, bmc_semantic_vectors, bmc_regular_form):
        """
        Laskee semanttisen pisteytyksen BMC-rakenteelle käyttäen useiden lauseparien pohjalta laskettua akselia.
        """
        scores = {
            "business_novelty": {},
            "customer_novelty": {},
            "impact": {}
        }

        for category, fields in bmc_semantic_vectors.items():
            for field, vector_data in fields.items():
                if field in bmc_regular_form[category] and bmc_regular_form[category][field]:
                    axis_vector = vector_data["axis_vector"]
                    ideal_mean = vector_data["ideal_mean"]

                    axis_length = norm(axis_vector)
                    if axis_length == 0:
                        scores[category][field] = 50.0
                        continue

                    vec_test = model.encode(bmc_regular_form[category][field])
                    relative = vec_test - ideal_mean
                    x_proj = dot(relative, axis_vector)

                    # Skaalataan kuten aiemmin (prosenttiasteikko 0-100)
                    scaled_axis_length = axis_length / 2
                    score = (1 - (x_proj / scaled_axis_length)) * 100
                    score = round(float(max(0, min(score, 100))), 2)

                    scores[category][field] = score
                else:
                    scores[category][field] = 50.0  # Jos data puuttuu, neutraali default

        return scores

if __name__ == "__main__":
    fcp = fcp_score()
    model = fcp.model

    # 1. Lue lähdedata
    with open("/Users/erikstandard/Desktop/AI-CTO/src/idea_dubster/wsa_grid_bmc.json") as f:
        bmc_data = json.load(f)

    all_scores = []

    # 2. Käsittele kaikki BMC:t
    for entry in bmc_data:
        print(entry)
        #result = fcp.bmc_fcp_score1(model, fcp.bmc_semantic_vectors, entry) WANHA VERSIO TAPAUKSELLE MONO SEMANTIC PROJEKTIOAKSELI
        result = fcp.bmc_fcp_score_multi(model, fcp.bmc_semantic_profiles2_done, entry)
        all_scores.append(result)

    #tallenna multi-scores json tiedostoon
    with open("/Users/erikstandard/Desktop/AI-CTO/src/idea_dubster/bmc_semantic_scores_multi.json", "w") as f:
        json.dump(all_scores, f, indent=4)
