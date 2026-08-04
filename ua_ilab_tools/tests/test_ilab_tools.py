import os
import re
import unittest
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock

from bs4 import BeautifulSoup

from ua_ilab_tools import extract_custom_forms, ua_ilab_tools


FIXTURE_DIR = Path(__file__).resolve().parent


@dataclass
class FakeResponse:
    text: str


def load_xml(filename):
    with open(FIXTURE_DIR / filename, "r") as file:
        return BeautifulSoup(file.read(), "xml")


class TestIlabToolsApiMethods(unittest.TestCase):
    def setUp(self):
        self.tools = ua_ilab_tools.IlabTools.__new__(ua_ilab_tools.IlabTools)
        self.tools.api = Mock()

    def test_get_service_requests_default_status(self):
        self.tools.api.get.return_value = [
            FakeResponse(
                """
                <ilab-response>
                    <service-requests>
                        <service-request>
                            <id>REQ1</id>
                            <state>processing</state>
                        </service-request>
                        <service-request>
                            <id>REQ2</id>
                            <state>processing</state>
                        </service-request>
                    </service-requests>
                </ilab-response>
                """
            )
        ]

        request_map = self.tools.get_service_requests()

        self.tools.api.get.assert_called_once_with(
            "service_requests.xml",
            parameters={"states": "processing", "from_date": "2015-01-01T12:00Z"},
            get_all=True,
        )
        self.assertEqual(set(request_map.keys()), {"REQ1", "REQ2"})
        for request_soup in request_map.values():
            self.assertEqual(request_soup.find("state").text, "processing")

    def test_get_service_requests_specific_status(self):
        self.tools.api.get.return_value = [
            FakeResponse(
                """
                <ilab-response>
                    <service-request>
                        <id>REQ3</id>
                        <state>completed</state>
                    </service-request>
                </ilab-response>
                """
            )
        ]

        request_map = self.tools.get_service_requests(status="completed")

        self.tools.api.get.assert_called_once_with(
            "service_requests.xml",
            parameters={"states": "completed", "from_date": "2015-01-01T12:00Z"},
            get_all=True,
        )
        self.assertEqual(list(request_map.keys()), ["REQ3"])
        self.assertEqual(request_map["REQ3"].find("state").text, "completed")

    def test_get_service_requests_specific_uri(self):
        self.tools.api.get.return_value = [
            FakeResponse(
                """
                <ilab-response>
                    <service-request>
                        <id>12345</id>
                        <state>processing</state>
                    </service-request>
                </ilab-response>
                """
            )
        ]

        request_map = self.tools.get_service_requests(specific_uri="12345")

        self.tools.api.get.assert_called_once_with(
            "service_requests/12345.xml",
            get_all=False,
        )
        self.assertEqual(request_map["12345"].find("id").text, "12345")

    def test_get_service_cost(self):
        self.tools.api.get.return_value = [
            FakeResponse(
                """
                <ilab-response>
                    <services>
                        <service>
                            <id>111</id>
                            <price>
                                <price>12.5</price>
                                <unit>
                                    <description>sample</description>
                                </unit>
                            </price>
                        </service>
                    </services>
                </ilab-response>
                """
            )
        ]

        result = self.tools.get_service_cost("111")

        self.tools.api.get.assert_called_once_with("services.xml")
        self.assertEqual(result.price, 12.5)
        self.assertEqual(result.samples_per_unit, "sample")

    def test_get_service_cost_returns_none_when_not_found(self):
        self.tools.api.get.return_value = [
            FakeResponse("<ilab-response><services></services></ilab-response>")
        ]

        result = self.tools.get_service_cost("missing")

        self.assertIsNone(result)

    def test_get_request_charges(self):
        self.tools.api.get.return_value = [
            FakeResponse(
                """
                <ilab-response>
                    <charges>
                        <charge><id>CHARGE1</id></charge>
                        <charge><id>CHARGE2</id></charge>
                    </charges>
                </ilab-response>
                """
            )
        ]

        charges = self.tools.get_request_charges("REQ1")

        self.tools.api.get.assert_called_once_with("service_requests/REQ1/charges.xml")
        self.assertEqual(set(charges.keys()), {"CHARGE1", "CHARGE2"})

    def test_get_milestones(self):
        self.tools.api.get.return_value = [
            FakeResponse(
                """
                <ilab-response>
                    <milestones>
                        <milestone><name>Received</name></milestone>
                        <milestone><name>Completed</name></milestone>
                        <milestone></milestone>
                    </milestones>
                </ilab-response>
                """
            )
        ]

        milestones = self.tools.get_milestones("REQ1")

        self.tools.api.get.assert_called_once_with("service_requests/REQ1/milestones.xml")
        self.assertEqual(set(milestones.keys()), {"Received", "Completed"})

    def test_get_custom_forms(self):
        self.tools.api.get.return_value = [
            FakeResponse(
                """
                <ilab-response>
                    <custom-forms>
                        <custom-form><id>FORM1</id></custom-form>
                        <custom-form><id>FORM2</id></custom-form>
                    </custom-forms>
                </ilab-response>
                """
            )
        ]

        forms = self.tools.get_custom_forms("REQ1")

        self.tools.api.get.assert_called_once_with("service_requests/REQ1/custom_forms.xml")
        self.assertEqual(set(forms.keys()), {"FORM1", "FORM2"})


class TestProjectExtraction(unittest.TestCase):
    def test_extract_project_info_with_and_without_full_name(self):
        req_soup = BeautifulSoup(
            """
            <service-request>
                <name>Core-Request-Test Project</name>
                <owner>
                    <name>Jane Doe</name>
                    <email>jane.doe@email.arizona.edu</email>
                </owner>
            </service-request>
            """,
            "xml",
        )

        full_project = ua_ilab_tools.extract_project_info(req_soup, full_name=True)
        short_project = ua_ilab_tools.extract_project_info(req_soup)

        self.assertEqual(full_project.name, "Core-Request-Test Project")
        self.assertEqual(short_project.name, "Test Project")
        self.assertEqual(full_project.res.first_name, "Jane")
        self.assertEqual(full_project.res.last_name, "Doe")
        self.assertEqual(full_project.res.lab_type, "internal")
        self.assertEqual(full_project.res.email, "jane.doe@email.arizona.edu")

    def test_extract_project_info_external_lab(self):
        req_soup = BeautifulSoup(
            """
            <service-request>
                <name>Core-Request-External Project</name>
                <owner>
                    <name>John Smith</name>
                    <email>john@example.com</email>
                </owner>
            </service-request>
            """,
            "xml",
        )

        project = ua_ilab_tools.extract_project_info(req_soup, full_name=True)

        self.assertEqual(project.res.lab_type, "external")


class TestCustomFormExtraction(unittest.TestCase):
    def test_extract_from_grid_container_name_in_form(self):
        form_soup = load_xml("extract_from_grid_container_name_in_form.xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3275577", form_soup)
        samples = form.samples
        sample_names = [sample.name for sample in samples]

        self.assertNotIn("Empty", sample_names)
        self.assertEqual(len(samples), 67)
        self.assertEqual(form.field_to_values["container_name"], "Test-Plate-Name")
        for sample in samples:
            self.assertIn("AF", sample.name)
            self.assertEqual(sample.con.name, "Test-Plate-Name")
            self.assertEqual(sample.con.con_type, "96 well plate")
            self.assertRegex(sample.location, r"[A-H]:[0-9]{1,2}")
            self.assertIn("Dilution", sample.udf_to_value)

    def test_extract_from_grid_container_name_in_grid(self):
        form_soup = load_xml("extract_from_grid_container_name_in_grid.xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3256202", form_soup)
        samples = form.samples
        sample_names = [sample.name for sample in samples]
        container_names = {
            "Plate-1",
            "Plate-2",
            "Plate-3",
            "Plate-4",
            "Plate-5",
            "Plate-6",
        }

        self.assertNotIn("Empty", sample_names)
        self.assertEqual(len(samples), 540)
        self.assertIn("Dilution_each_sample", form.field_to_values)
        for sample in samples:
            self.assertTrue(sample.name)
            self.assertIn(sample.con.name, container_names)
            self.assertEqual(sample.con.con_type, "96 well plate")
            self.assertRegex(sample.location, r"[A-H]:[0-9]{1,2}")
            self.assertIn("Dilution", sample.udf_to_value)

    def test_extract_from_grid_tgm_data(self):
        form_soup = load_xml("extract_from_grid_tgm_data.xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3904550", form_soup)
        samples = form.samples

        self.assertEqual(len(samples), 19)
        for sample in samples:
            self.assertIn("TGM Assay List", sample.udf_to_value)
            self.assertNotEqual(sample.udf_to_value["TGM Assay List"][-1], ",")

    def test_extract_from_grid_lvs_data(self):
        form_soup = load_xml("extract_from_grid_lvs_primers.xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3923775", form_soup)
        samples = form.samples

        self.assertEqual(len(samples), 7)
        for sample in samples:
            self.assertIn("Primer", sample.udf_to_value)
            self.assertEqual(len(sample.udf_to_value["Primer"].split(",")), 3)

    def test_extract_custom_form_info_samples_con_type_tube(self):
        form_soup = load_xml("extract_custom_form_info_samples_con_type_tube.xml")

        samples = ua_ilab_tools.extract_custom_form_info("0", "3271720", form_soup).samples
        sample_names = ["UA2001111", "UA2002222", "UA2003333", "UA2004444", "UA2005555"]

        self.assertEqual(len(samples), len(sample_names))
        for sample in samples:
            self.assertIn(sample.name, sample_names)
            self.assertIn(sample.con.name, sample_names)
            self.assertEqual(sample.con.con_type, "Tube")
            self.assertEqual(sample.location, "1:1")
            self.assertIn("TGM Assay List", sample.udf_to_value)

    def test_extract_from_grid_eight_strip(self):
        form_soup = load_xml("extract_from_grid_con_type_eight_strip.xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3220469", form_soup)
        samples = form.samples
        sample_names = ["A3", "B13", "H11", "F8", "G2", "C3", "C5", "E6"]

        for sample in samples:
            self.assertIn(sample.name, sample_names)
            self.assertRegex(sample.con.name, r"\d+-[1-8]")
            self.assertEqual(sample.con.con_type, "8-well strip")
            self.assertRegex(sample.location, r"A:[1-8]")
            self.assertIn("Volume (uL)", sample.udf_to_value)

    def test_extract_from_grid_eight_strip_duplicate_tube_number_raises(self):
        form_soup = load_xml("extract_from_grid_con_type_eight_strip_too_many_tubes.xml")

        with self.assertRaises(TypeError):
            ua_ilab_tools.extract_custom_form_info("0", "3220469", form_soup)

    def test_extract_custom_form_info_samples_not_ascii_characters(self):
        form_soup = load_xml("extract_custom_form_info_samples_not_ascii_characters.xml")

        form = ua_ilab_tools.extract_custom_form_info("0", "3209463", form_soup)
        samples = form.samples

        self.assertEqual(len(samples), 2)

        for sample in samples:
            # Ensure non-ASCII characters were removed.
            self.assertNotRegex(sample.name, r"[^\x00-\x7F]")

            # Tube containers should use the sample name.
            self.assertEqual(sample.con.name, sample.name)
            self.assertEqual(sample.con.con_type, "Tube")


class TestExtractCustomFormsInternals(unittest.TestCase):
    def test_translate_to_well(self):
        for i in range(1, 97):
            clarity_well = "ABCDEFGH"[(i - 1) % 8] + ":" + "%01d" % ((i - 1) // 8 + 1,)
            with_zero = "ABCDEFGH"[(i - 1) % 8] + ":" + "%02d" % ((i - 1) // 8 + 1,)
            without_colon = "ABCDEFGH"[(i - 1) % 8] + "%01d" % ((i - 1) // 8 + 1,)
            without_colon_with_zero = "ABCDEFGH"[(i - 1) % 8] + "%02d" % (
                (i - 1) // 8 + 1,
            )

            self.assertEqual(extract_custom_forms._translate_to_well(with_zero), clarity_well)
            self.assertEqual(extract_custom_forms._translate_to_well(without_colon), clarity_well)
            self.assertEqual(
                extract_custom_forms._translate_to_well(without_colon_with_zero),
                clarity_well,
            )

    def test_translate_to_well_bad_input_number_raises(self):
        with self.assertRaises(TypeError):
            extract_custom_forms._translate_to_well("4")

    def test_translate_to_well_bad_input_empty_string_raises(self):
        with self.assertRaises(TypeError):
            extract_custom_forms._translate_to_well("")

    def test_translate_to_well_allows_strip_tube_numbers_when_plate_false(self):
        self.assertEqual(extract_custom_forms._translate_to_well("4", plate=False), "A:4")

    def test_sanitize_text_converts_non_ascii(self):
        self.assertEqual(extract_custom_forms._sanitize_text("157ã"), "157a")

    def test_sanitize_text_replaces_plus_with_plus_word(self):
        self.assertEqual(extract_custom_forms._sanitize_text("A+B"), "AplusB")


if __name__ == "__main__":
    unittest.main()
