import pandas as pd
import matplotlib.pyplot as plt
import json
import plotly.express as px 
import numpy as np

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
        # Painokertoimet
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
        return sum(float(row[k]) * w for k, w in weights.items())

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
        # WSA-pisteet
        self.df["business_novelty_score"] = self.df_business.apply(lambda row: self.weighted_sum(row, self.business_novelty_weights), axis=1)
        self.df["customer_novelty_score"] = self.df_customer.apply(lambda row: self.weighted_sum(row, self.customer_novelty_weights), axis=1)
        self.df["impact_score"] = self.df_impact.apply(lambda row: self.weighted_sum(row, self.impact_weights), axis=1)

        # Rankingit
        self.df["business_novelty_rank"] = self.df["business_novelty_score"].rank(ascending=False).astype(int)
        self.df["customer_novelty_rank"] = self.df["customer_novelty_score"].rank(ascending=False).astype(int)
        self.df["impact_rank"] = self.df["impact_score"].rank(ascending=False).astype(int)

        # rankingin + viite alkuperäiseen
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


bmc_collections = {
    "huonoin": {
        "business_novelty": {
            "key_partners": 56.28,
            "key_activities": 63.05,
            "key_resources": 50.15,
            "value_propositions": 65.54,
            "customer_relationships": 40.44,
            "channels": 58.39,
            "revenue_streams": 57.85
        },
        "customer_novelty": {
            "customer_segments": 37.85,
            "value_propositions": 60.15,
            "customer_relationships": 51.7,
            "channels": 42.7,
            "key_activities": 28.09
        },
        "impact": {
            "cost_structure": 43.4,
            "revenue_streams": 68.09,
            "key_resources": 60.64,
            "value_propositions": 29.0,
            "customer_segments": 52.97
        }
    },
    "mid": {
        "business_novelty": {
            "key_partners": 65.93,
            "key_activities": 68.95,
            "key_resources": 68.61,
            "value_propositions": 55.38,
            "customer_relationships": 74.85,
            "channels": 67.87,
            "revenue_streams": 73.46
        },
        "customer_novelty": {
            "customer_segments": 76.87,
            "value_propositions": 57.05,
            "customer_relationships": 64.26,
            "channels": 66.07,
            "key_activities": 56.48
        },
        "impact": {
            "cost_structure": 50.76,
            "revenue_streams": 68.98,
            "key_resources": 62.28,
            "value_propositions": 53.7,
            "customer_segments": 59.92
        }
    },
    "paras": {
        "business_novelty": {
            "key_partners": 71.73,
            "key_activities": 70.36,
            "key_resources": 56.43,
            "value_propositions": 68.04,
            "customer_relationships": 61.84,
            "channels": 72.57,
            "revenue_streams": 64.87
        },
        "customer_novelty": {
            "customer_segments": 68.16,
            "value_propositions": 62.09,
            "customer_relationships": 65.32,
            "channels": 84.26,
            "key_activities": 70.71
        },
        "impact": {
            "cost_structure": 53.56,
            "revenue_streams": 63.0,
            "key_resources": 61.83,
            "value_propositions": 61.69,
            "customer_segments": 66.68
        }
    }, 
    "testi": {
    'business_novelty': {
        'key_partners': 36.62, 
        'key_activities': 45.9, 
        'key_resources': 44.71, 
        'value_propositions': 51.9, 
        'customer_relationships': 30.14, 
        'channels': 52.02, 
        'revenue_streams': 46.03}, 
    'customer_novelty': {
        'customer_segments': 59.16, 
        'value_propositions': 51.9, 
        'customer_relationships': 30.14, 
        'channels': 52.02, 
        'key_activities': 45.9}, 
    'impact': {
        'cost_structure': 15.87, 
        'revenue_streams': 46.03, 
        'key_resources': 33.64, 
        'value_propositions': 30.51, 
        'customer_segments': 17.91}}
}

data = []
mcdm = MCDM()
# Kerätään tiedot visualisointia varten
for name, bmc in bmc_collections.items():
    ranking = mcdm.calculate_single_ranking_wsa(bmc)
    print(ranking)
    data.append({
        "Name": name,
        "BN_Rank": ranking["business_novelty_rank"],
        "CN_Rank": ranking["customer_novelty_rank"],
        "Impact_Rank": ranking["impact_rank"]
    })

df = pd.DataFrame(data)

# Visualisointi: X = BN, Y = CN, väri = Impact
plt.figure(figsize=(8, 6))
scatter = plt.scatter(
    df["BN_Rank"],
    df["CN_Rank"],
    c=df["Impact_Rank"],
    cmap="viridis",
    s=150,
    edgecolors="black"
)

# Annotointi
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
plt.show()