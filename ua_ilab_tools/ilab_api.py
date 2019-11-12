#!/usr/bin/env python
"""A host of tools that interact with the ilab REST database."""
from ua_generic_rest_api import ua_generic_rest_api


class IlabApi(ua_generic_rest_api.GenericRestApi):
    """The object that holds the stache environment variables."""
    def __init__(self, core_id, auth_creds):
        host = f"https://api.ilabsolutions.com/v1/cores/{core_id}/"
        super().__init__(host, auth_creds, "page", page_tag=None)

    def get(self, endpoints, parameters=None, get_all=True, total_pages=None):
        responses = super().get(endpoints, parameters, get_all, total_pages)
        return '\n'.join([response.text for response in responses])
