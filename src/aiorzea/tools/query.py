from typing import Optional, Any, Annotated
import requests
import time

from aiorzea.tools.base import BaseTool


class APIQueryTool(BaseTool):

    def __init__(self, base_url: str, api_key: Optional[str] = None, *args, **kwargs):
        self.base_url = base_url
        self.api_key = api_key
        super().__init__(*args, **kwargs)
    

class XIVAPIQueryTool(APIQueryTool):

    name = "XIVAPIQueryTool"

    def __init__(self, api_key: Optional[str] = None, *args, **kwargs):
        self.sheets = []
        super().__init__(base_url="https://v2.xivapi.com", api_key=api_key)

    def build(self):
        self.build_sheets()

    def build_sheets(self):
        response = requests.get(
            f"{self.base_url}/api/sheet"
        )
        self.sheets = list(map(lambda x: x["name"], response.json()["sheets"]))

    def __call__(
            self, 
            sheets: str, 
            fields: str, 
            queries: str
        ) -> Annotated[list[dict], "Results of the query"]:
        """
        Query the XIVAPI for the given sheets, fields, and queries.

        Parameters
        ----------
        sheets: str
            The sheets to query. It should be a comma-separated 
            list of sheet names. Common ones include:
            - `Item`: Game items.
            - `Achievement`: Achievements.
            - `Mount`: Mounts.
            - `Action`: Skills and actions.
        fields: str
            The fields to return. It should be a comma-separated list 
            of field names. Available fields can be found in the API 
            documentation for each sheet.
        queries: str
            The queries to search for. A query should follow the format
            `[field][operator][value]`. For example:
            `"Name=\"Clarent\""`.
            Note that when the value is a string, it should be in quotes,
            and it is typically capitalized every word.
        
        Returns
        -------
        str
            The results of the query.
        """
        t0 = time.time()

        # Build the search URL
        url = f"{self.base_url}/api/search"
        
        # Set up the query parameters
        params = {
            'sheets': sheets,
            'fields': fields,
            'query': queries,
        }
        
        # Add API key if provided
        if self.api_key:
            params['private_key'] = self.api_key
        
        # Make the request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        
        t1 = time.time()
        if t1 - t0 < 1:
            # Prevent rate limiting
            time.sleep(1 - (t1 - t0))

        return str(response.json()["results"])
    
    def query_item(self, query: str) -> str:
        """Query the XIVAPI for an item.

        Parameters
        ----------
        query: str
            The queries to search for. A query should follow the format
            `[field][operator][value]`. For example:
            `"Name=\"Clarent\""`.
            Note that when the value is a string, it should be in quotes,
            and it is typically capitalized every word.
        
        Returns
        -------
        str
            The results of the query.
        """
        return self(sheets="Item", fields="*", queries=query)
