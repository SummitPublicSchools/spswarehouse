import requests
import json

try:
    from .credentials import canvas_config
except:
    print("No canvas credentials file found in spswarehouse. This could cause issues.")
    canvas_config = None

class CanvasClient():
    def __init__(self, config=None):
        if config is None:
            self.config = canvas_config
        else:
            self.config = config

        self.HOST = self.config["host"]
        self.TOKEN = self.config["api_token"]

    def request(self, method, path, **kwargs):
        """
        Makes an authenticated request to the Canvas API. Follows the semantics of the Requests
        library. Returns a Response object.

        If `path` starts with a "/", it is assumed to be a relative path and the base
        Canvas URL (config["host"]) is prepended
        """
        if path.startswith("/"):
            path = f'{self.HOST}{path}'

        headers = kwargs.setdefault("headers", {})
        kwargs["headers"]["Authorization"] = f"Bearer {self.TOKEN}"

        r = requests.request(method, path, **kwargs)
            
        return r

    def _link_header_to_dict(self, link_header):
        # Turning pagination headers into a dictionary
        # Example:
        #"""
        #<https://summitps.instructure.com/api/v1/courses/2809/modules?page=1&per_page=10>; rel="current",
        #<https://summitps.instructure.com/api/v1/courses/2809/modules?page=2&per_page=10>; rel="next",
        #<https://summitps.instructure.com/api/v1/courses/2809/modules?page=1&per_page=10>; rel="first",
        #<https://summitps.instructure.com/api/v1/courses/2809/modules?page=2&per_page=10>; rel="last"
        #"""
        split_header_list = [l.partition("; rel=") for l in link_header.split(",") ]
        link_header_dict = { type.strip('"') : url.strip("<>") for (url, _, type) in split_header_list }
        
        return link_header_dict

    def get_paginated_json(self, path, **kwargs):
        """
        Helper function for a very common type of API request: a GET request
        where the data to be returned is JSON and may be paginated.

        This function handles following pagination links and returns
        all the data at once. It may make multiple requests to the Canvas
        API.
        """
        r = self.request("GET", path, **kwargs)
        
        if r.status_code != 200:
            print("Received a non-200 status code:", r)
            return None
        
        data = r.json()
        
        # Handling pagination: continue to make
        # requests until Canvas doesn't give us any more pages to follow
        while "LINK" in r.headers:
            link_header_dict = self._link_header_to_dict(r.headers["LINK"])
            if "next" not in link_header_dict:
                # We're done! No more pages
                break
            
            # Still need to fetch more...
            r = self.request("GET", link_header_dict["next"], **kwargs)
            data.extend(r.json())
            
        return data

Canvas = None if canvas_config is None else CanvasClient()
