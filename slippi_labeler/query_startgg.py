import requests
import traceback

STARTGG_ENDPOINT = "https://api.start.gg/gql/alpha"
PAGE_SIZE = 500


class StartClient:
    def __init__(self, token=None):
        self.token = StartClient.load_token()

    def load_token():
        # TODO: Find a better way to load a token
        return open("/home/coy/code/slippi-website/slippi_files/token").readline()

    def query_start(self, query: str, variables: str):
        return requests.post(
            STARTGG_ENDPOINT,
            json={"query": query, "variables": variables},
            headers={"Authorization": f"Bearer {self.token}"},
        )

    def get_participants(self, slug: str):
        try:
            results = self.query_start(
                f"""
                    query GetAttendees($tourneySlug: String!) {{
                        tournament(slug: $tourneySlug) {{
                            name
                            participants (query: {{ perPage: {PAGE_SIZE} }}) {{
                                nodes {{
                                    gamerTag
                                }}
                            }}
                        }}
                    }}
                """,
                {"tourneySlug": slug},
            )
            request_data = results.json()["data"]["tournament"]
            return {
                "tournament_name": request_data["name"],
                "participants": [
                    node["gamerTag"] for node in request_data["participants"]["nodes"]
                ],
            }
        except Exception:
            # TODO figure out logging
            print(traceback.format_exc())
            return None
