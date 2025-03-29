import requests
import openai

class CrunchbaseService:
    def __init__(self, api_key, openai_api_key, project_name, project_description):
        """
        Initializes the CrunchbaseService with the given API key, OpenAI API key, project name, and project description.
        :param api_key: Crunchbase API key
        :param openai_api_key: OpenAI API key
        :param project_name: Name of the project to pull data for
        :param project_description: Description of the project
        """
        self.api_key = api_key
        self.openai_api_key = openai_api_key
        self.project_name = project_name
        self.project_description = project_description
        self.data = None

    def generate_search_query(self):
        """
        Generates a search query from the project description using GPT.
        :return: Search query string
        """
        openai.api_key = self.openai_api_key
        prompt = f"Generate a concise search query for the following project description:\n\n{self.project_description}"
        response = openai.Completion.create(
            engine="gpt-4o",
            prompt=prompt,
            max_tokens=50,
            n=1,
            stop=None,
            temperature=0.7,
        )
        query = response.choices[0].text.strip()
        return query

    def fetch_data(self):
        """
        Fetches data from Crunchbase for the given project name.
        """
        query = self.generate_search_query()
        url = f"https://api.crunchbase.com/v3.1/odm-organizations?query={query}&user_key={self.api_key}"
        response = requests.get(url)
        if response.status_code == 200:
            self.data = response.json()
        else:
            print(f"Error fetching data from Crunchbase: {response.status_code}")
            self.data = None

    def compute_customer_novelty(self):
        """
        Computes the customer novelty based on the number of similar business ideas found on Crunchbase.
        :return: Customer novelty score
        """
        if not self.data:
            print("No data available to compute customer novelty.")
            return None

        n = len(self.data['data']['items'])
        z = sum(item['properties']['heat_score'] for item in self.data['data']['items']) / n if n > 0 else 1
        customer_novelty = 1 / (1 + n / z)
        return customer_novelty

# Example usage
if __name__ == "__main__":
    api_key = "your_crunchbase_api_key"
    openai_api_key = "your_openai_api_key"
    project_name = "example_project"
    project_description = "An AI-powered smart assistant that helps users manage their daily tasks."
    service = CrunchbaseService(api_key, openai_api_key, project_name, project_description)
    service.fetch_data()
    novelty_score = service.compute_customer_novelty()
    print(f"Customer Novelty Score: {novelty_score}")