#bmc_semantic_profiles vektorization
import numpy as np
from sentence_transformers import SentenceTransformer
from numpy import dot
import pandas as pd
from numpy.linalg import norm
import json
import os
import plotly.express as px 
import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.pyplot as plt
import json
import plotly.express as px 
import numpy as np

class fcp_score:
    
    def __init__(self):
        print("Initializing fcp_score class...")
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
        #self.bmc_semantic_vectors_done = self.populate_semantic_vectors() #tämä funktio muuttaa bmc:n vektoreiksi ja tallentaa uuteen sanakirjaan
        profiles_path = os.path.join(os.path.dirname(__file__), ".../idea_dubster/semantic_profiles2.json")
        with open(profiles_path, "r", encoding="utf-8") as f:
            self.bmc_semantic_profiles2 = json.load(f)
            # Standardize keys to use underscores for consistency
            self.bmc_semantic_profiles2 = {
                key.replace(" ", "_"): value
                for key, value in self.bmc_semantic_profiles2.items()
            }
        self.bmc_semantic_profiles2_done = self.populate_semantic_vectors2() #tämä funktio muuttaa bmc:n vektoreiksi ja tallentaa uuteen sanakirjaan
    
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
    
    def populate_semantic_vectors2(self):
        """
        Tämä funktio rakentaa semanttiset projektioakselit multi-example erotusvektoreiden keskiarvona.
        """
        # Init uusi sanakirja joka tallentaa lopputuloksen
        semantic_vectors = {}
        print("Populating semantic vectors for multi-profile BMC...")
        for category, fields in self.bmc_semantic_profiles2.items():
            semantic_vectors[category] = {}

            for field, examples in fields.items():
                # Haetaan kaikki lauseparit
                ideal_list = examples["ideal"]
                anti_ideal_list = examples["anti_ideal"]
                print(f"Ideaalit: {ideal_list}, Anti-ideaalit: {anti_ideal_list}")

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
        print("using WRONG fcp_score function")

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

    def bmc_fcp_score_multi(self, user_given_bmc_dict):
        print("Calculating FCP scores for multi-profile BMC...")
        """
        Laskee semanttisen pisteytyksen käyttäjän syöttämälle BMC-rakenteelle 
        käyttäen multi-profiilista laskettua akselia (multi-lausepareista).
        """
        print("Calculating FCP scores for multi-profile BMC...")
        user_given_bmc_dict_clean = self.bmc_cleaner(user_given_bmc_dict)
        company_name, flat_bmc_data = list(user_given_bmc_dict_clean.items())[0]

        scores = {
            "business_novelty": {},
            "customer_novelty": {},
            "impact": {}
        }

        # Käytetään multi-profiilista luotua projektiodataa
        for category, fields in self.bmc_semantic_profiles2_done.items():
            for field, vector_data in fields.items():
                if field in flat_bmc_data and flat_bmc_data[field]:
                    axis_vector = vector_data["axis_vector"]
                    ideal_mean = vector_data["ideal_mean"]

                    axis_length = norm(axis_vector)
                    if axis_length == 0:
                        scores[category][field] = 50.0
                        continue

                    vec_test = self.model.encode(flat_bmc_data[field])
                    relative = vec_test - ideal_mean
                    x_proj = dot(relative, axis_vector)

                    scaled_axis_length = axis_length / 2
                    score = (1 - (x_proj / scaled_axis_length)) * 100
                    score = round(float(max(0, min(score, 100))), 2)

                    scores[category][field] = score
                else:
                    scores[category][field] = 50.0  # Jos data puuttuu

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

        
        scores_path = os.path.join(os.path.dirname(__file__), ".../idea_dubster/bmc_semantic_scores_multi.json")
        with open(scores_path, "r", encoding="utf-8") as f:
            self.novelty_rank_data = json.load(f)

        self.df = pd.DataFrame(self.novelty_rank_data)
        self.df_business = self.df["business_novelty"].apply(pd.Series)
        self.df_customer = self.df["customer_novelty"].apply(pd.Series)
        self.df_impact = self.df["impact"].apply(pd.Series)

    def weighted_sum(self, row, weights):
        print("Calculating weighted sum...")
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
        print("Calculating rankings using Weighted Sum Approach (WSA)...")
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
        print("Calculating single ranking WSA for new BMC entry...") 
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

        print("palautetaan skaalatut rankingit...")
        print(extended_df.loc[last_index, [
            "business_novelty_scaled", "customer_novelty_scaled", "impact_scaled"
        ]])

        return extended_df.loc[last_index, [
            "business_novelty_scaled", "customer_novelty_scaled", "impact_scaled"
        ]].rename({
            "business_novelty_scaled": "business_novelty_rank",
            "customer_novelty_scaled": "customer_novelty_rank",
            "impact_scaled": "impact_rank"
        }).to_dict()

