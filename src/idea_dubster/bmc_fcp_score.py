#bmc_semantic_profiles vektorization
import numpy as np
from sentence_transformers import SentenceTransformer
from numpy import dot
import pandas as pd
from numpy.linalg import norm
import json
import plotly.express as px 
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
import json
import plotly.express as px 
import numpy as np

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
        self.bmc_semantic_profiles = {
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
        self.bmc_semantic_vectors_done = self.populate_semantic_vectors() #tämä funktio muuttaa bmc:n vektoreiksi ja tallentaa uuteen sanakirjaan

    def populate_semantic_vectors(self):
        """
        Converts the 'ideal' and 'anti_ideal' textual profiles in `self.bmc_semantic_profiles`
        into semantic vector representations using the model's `encode` method, and stores
        them in `self.bmc_semantic_vectors`. This process should be performed each time the
        application is started to ensure the vectors are up to date.

        Returns:
            dict: The updated `self.bmc_semantic_vectors` dictionary containing the semantic
            vectors for each category and key.
        """
        for category, items in self.bmc_semantic_vectors.items():
            for key in items:
                ideal_text = self.bmc_semantic_profiles[category][key]["ideal"]
                anti_ideal_text = self.bmc_semantic_profiles[category][key]["anti_ideal"]
                self.bmc_semantic_vectors[category][key]["ideal"] = self.model.encode(ideal_text)
                self.bmc_semantic_vectors[category][key]["anti_ideal"] = self.model.encode(anti_ideal_text)
        return self.bmc_semantic_vectors
    
    def round_scores(self, scores_dict):
        rounded = {}
        for category, fields in scores_dict.items():
            rounded[category] = {
                key: round(float(value), 2) for key, value in fields.items()
            }
        return rounded

    def bmc_cleaner(self, user_given_bmc_dict):
        if "company_name" not in user_given_bmc_dict:
            raise ValueError("Input dictionary is missing 'company_name' key.")

        company_name = user_given_bmc_dict["company_name"]
        keys_to_remove = {"company_name", "assistant_response"}

        # Poistetaan tarpeettomat avaimet
        cleaned_dict = {k: v for k, v in user_given_bmc_dict.items() if k not in keys_to_remove}

        # Palautetaan uusi rakenne, jossa yritysnimi on pääavain
        result = {company_name: cleaned_dict}

        return result
        
    def fcp_score(self, user_given_bmc_dict):

        user_given_bmc_dict_clean = self.bmc_cleaner(user_given_bmc_dict)  # Puhdistetaan käyttäjän antama BMC sanakirja
        company_name, flat_bmc_data = list(user_given_bmc_dict_clean.items())[0]
        
        scores = {
            "business_novelty": {},
            "customer_novelty": {},
            "impact": {}
        }

        for category, fields in self.bmc_semantic_vectors_done.items():
            for field, vector_pair in fields.items():
                if field in flat_bmc_data and flat_bmc_data[field]:
                    vec_ideal = vector_pair["ideal"]
                    vec_anti = vector_pair["anti_ideal"]
                    axis_vector = vec_anti - vec_ideal
                    axis_length = norm(axis_vector)
                    scaled_axis_length = axis_length / 1

                    # Jos vektorit ovat identtiset tai tyhjät, vältä virhe
                    if axis_length == 0:
                        scores[category][field] = 50.0
                        continue

                    axis_x = axis_vector / axis_length
                    vec_test = self.model.encode(flat_bmc_data[field])
                    relative = vec_test - vec_ideal
                    x_proj = dot(relative, axis_vector)
                    score = (1 - (x_proj / scaled_axis_length)) * 100
                    scores[category][field] = float(round(max(0, min(score, 100)), 2))
        #return scores
        return self.round_scores(scores)

class MCDM:
    """
    MCDM (Multi-Criteria Decision Making) Class
    This class is designed to calculate rankings for business novelty, customer novelty, 
    and impact values using MCDM methods such as Weighted Sum Approach (WSA). It also 
    associates the rankings back to each Business Model Canvas (BMC) entry.
    Attributes:
        business_novelty_weights (dict): Weights for calculating business novelty scores.
        customer_novelty_weights (dict): Weights for calculating customer novelty scores.
        impact_weights (dict): Weights for calculating impact scores.
        customer_novelty_rank_data (dict): Data loaded from a JSON file containing semantic scores.
        df (pandas.DataFrame): DataFrame containing the loaded data.
        df_business (pandas.DataFrame): DataFrame containing business novelty data.
        df_customer (pandas.DataFrame): DataFrame containing customer novelty data.
        df_impact (pandas.DataFrame): DataFrame containing impact data.
    Methods:
        weighted_sum(row, weights):
            Calculates the weighted sum for a given row and weights.
        calculate_rankings_wsa():
            and impact, and returns the rankings as a DataFrame.
        calculate_single_ranking_wsa(new_bmc_entry):
            Calculates scaled rankings for a new entry based on weighted scores and existing data.
            Returns a dictionary containing the scaled rankings for business novelty, customer novelty, 
    """
    def __init__(self):
        self.business_novelty_weights = {
            "key_partners": 0.1,
            "key_activities": 0.1,
            "key_resources": 0.1,
            "value_propositions": 0.1,
            "customer_relationships": 0.1,
            "channels": 0.1,
            "revenue_streams": 0.1
        }
        self.customer_novelty_weights = {
            "customer_segments": 0.1,
            "value_propositions": 0.1,
            "customer_relationships": 0.1,
            "channels": 0.1,
            "key_activities": 0.1
        }
        self.impact_weights = {
            "cost_structure": 0.1,
            "revenue_streams": 0.1,
            "key_resources": 0.1,
            "value_propositions": 0.1,
            "customer_segments": 0.1
        }

        
        with open("/Users/erikstandard/Desktop/AI-CTO/src/idea_dubster/semantic_scores_output.json") as f:
            self.customer_novelty_rank_data = json.load(f) 

        self.df = pd.DataFrame(self.customer_novelty_rank_data)
        self.df_business = self.df["business_novelty"].apply(pd.Series)
        self.df_customer = self.df["customer_novelty"].apply(pd.Series)
        self.df_impact = self.df["impact"].apply(pd.Series)

    def weighted_sum(self, row, weights):
        """
        Calculates the weighted sum of values in a row based on the provided weights.

        Args:
            row (dict): A dictionary containing the data row, where keys correspond to the items to be weighted.
            weights (dict): A dictionary mapping the same keys to their respective weight values.

        Returns:
            float: The weighted sum of the values in the row.
        """
        #return sum(float(row[k]) * w for k, w in weights.items())
        return sum(float(row.get(k, 0)) * w for k, w in weights.items())

    def calculate_rankings_wsa(self):
        """
        Calculates rankings based on weighted scores for business novelty, customer novelty, 
        and impact, and returns the rankings.

        The method performs the following steps:
        1. Computes weighted scores for business novelty, customer novelty, and impact 
           using the `weighted_sum` method and respective weights.
        2. Ranks the scores in descending order and assigns integer ranks.
        3. Returns a DataFrame containing the ranks for business novelty, customer novelty, 
           and impact.

        Returns:
            pandas.DataFrame: A DataFrame with columns:
                - 'business_novelty_rank': Rank based on business novelty scores.
                - 'customer_novelty_rank': Rank based on customer novelty scores.
                - 'impact_rank': Rank based on impact scores.
        """
        self.df["business_novelty_score"] = self.df_business.apply(lambda row: self.weighted_sum(row, self.business_novelty_weights), axis=1)
        self.df["customer_novelty_score"] = self.df_customer.apply(lambda row: self.weighted_sum(row, self.customer_novelty_weights), axis=1)
        self.df["impact_score"] = self.df_impact.apply(lambda row: self.weighted_sum(row, self.impact_weights), axis=1)
        self.df["business_novelty_rank"] = self.df["business_novelty_score"].rank(ascending=False).astype(int)
        self.df["customer_novelty_rank"] = self.df["customer_novelty_score"].rank(ascending=False).astype(int)
        self.df["impact_rank"] = self.df["impact_score"].rank(ascending=False).astype(int)

        return self.df[["business_novelty_rank", "customer_novelty_rank", "impact_rank"]]
    
    def calculate_single_ranking_wsa(self, new_bmc_entry):
        """
        Calculate scaled rankings for a new entry based on weighted scores and existing data.

        This method takes a new entry and calculates its rankings relative to an existing dataset
        of 99 entries. It computes weighted scores for three categories: business novelty, 
        customer novelty, and impact. Rankings are scaled such that the best score corresponds 
        to 99 and the worst score corresponds to 0.

        Args:
            new_bmc_entry (dict): A dictionary representing the new entry to be ranked. 
                                  It should contain keys corresponding to the columns 
                                  "business_novelty", "customer_novelty", and "impact".

        Returns:
            dict: A dictionary containing the scaled rankings for the new entry:
                  - "business_novelty_rank": Scaled rank for business novelty.
                  - "customer_novelty_rank": Scaled rank for customer novelty.
                  - "impact_rank": Scaled rank for impact.

        Raises:
            ValueError: If the existing dataset does not contain exactly 99 rows.
        """

        if len(self.df) != 99:
            raise ValueError(f"Vertailudatan koko ei ole 99! Löytyi: {len(self.df)}")
        # Luo tilapäinen laajennettu df (99 + 1 = 100)
        extended_df = pd.concat([self.df, pd.DataFrame([new_bmc_entry])], ignore_index=True)
        # Puretaan osakategoriat
        extended_business = extended_df["business_novelty"].apply(pd.Series)
        extended_customer = extended_df["customer_novelty"].apply(pd.Series)
        extended_impact = extended_df["impact"].apply(pd.Series)

        # Lasketaan WSA-scoret
        extended_df["business_novelty_score"] = extended_business.apply(
            lambda row: self.weighted_sum(row, self.business_novelty_weights), axis=1
        )
        extended_df["customer_novelty_score"] = extended_customer.apply(
            lambda row: self.weighted_sum(row, self.customer_novelty_weights), axis=1
        )
        extended_df["impact_score"] = extended_impact.apply(
            lambda row: self.weighted_sum(row, self.impact_weights), axis=1
        )
        # Rankingit (1 = paras, 100 = huonoin)
        extended_df["business_novelty_rank"] = extended_df["business_novelty_score"].rank(ascending=False, method="min").astype(int)
        
        extended_df["customer_novelty_rank"] = extended_df["customer_novelty_score"].rank(ascending=False, method="min").astype(int)
        
        extended_df["impact_rank"] = extended_df["impact_score"].rank(ascending=False, method="min").astype(int)
        
        
        # Skaalataan: paras = 99, huonoin = 0
        max_rank = len(extended_df) - 1
        extended_df["business_novelty_scaled"] = max_rank - extended_df["business_novelty_rank"] + 1
        extended_df["customer_novelty_scaled"] = max_rank - extended_df["customer_novelty_rank"] + 1
        extended_df["impact_scaled"] = max_rank - extended_df["impact_rank"] + 1

        # Palauta käyttäjän syötteen skaalatut rankingit
        last_index = len(extended_df) - 1
        return extended_df.loc[last_index, [
            "business_novelty_scaled", "customer_novelty_scaled", "impact_scaled"
        ]].rename({
            "business_novelty_scaled": "business_novelty_rank",
            "customer_novelty_scaled": "customer_novelty_rank",
            "impact_scaled": "impact_rank"
        }).to_dict()


if __name__ == "__main__":
    #1 alustetaan käyttäjän antama bmc
    user_given_input_bmc_list = [
   { 
        "company_name": "AMD",
        "assistant_response": "assistant_response",
        "key_partners": "OEMs, system integrators, software vendors, cloud service providers, graphics card partners, and foundries form AMD’s strategic partner network.",
        "key_activities": "AMD focuses on research and development, product design, engineering, and marketing to deliver high-performance computing solutions.",
        "key_resources": "High-value resources include proprietary R&D, supply networks, and expert engineering teams.",
        "value_propositions": "AMD delivers advanced computing solutions that meet the demands of performance-intensive users and scalable infrastructures.",
        "customer_relationships": "Customer support is provided through online communities, forums, phone support, events, and social networks.",
        "channels": "AMD reaches customers via direct websites, live chat, social media, and OEM and partner distribution.",
        "customer_segments": "The company targets distinct user groups such as gamers, OEMs, data centers, and governments for maximum market reach.",
        "cost_structure": "Primary costs include R&D, supply chain management, sales, marketing, and manufacturing.",
        "revenue_streams": "Revenue streams are composed of product sales and licensing agreements targeting both consumer and enterprise markets."
    },
    {
        "company_name": "American Express",
        "assistant_response": "assistant_response",
        "key_partners": "American Express partners with merchants, airlines, retailers, technology firms, and co-branding partners to broaden its service ecosystem.",
        "key_activities": "Core activities include payment processing, marketing, credit risk management, and exceptional customer service.",
        "key_resources": "Human capital and technology systems are key enablers of customer value delivery and operational efficiency.",
        "value_propositions": "American Express adds impact through trust, customer loyalty, and sophisticated financial tools.",
        "customer_relationships": "The business builds strong relationships through premium support, personalized rewards, and targeted service delivery.",
        "channels": "It uses multiple channels including social media, digital platforms, and customer service centers to deliver its value.",
        "customer_segments": "Targeted segments include high-spending individuals, business clients, and global merchant networks.",
        "cost_structure": "Major costs include salaries, technology, transaction processing, marketing, and regulatory compliance.",
        "revenue_streams": "Revenue is derived from financial services fees, merchant transaction fees, and travel and payment-related commissions."
    },
    {
        "company_name": "Accenture",
        "assistant_response": "assistant_response",
        "key_partners": "Accenture partners with technology companies, web service providers, and software firms to deliver integrated solutions.",
        "key_activities": "Key activities involve continuous development of bespoke services to address emerging business problems.",
        "key_resources": "Strategic personnel, including digital marketers and data scientists, form critical assets.",
        "value_propositions": "Accenture positively impacts clients by reducing inefficiencies and driving measurable performance improvements.",
        "customer_relationships": "Customer collaboration and personalized engagement drive long-term relationships.",
        "channels": "Channels include conferences, digital marketing, and direct engagement via events and media.",
        "customer_segments": "Target segments include organizations undergoing digital transformation and seeking scalable growth strategies.",
        "cost_structure": "Primary costs involve subcontractor compensation, administrative expenses, and employee salaries.",
        "revenue_streams": "Revenue is generated from consulting fees and outsourcing agreements."
    },
    {
        "company_name": "Adobe",
        "assistant_response": "assistant_response",
        "key_partners": "Adobe collaborates with tech companies, independent software vendors, and resellers to distribute its creative and digital solutions.",
        "key_activities": "Focused on innovation in digital creativity, Adobe continues refining its design and platform offerings.",
        "key_resources": "The company leverages proprietary IP, skilled human capital, and robust cloud infrastructure.",
        "value_propositions": "Adobe drives societal impact by democratizing digital creation and fostering education.",
        "customer_relationships": "Engagement is fostered through community support and high-quality service.",
        "channels": "Channels include Adobe's official site, online communities, and educational partnerships.",
        "customer_segments": "Key segments include enterprises, creative professionals, students, and educational institutions.",
        "cost_structure": "Main costs stem from research and development, administrative operations, and infrastructure maintenance.",
        "revenue_streams": "Adobe's revenues come from software subscriptions, licenses, and digital media sales."
    },
    {
        "company_name": "Afterpay",
        "assistant_response": "assistant_response",
        "key_partners": "Afterpay collaborates with third-party merchants and logistics providers to deliver seamless payment experiences.",
        "key_activities": "The company focuses on research and development, investment management, and maintaining a streamlined digital platform.",
        "key_resources": "High-value resources include proprietary R&D, supply networks, and expert engineering teams.",
        "value_propositions": "The platform delivers value by enabling interest-free installment payments for consumers and higher conversion rates for merchants.",
        "customer_relationships": "Customer support is maintained through responsive assistance and user engagement across digital platforms.",
        "channels": "Key channels include the website, mobile platforms, and retail integration.",
        "customer_segments": "Target users include online shoppers and global merchants seeking embedded finance solutions.",
        "cost_structure": "Major costs include platform development, logistics coordination, and international subsidiary operations.",
        "revenue_streams": "Revenue is generated from commissions and lead generation services provided to partner vendors."
    },
    {
        "company_name": "Aggregator",
        "assistant_response": "assistant_response",
        "key_partners": "Aggregators rely on third-party application developers and service providers to populate their platform with competitive offers.",
        "key_activities": "Core activities include platform development, sales, and customer service operations.",
        "key_resources": "High-value resources include proprietary R&D, supply networks, and expert engineering teams.",
        "value_propositions": "The platform delivers value by enabling interest-free installment payments for consumers and higher conversion rates for merchants.",
        "customer_relationships": "Customer support is maintained through responsive assistance and user engagement across digital platforms.",
        "channels": "Key channels include the website, mobile platforms, and retail integration.",
        "customer_segments": "Target users include online shoppers and global merchants seeking embedded finance solutions.",
        "cost_structure": "Expenses involve platform maintenance, digital channel development, and personnel costs such as a dedicated sales team.",
        "revenue_streams": "Revenue is generated from commissions and lead generation services provided to partner vendors."
    },
    {
        "company_name": "Airbnb",
        "assistant_response": "assistant_response",
        "key_partners": "Airbnb cooperates with hosts, investors, insurance companies, and payment processors to operate its accommodation platform effectively.",
        "key_activities": "Key activities include platform maintenance, customer service, and continuous user experience research.",
        "key_resources": "Airbnb's main resources are its host community, technical infrastructure, and software development teams.",
        "value_propositions": "It offers affordable accommodation in private homes and a smooth, competitive booking process.",
        "customer_relationships": "Airbnb supports relationships through self-service tools and dedicated customer support.",
        "channels": "Customers are engaged through social media, travel bloggers, and referrals.",
        "customer_segments": "Airbnb serves budget-conscious travelers, local experience seekers, and private hosts.",
        "cost_structure": "Major costs are platform development, customer support operations, and marketing efforts.",
        "revenue_streams": "Income arises from service fees paid by both guests and hosts during transactions."
    },
    {
        "company_name": "ALDI",
        "assistant_response": "assistant_response",
        "key_partners": "ALDI collaborates with manufacturers, logistics providers, and real estate developers to maintain a cost-effective and scalable retail model.",
        "key_activities": "Its core activities are product procurement, store operations, and logistics.",
        "key_resources": "Key resources include its distribution network, brand recognition, and operational model.",
        "value_propositions": "ALDI promises high-quality essentials at the lowest prices.",
        "customer_relationships": "Customer interaction is minimal and streamlined, relying heavily on self-service.",
        "channels": "Sales occur in physical stores supported by flyers, in-store promotions, and limited digital outreach.",
        "customer_segments": "ALDI targets cost-conscious families, single shoppers, and value-oriented consumers.",
        "cost_structure": "The largest costs are product sourcing, real estate, and employee salaries.",
        "revenue_streams": "ALDI generates revenue entirely from physical product sales."
    }
]
    #2 alustetaan luokat
    #fcp = fcp_score()
    #mcdm = MCDM()
    #3 lasketaan fcp score käyttäjän antamalle bmc:lle
    #user_bmc_scores_dict = fcp.fcp_score(user_given_input_bmc_list[0])
   # print("User BMC Scores Dictionary:", user_bmc_scores_dict)
    #4 lasketaan mcdm/wsa rankingi käyttäjän antamalle bmc:lle
    #ranking = mcdm.calculate_single_ranking_wsa(user_bmc_scores_dict)

    import gradio as gr
    import pandas as pd
    import matplotlib.pyplot as plt
    import ast

    fcp = fcp_score()
    mcdm = MCDM()
    data = []  # Lista aiemmista pisteistä
    
    # Funktio, joka ottaa tekstimuotoisen BMC:n, arvioi sen ja piirtää pisteen
    def evaluate_and_plot(bmc_input_text):
        try:
            bmc_dict = ast.literal_eval(bmc_input_text)
            if not isinstance(bmc_dict, dict):
                raise ValueError("Syötteen täytyy olla sanakirja")
        except Exception as e:
            return None, {"error": f"Virhe BMC-syötteessä: {e}"}

        user_bmc_scores_dict = fcp.fcp_score(bmc_dict)
        ranking = mcdm.calculate_single_ranking_wsa(user_bmc_scores_dict)

        # Tallenna visualisointidataan
        company_name = bmc_dict.get("company_name", f"Yritys {len(data)+1}")
        data.append({
            "Name": company_name,
            "BN_Rank": ranking["business_novelty_rank"],
            "CN_Rank": ranking["customer_novelty_rank"],
            "Impact_Rank": ranking["impact_rank"]
        })

        df = pd.DataFrame(data)
        plt.figure(figsize=(8, 6))
        scatter = plt.scatter(
            df["BN_Rank"],
            df["CN_Rank"],
            c=df["Impact_Rank"],
            cmap="viridis",
            s=150,
            edgecolors="black"
        )
        for i in range(len(df)):
            plt.text(df["BN_Rank"][i] + 1, df["CN_Rank"][i], df["Name"][i], fontsize=9, va='center')

        plt.title("Yksi vastaan muut: BMC-rankingit 2D-koordinaatistossa")
        plt.xlabel("Business Novelty Rank")
        plt.ylabel("Customer Novelty Rank")
        plt.xlim(0, 100)
        plt.ylim(0, 100)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.colorbar(scatter, label="Impact Rank")
        plt.tight_layout()

        return plt.gcf(), ranking

    # Gradio-käyttöliittymä
    demo = gr.Interface(
        fn=evaluate_and_plot,
        inputs=gr.Textbox(label="Liitä BMC Canvas sanakirjana", lines=20, placeholder="{\"company_name\": \"Esimerkki Oy\", ...}"),
        outputs=[gr.Plot(label="2D-ranking-visualisointi"), gr.JSON(label="Ranking-tulokset")],
        title="BMC Semanttinen Arviointi & Visualisointi",
        allow_flagging="never"
    )

    demo.launch()