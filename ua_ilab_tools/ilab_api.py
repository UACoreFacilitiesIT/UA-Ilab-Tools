#!/usr/bin/env python
"""A host of tools that interact with the ilab REST database."""
from ua_generic_rest_api import ua_generic_rest_api
from bs4 import BeautifulSoup


class IlabApi(ua_generic_rest_api.GenericRestApi):
    """The object that holds the stache environment variables."""
    def __init__(self, core_id, auth_creds):
        host = f"https://api.ilabsolutions.com/v1/cores/{core_id}/"
        super().__init__(host, auth_creds, "page")

    def get(self, endpoints, parameters=None, get_all=True, total_pages=None):
        response = super().get(endpoints, parameters)
        if get_all:
            first_page_soup = BeautifulSoup(response[0].text, "xml")
            total_pages = first_page_soup.find("total-pages")
            if total_pages:
                total_pages = int(total_pages.text)
                return super().get(endpoints, parameters, total_pages)

        return response
