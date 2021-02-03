import os
import re
import json
from nose.tools import raises
from nose.plugins.attrib import attr
from bs4 import BeautifulSoup
from ua_ilab_tools import extract_custom_forms, ua_ilab_tools


ALL_REQS_SOUP = None


class TestIlabTools():
    def setUp(self):
        DISALLOWED_CHARS = r"[^a-zA-Z0-9:,.]"
        REPLACE_CHARS = "-"
        extract_custom_forms.update_globals(DISALLOWED_CHARS, REPLACE_CHARS)
        creds_path = (os.path.join(
            os.path.split(__file__)[0], "ilab_creds.json"))
        with open(creds_path, 'r') as file:
            creds = json.loads(file.read())
        self.tools = ua_ilab_tools.IlabTools(creds["core_id"], creds["token"])

    def test_get_service_requests_specific_status(self):
        request_map = self.tools.get_service_requests()
        assert request_map.values()
        for value in request_map.values():
            assert value.find("state").text == "processing"

        request_map = self.tools.get_service_requests(status="completed")
        # NOTE: Fails if there are not > 30 completed requests in ilab env.
        assert len(request_map) > 30
        assert request_map.values()
        for value in request_map.values():
            assert value.find("state").text == "completed"

    @attr("env_requests")
    def test_get_service_requests_specific_uri(self):
        self._get_all_requests_singleton()
        specific_req_soup = ALL_REQS_SOUP[0]

        req_id = specific_req_soup.find("id").text
        request_map = self.tools.get_service_requests(specific_uri=req_id)
        assert request_map[req_id].find("id").text == req_id

    def test_get_service_cost(self):
        services_soup = BeautifulSoup(
            self.tools.api.get("services.xml", get_all=False)[0].text, "xml")
        single_soup = services_soup.find("service")
        service_id = single_soup.find("id").text
        price = float(single_soup.find("price").find("price").text)
        unit = single_soup.find("unit").find("description").text

        result = self.tools.get_service_cost(service_id)
        assert result.price == price
        assert result.samples_per_unit == unit

    @attr("env_requests")
    def test_get_request_charges(self):
        self._get_all_requests_singleton()
        for req_soup in ALL_REQS_SOUP:
            charges_url = req_soup.find("list-charges").find("url").text
            if charges_url:
                break

        req_id = charges_url.split('/')[-2]
        get_responses = self.tools.api.get(
            f"service_requests/{req_id}/charges.xml")
        charges_pages_soups = [
            BeautifulSoup(response.text, "xml") for response in get_responses]

        num_charges = 0
        for get_soup in charges_pages_soups:
            num_charges += len(get_soup.find_all("charge"))

        charges = self.tools.get_request_charges(req_id)
        assert len(charges.keys()) == num_charges

    @attr("env_requests")
    def test_get_milestones(self):
        self._get_all_requests_singleton()
        for req_soup in ALL_REQS_SOUP:
            milestone_url = req_soup.find("list-milestones").find("url").text
            if milestone_url:
                break

        req_id = milestone_url.split('/')[-2]
        milestone_map = self.tools.get_milestones(req_id)

        get_responses = self.tools.api.get(
            f"service_requests/{req_id}/milestones.xml")
        milestones_pages_soups = [
            BeautifulSoup(response.text, "xml") for response in get_responses]

        name_tags = list()
        for get_soup in milestones_pages_soups:
            name_tag = get_soup.find("name")
            if name_tag:
                name_tags.append(name_tag)

        if name_tags:
            for tag in name_tags:
                assert tag.text in milestone_map
        else:
            assert milestone_map == {}

    @attr("env_requests")
    def test_get_custom_forms_single_and_multiple_forms_same_request(self):
        self._get_all_requests_singleton()
        custom_form_urls = list()
        for req_soup in ALL_REQS_SOUP:
            req_forms_soups = req_soup.find("list-custom-forms")
            if req_forms_soups:
                custom_form_urls = req_forms_soups.find_all("url")
                if len(custom_form_urls) > 1:
                    break

        req_id = custom_form_urls[0].text.split('/')[-2]
        result = self.tools.get_custom_forms(req_id)
        assert len(custom_form_urls) == len(result)
        for value in result.values():
            assert value.find("id").text == value.find("id").text

    def _get_all_requests_singleton(self):
        global ALL_REQS_SOUP
        if ALL_REQS_SOUP is None:
            get_responses = self.tools.api.get("service_requests.xml")
            request_paged_soups = [
                BeautifulSoup(
                    response.text, "xml") for response in get_responses]

            all_requests_soups = list()
            for get_soup in request_paged_soups:
                for req_soup in get_soup.find_all("service-request"):
                    all_requests_soups.append(req_soup)

            ALL_REQS_SOUP = all_requests_soups

    @attr("env_requests")
    def test_extract_project_info_with_and_without_full_name(self):
        self._get_all_requests_singleton()
        for req_soup in ALL_REQS_SOUP:
            form_url = req_soup.find("list-custom-forms").find("url").text
            if form_url:
                break

        req_url = form_url.replace("/custom_forms.xml", ".xml")
        req_soup = BeautifulSoup(
            self.tools.api.get(req_url)[0].text, "xml")

        prj_name = req_soup.find("name").text
        res_name = req_soup.find("owner").find("name").text
        email = req_soup.find("owner").find("email").text
        # NOTE: Change to your institution's email address.
        if "email.arizona.edu" in email:
            lab_type = "internal"
        else:
            lab_type = "external"

        prj_info = ua_ilab_tools.extract_project_info(req_soup, full_name=True)

        assert prj_info.name == prj_name
        assert prj_info.res.first_name == res_name.split()[0]
        assert prj_info.res.last_name == res_name.split()[-1]
        assert prj_info.res.lab_type == lab_type
        assert prj_info.res.email == email

        prj_info = ua_ilab_tools.extract_project_info(req_soup)

        assert prj_info.name == prj_name.split('-')[-1]

    def test_extract_from_grid_container_name_in_form(self):
        template_path = (os.path.join(
            os.path.split(__file__)[0],
            "extract_from_grid_container_name_in_form.xml"))
        with open(template_path) as file:
            form = file.read()
        form_soup = BeautifulSoup(form, "xml")

        form = ua_ilab_tools.extract_custom_form_info(
            "0", "3275577", form_soup)
        samples = form.samples
        sample_names = [sample.name for sample in samples]

        assert "Empty" not in sample_names
        assert len(samples) == 67
        assert form.field_to_values["container_name"] == "Test-Plate-Name"
        for sample in samples:
            assert "AF" in sample.name
            assert sample.con.name == "Test-Plate-Name"
            assert sample.con.con_type == "96 well plate"
            assert re.search(r"[A-H]:[0-9]{1,2}", sample.location) is not None
            assert "Dilution" in sample.udf_to_value.keys()

    def test_extract_from_grid_container_name_in_grid(self):
        template_path = (os.path.join(
            os.path.split(__file__)[0],
            "extract_from_grid_container_name_in_grid.xml"))
        with open(template_path) as file:
            req = file.read()
        req_soup = BeautifulSoup(req, "xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3256202", req_soup)
        samples = form.samples
        sample_names = [sample.name for sample in samples]
        container_names = [
            "Plate-1", "Plate-2", "Plate-3", "Plate-4", "Plate-5", "Plate-6"]

        assert "Empty" not in sample_names
        assert len(samples) == 540
        assert "Dilution_each_sample" in form.field_to_values.keys()
        for sample in samples:
            assert '-' in sample.name
            assert sample.con.name in container_names
            assert sample.con.con_type == "96 well plate"
            assert re.search(r"[A-H]:[0-9]{1,2}", sample.location) is not None
            assert "Dilution" in sample.udf_to_value.keys()

    # NOTE: These tests are workflow specific, testing the special handling of
    # certain sample fields.
    def test_extract_from_grid_tgm_data(self):
        template_path = (os.path.join(
            os.path.split(__file__)[0], "extract_from_grid_tgm_data.xml"))
        with open(template_path) as file:
            req = file.read()
        req_soup = BeautifulSoup(req, "xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3904550", req_soup)
        samples = form.samples

        assert len(samples) == 19
        for sample in samples:
            assert "TGM Assay List" in sample.udf_to_value.keys()
            assert sample.udf_to_value["TGM Assay List"][-1] != ','

    def test_extract_from_grid_lvs_data(self):
        template_path = (os.path.join(
            os.path.split(__file__)[0], "extract_from_grid_lvs_primers.xml"))
        with open(template_path) as file:
            req = file.read()
        req_soup = BeautifulSoup(req, "xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3923775", req_soup)
        samples = form.samples

        assert len(samples) == 7
        for sample in samples:
            assert "Primer" in sample.udf_to_value.keys()
            assert '*' not in sample.udf_to_value["Primer"]
            assert len(sample.udf_to_value["Primer"].split(',')) == 3

    def test_extract_custom_form_info_samples_con_type_tube(self):
        template_path = (os.path.join(
            os.path.split(__file__)[0],
            "extract_custom_form_info_samples_con_type_tube.xml"))
        with open(template_path) as file:
            req = file.read()
        req_soup = BeautifulSoup(req, "xml")

        samples = ua_ilab_tools.extract_custom_form_info(
            "0", "3271720", req_soup).samples
        sample_names = [
            "UA2001111", "UA2002222", "UA2003333", "UA2004444", "UA2005555"]
        assert len(samples) == len(sample_names)
        for sample in samples:
            assert sample.name in sample_names
            assert sample.con.name in sample_names
            assert sample.con.con_type == "Tube"
            assert sample.location == "1:1"
            assert "TGM Assay List" in sample.udf_to_value.keys()

    def test_extract_from_grid_eight_strip(self):
        # Based off of a request, but required some alteration.
        template_path = (os.path.join(
            os.path.split(__file__)[0],
            "extract_from_grid_con_type_eight_strip.xml"))
        with open(template_path) as file:
            req = file.read()
        req_soup = BeautifulSoup(req, "xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3220469", req_soup)
        samples = form.samples
        sample_names = ["A3", "B13", "H11", "F8", "G2", "C3", "C5", "E6"]
        # assert len(samples) == len(sample_names)
        for sample in samples:
            assert sample.name in sample_names
            assert re.search(r"0-[1-8]", sample.con.name) is not None
            assert sample.con.con_type == "8-well strip"
            assert re.search(r"A:[1-8]", sample.location) is not None
            assert "Volume (uL)" in sample.udf_to_value.keys()

    @raises(TypeError)
    def test_extract_from_grid_eight_strip_too_many_tubes(self):
        template_path = (os.path.join(
            os.path.split(__file__)[0],
            "extract_from_grid_con_type_eight_strip_too_many_tubes.xml"))
        with open(template_path) as file:
            req = file.read()
        req_soup = BeautifulSoup(req, "xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3220469", req_soup)
        samples = form.samples
        sample_names = ["A3", "B13", "H11", "F8", "G2", "C3", "C5", "E6"]
        assert len(samples) == len(sample_names)
        for sample in samples:
            assert sample.name in sample_names
            assert re.search(r"2220920-[1-8]", sample.con.name) is not None
            assert sample.con.con_type == "8-well strip"
            assert re.search(r"A:[1-8]", sample.location) is not None
            assert "Volume (uL)" in sample.udf_to_value.keys()

    def test_extract_custom_form_info_samples_not_ascii_characters(self):
        template_path = (os.path.join(
            os.path.split(__file__)[0],
            "extract_custom_form_info_samples_not_ascii_characters.xml"))
        template_path
        with open(template_path) as file:
            req = file.read()
        req_soup = BeautifulSoup(req, "xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3209463", req_soup)
        samples = form.samples
        for sample in samples:
            assert re.search(r"[^0-9A-Za-z-]", sample.con.name) is None

    def test_translate_to_well(self):
        for i in range(1, 97):
            clarity_well = (
                'ABCDEFGH'[(i - 1) % 8] + ':' + '%01d' % ((i - 1) // 8 + 1,))
            with_zero = (
                'ABCDEFGH'[(i - 1) % 8] + ':' + '%02d' % ((i - 1) // 8 + 1,))
            without_colon = (
                'ABCDEFGH'[(i - 1) % 8] + '%01d' % ((i - 1) // 8 + 1,))
            without_colon_with_zero = (
                'ABCDEFGH'[(i - 1) % 8] + '%02d' % ((i - 1) // 8 + 1,))
            result = (
                clarity_well
                == extract_custom_forms._translate_to_well(with_zero)
                == extract_custom_forms._translate_to_well(without_colon)
                == extract_custom_forms._translate_to_well(
                    without_colon_with_zero))
            assert result

    @raises(TypeError)
    def test_translate_to_well_bad_input_number(self):
        extract_custom_forms._translate_to_well("4")

    @raises(TypeError)
    def test_translate_to_well_bad_input_empty_string(self):
        extract_custom_forms._translate_to_well("")
