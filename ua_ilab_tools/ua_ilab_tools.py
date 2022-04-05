"""Tools that interact with Ilab's REST database."""
import re
import copy
import traceback
from bs4 import BeautifulSoup
from ua_ilab_tools import extract_custom_forms, ilab_api, api_types

ONLY_INT_FIELDS = [
    "Concentration_each_sample", "Concentration", "Volume (uL)",
    "Initial_Number_Slides_or_Punches_each_sample", "Template Length",
    "Template_Length_each_sample"]


SKIP_FORM_PATTERNS = [r"REQUEST A QUOTE.*", r".*NQ.*"]


class IlabConfigError(Exception):
    """The request or form has been configured or altered incorrectly."""


class IlabTools():
    def __init__(self, core_id, token):
        if "Bearer" not in token:
            token = "Bearer " + token
        auth_creds = {
            "Authorization": f"{token}",
            "Content-Type": "application/xml"
        }
        self.api = ilab_api.IlabApi(core_id, auth_creds)

    def get_service_requests(
        self,
        status="processing",
        from_date="2015-01-01T12:00Z",
        specific_uri=None
    ):
        """Get the service requests with the given status from ilab's REST DB.

        Keyword Arguments:
            status (string):
                If you want service requests with a certain status. By default,
                it is 'processing'.
            specific_uri (string):
                If you want a specific endpoint.

        Returns:
            req_uri_to_soup (dict):
                The dictionary that holds all of the
                {service req uris:request soup}. If no service requests are
                found, returns an empty dict.
        """
        req_uri_to_soup = {}
        if specific_uri:
            get_responses = self.api.get(
                f"service_requests/{specific_uri}.xml", get_all=False)
            requests_soup = BeautifulSoup(get_responses[0].text, "xml")
            requests_soup = requests_soup.find("service-request")
            req_uri_to_soup[requests_soup.find("id").string] = requests_soup
        else:
            get_responses = self.api.get(
                "service_requests.xml",
                parameters={"states": status, "from_date": from_date},
                get_all=True)

        # Soup all get responses (multiple pages or not).
        req_paged_soups = [
            BeautifulSoup(response.text, "xml") for response in get_responses]

        # Get every service-request in every page.
        for get_soup in req_paged_soups:
            for req_soup in get_soup.find_all("service-request"):
                req_uri_to_soup[req_soup.find("id").string] = req_soup

        return req_uri_to_soup

    def get_service_cost(self, price_id):
        """Get the cost associated with the given service_id.

        Arguments:
            price_id (string):
                The id associated with a price.

        Returns:
            service_price (namedtuple):
                The calculated price of the service, or None if not found.
        """
        service_price = None
        get_responses = self.api.get("services.xml")

        for response in get_responses:
            services_page_soup = BeautifulSoup(response.text, "xml")
            id_soup = services_page_soup.find(string=price_id)
            if id_soup:
                service_soup = id_soup.find_parent("service")
                price_soup = service_soup.find("price")
                current_price = price_soup.find("price").string
                unit = price_soup.find("unit").find("description").string
                service_price = api_types.Service_Price(
                    price=float(current_price),
                    samples_per_unit=unit)

        return service_price

    def get_request_charges(self, req_id):
        """Get all of the charges of the req_id passed in.

        Arguments:
            req_id(string):
                The unique string of ints that map to a request.

        Returns:
            charges_uri_soup (dict):
                The dict of uri_to_soup of all the charges associated with that
                request. Returns an empty dict if not found.
        """
        get_responses = self.api.get(f"service_requests/{req_id}/charges.xml")
        charge_paged_soups = [
            BeautifulSoup(response.text, "xml") for response in get_responses]

        charges_uri_soup = dict()
        for get_soup in charge_paged_soups:
            for charge in get_soup.find_all("charge"):
                charges_uri_soup[charge.find("id").string] = charge

        return charges_uri_soup

    def get_milestones(self, request_id):
        """Get all of the milestones associated with a service request.

        Arguments:
            request_id (string):
                The unique string of ints that map to a request.

        Returns:
            milestone_name_soup (dict):
                Holds all {milestone name : soup of milestone}. Returns an
                empty dict if not found.
        """
        get_responses = self.api.get(
            f"service_requests/{request_id}/milestones.xml")
        milestone_paged_soups = [
            BeautifulSoup(response.text, "xml") for response in get_responses]

        milestone_name_soup = {}
        for get_soup in milestone_paged_soups:
            for milestone in get_soup.find_all("milestone"):
                name_tag = milestone.find("name")
                if name_tag:
                    milestone_name_soup[name_tag.string] = milestone

        return milestone_name_soup

    def get_custom_forms(self, req_id):
        """Get all of the custom forms of the req_id passed in.

        Arguments:
            req_id (string):
                The unique string of ints that map to a request.

        Returns:
            forms_uri_to_soup (dict):
                The dictionary that holds all of the
                {custom form uris: form_soup}. Returns an empty dict if not
                found.
        """
        get_responses = self.api.get(
            f"service_requests/{req_id}/custom_forms.xml")
        form_paged_soups = [
            BeautifulSoup(response.text, "xml") for response in get_responses]

        forms_uri_to_soup = {}
        for get_soup in form_paged_soups:
            for form in get_soup.find_all("custom-form"):
                forms_uri_to_soup[form.find("id").string] = form

        return forms_uri_to_soup


def extract_project_info(req_soup, full_name=False):
    """Extract the relevant project info from a request.

    Arguments:
        req_soup (BS4 soup object):
            The soup of the request.
        full_name (boolean):
            Whether or not to capture the entire project name or just the last
            hyphenated element.

    Returns:
        prj_info (Project):
            The required info to post a project.
    """
    if full_name:
        prj_name = req_soup.find("name").string
    else:
        prj_name = req_soup.find("name").string.split('-')[-1]
    res_name = req_soup.find("owner").find("name").string
    email = req_soup.find("owner").find("email").string
    # NOTE: Change this line to your own institution's email domain.
    if "email.arizona.edu" in email:
        res_lab = "internal"
    else:
        res_lab = "external"

    # Replace all not ascii chars with ascii ones, and any symbols with '-'.
    prj_res = api_types.Researcher(
        extract_custom_forms._sanitize_text(res_name.split()[0]),
        extract_custom_forms._sanitize_text(res_name.split()[-1]),
        extract_custom_forms._sanitize_text(res_lab),
        email,
        "")
    prj_info = api_types.Project(prj_name, prj_res)

    return prj_info


def extract_custom_form_info(req_id, form_id, form_soup):
    """Extract all of the fields passed into the form.

    Arguments:
        req_id (String):
            The unique string of ints that map to a request (URI).
        form_id (String):
            The unique string of ints that map to a form.
        form_soup (BeautifulSoup object):
            The soup of the form you want to parse.

    Returns:
        form_info (CustomForm):
            The CustomForm object with all of the form's fields initialized.

    Raises:
        TypeError:
            The form has no fields configured.
        ValueError:
            The form has duplicate samples.
    """

    # If we need any of these types, we can make new methods.
    skip_types = ["charges", "file", "table", "help", "file_no_upload"]
    field_strategy = {
        "handsontable_grid": extract_custom_forms.grid_type,
        "checkbox": extract_custom_forms.checkbox_type,
        "all_others": extract_custom_forms.all_other_types}

    # Find the desired custom form out of all of the form_soup.
    target_form = form_soup.find(string=form_id)
    target_form = target_form.find_parent("custom-form")
    form_soup = target_form

    form_name = form_soup.find("name").string
    fields_soup = form_soup.find("fields")
    form_info = api_types.CustomForm(form_name, req_id, form_id)

    # Get all of the field information.
    for field_soup in fields_soup.find_all("field"):
        field_type = field_soup.find("type").string
        if field_type in skip_types:
            # Do nothing with the field types that we don't yet care about.
            continue

        try:
            field_strategy[field_type](field_soup, form_info)
        except KeyError:
            field_strategy["all_others"](field_soup, form_info)
        except TypeError:
            raise TypeError(
                f"The grid in the {form_info.name} form in request"
                f" {form_info.req_id} has been filled out incorrectly. The"
                f" error message is: {traceback.format_exc()}")

    # Raise an error if a form doesn't have samples.
    if not form_info.samples:
        return form_info

    if form_info.field_to_values.get("duplicate_samples"):
        if form_info.field_to_values["duplicate_samples"] == "Yes":
            b_samples = copy.deepcopy(form_info.samples)
            for a_sample, b_sample in zip(form_info.samples, b_samples):
                a_sample.name += "A"
                b_sample.name += "B"
            form_info.samples = form_info.samples + b_samples

    extract_custom_forms.bind_container_info(form_info)

    # Allows duplicate names if they have different well locations in a
    # plate.
    if form_info.con_type != "96 well plate":
        sample_names = [sample.name for sample in form_info.samples]
        if len(set(sample_names)) != len(sample_names):
            raise ValueError(
                f"There are two or more samples named the same thing in"
                f" request {form_info.req_id}. Please review and edit your"
                f" sample names.")

    for name, value in form_info.field_to_values.items():
        if name in ONLY_INT_FIELDS:
            value = re.sub(r"[^.0-9]", "", value)
        if "_each_sample" in name:
            udf_name = name.replace("_each_sample", "").replace("_", " ")
            for sample in form_info.samples:
                sample.udf_to_value[udf_name] = value

    return form_info
