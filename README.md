# UA-Ilab-Tools

A set of tools that interact with Ilab's REST database.

## Motivation

Was designed to implement a simple way to interact with Ilab's REST architecture.

## Features

- ilab_api.py contains a class to use simple REST functions such as GET, PUT, POST, and DELETE.
- ua_ilab_tools.py contains a class to interact with the REST architecture outside of the simple REST verbs, such as:
    - get_service requests which returns the service requests with a given status.
    - get_service_cost which returns the cost associated with a given service_id.
    - get_request_charges which returns all of the charges of the request id.
    - get_milestones which returns all of the milestones associated with a service request.
    - get_custom_forms which returns all of the custom forms associated with the request id.
- extract_project_info which gets the relevant project info from a request.
- extract_custom_form_info which gets all of the fields of a form.

## Code Example

```python
from ua_ilab_tools import ilab_api, ua_ilab_tools


api = ilab_api.IlabApi(core_id, auth_creds)
# "token" contains the Authorization information for headers.
tools = ua_ilab_tools.IlabTools(core_id, token)

prj_info = ua_ilab_tools.extract_project_info(soup)
form_info = ua_ilab_tools.extract_custom_form_info(
    req_id, form_id, form_soup)
```

## Installation

```bash
pip install ua-ilab-tools
```

## Tests
The test suite has been migrated to Python's built-in unittest framework and no longer requires Nose.

To run the tests, from the repository root:
```bash
python -m unittest ua_ilab_tools.tests.test_ilab_tools
```
### Note:
- The XML fixture-based tests run completely offline. (No network requests made with token & core_id)
- API-related tests use mocked responses and do not require access to an iLab environment.
- ilab_creds.json is no longer required for running the unit test suite.

## How to Use

- Get general endpoints
- Get information associated with specific service requests.
- Get data associated with specific projects and custom_forms.

## Credits

[sterns1](sterns1@github.com)
[EtienneThompson](etiennethompson@github.com)

## License

MIT
