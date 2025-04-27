from typing import Optional, Any, Annotated
import requests

from aiorzea.tools.base import BaseTool


class APIQueryTool(BaseTool):

    def __init__(self, base_url: str, api_key: Optional[str] = None, *args, **kwargs):
        self.base_url = base_url
        self.api_key = api_key
        super().__init__(*args, **kwargs)
    

class XIVAPIQueryTool(APIQueryTool):

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

    def create_query_string(self, queries: list[list[str]]) -> list[str]:
        if isinstance(queries, str):
            raise TypeError("queries must be a list of lists of strings.")
        if isinstance(queries[0], str):
            queries = [queries]
        res = ""
        for i, q in enumerate(queries):
            res += f"{q[0]}{q[1]}{q[2]}"
            if i < len(queries) - 1:
                res += " "
        return res


    def __call__(
            self, 
            sheets: str, 
            fields: str, 
            queries: list[list[str]]
        ) -> Annotated[list[dict], "Results of the query"]:
        """
        Query the XIVAPI for the given sheets, fields, and queries.

        Parameters
        ----------
        sheets: str
            The sheets to query. It should be a comma-separated 
            list of sheet names. Available sheets can be found in 
            `self.sheets`. Common ones include:
            - `Item`: Game items.
            - `Achievement`: Achievements.
            - `Mount`: Mounts.
            - `Action`: Skills and actions.
        fields: str
            The fields to return. It should be a comma-separated list 
            of field names. Available fields can be found in the API 
            documentation for each sheet.
        queries: list[list[str]]
            The queries to search for. Multiple queries are supported,
            and each query should be a list containig 3 strings: the
            field, the operator, and the value. For example, to give
            multiple queries, you can do:
            `[["ClassJob.Abbreciation", "=", "BRD"], ["ClassJobLevel", "=", "92"]]`.
            Note that when the value is a string giving the name of an
            item, action, etc., it is typically capitalized every word.
        
        Returns
        -------
        list[dict]
            The results of the query.
        """
        # Build the search URL
        url = f"{self.base_url}/api/search"
        
        # Set up the query parameters
        params = {
            'sheets': sheets,
            'fields': fields,
            'query': self.create_query_string(queries),
        }
        
        # Add API key if provided
        if self.api_key:
            params['private_key'] = self.api_key
        
        # Make the request
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise exception for bad status codes
        
        return response.json()["results"]
