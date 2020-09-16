"""Methods to harvest data from iLab custom forms."""
import re
import math
import unicodedata
import ast
from ua_ilab_tools import api_types


# NOTE: Change these globals to match names of these types of fields in your
# Clarity instance.


DISALLOWED_CHARS = r""
REPLACE_CHARS = r""


ONLY_INT_FIELDS = [
    "Concentration_each_sample", "Concentration", "Volume (uL)",
    "Initial_Number_Slides_or_Punches_each_sample", "Template Length",
    "Template_Length_each_sample"]


BOOL_FIELDS = [
    "H&E Slide Submitted?"]


def update_globals(disallowed_chars, replace_chars):
    global DISALLOWED_CHARS
    DISALLOWED_CHARS = disallowed_chars
    global REPLACE_CHARS
    REPLACE_CHARS = replace_chars


def grid_type(field_soup, form_info):
    """Harvest all of the sample info and add it to the CustomForm.

    Arguments:
        field_soup (BeautifulSoup object): The soup containing the
            field information.
        form_info (api_types.CustomForm): the dataclass holding info on the
            form.
    """
    if field_soup.find("value") is None:
        return
    elif field_soup.find("value").string == "[]":
        # The list is empty, do nothing.
        return

    if form_info.samples:
        # Sample data are in 2 or more grids.
        raise TypeError(
            f"There are 2 or more grids with sample data in the"
            f" {form_info.name} Custom Form for Request:"
            f" {form_info.req_id} . Please delete the data from the grid"
            f" that you don't want to use and try again.")
    form_info.samples.extend(extract_from_grid(field_soup, form_info))


def checkbox_type(field_soup, form_info):
    """Gather info from the ilab_form checkbox type.

    Arguments:
        field_soup (BeautifulSoup object): The soup containing the
            field information.
        form_info (api_types.CustomForm): the dataclass holding info on the
            form.
    """
    field_name = field_soup.find("identifier").string
    if field_soup.find("value"):
        form_info.field_to_values[field_name] = True
    else:
        form_info.field_to_values[field_name] = False


def all_other_types(field_soup, form_info):
    """All other types of field where data is saved as a form field.

    These types include: small (string), medium (text_medium),
        large (text) text box, date, select (pull down menu), radio,
        and text_section fields.

    Arguments:
        field_soup (BeautifulSoup object): The soup containing the
            field information.
    """
    value = field_soup.find("value")
    if value and value.string:
        form_info.field_to_values[field_soup.find(
            "identifier").string] = field_soup.find("value").string

    if value == "container_name":
        form_info.con_type = "96 well plate"


def bind_container_info(form_info):
    """Associate the container info to the form samples.

    Arguments:
        form_info: The form that holds the samples that are being bound.

    Restrictions:
        One container type per samples list.
    """
    con_strategy = {
        "Tube": tube_bind,
        "8-well strip": eight_well_strip_bind,
        "96 well plate": plate_96_bind}

    # Every sample assuredly has the same con_type.
    con_strategy[form_info.con_type](form_info)


def tube_bind(form_info):
    """Add the tube container info to the samples in the form.

    Arguments:
        form_info (api_types.CustomForm): the dataclass holding info on the
            form.
    """
    sample_names = []
    for sample in form_info.samples:
        sample.con = api_types.Container(sample.name, "Tube")
        sample.con.name = sample.name
        sample_names.append(sample.name)


def plate_96_bind(form_info):
    """Add the plate container info to the samples in the form.

    Arguments:
        form_info (api_types.CustomForm): the dataclass holding info on the
            form.
    """

    smp_locations = {}
    for sample in form_info.samples:
        sample.con = api_types.Container()
        # If 'Container Name' in grid.
        if sample.udf_to_value.get("Container Name"):
            con_name = sample.udf_to_value["Container Name"]
        # If 'container_name' in form.
        elif form_info.field_to_values.get("container_name"):
            con_name = form_info.field_to_values["container_name"]
        else:
            raise TypeError(
                f"The sample {sample.name} in request {form_info.req_id} on"
                f" form {form_info.name} was not given a container name.")

        # Replace all not ascii chars with ascii ones.
        con_name = _sanitize_text(con_name)
        con_name = re.sub(r"[^a-zA-Z0-9\-]", "-", con_name)
        sample.con.name = con_name
        sample.con.con_type = "96 well plate"

        # Make a dictionary of con_name: well, to make sure that there are no
        # two samples in the same well.
        smp_locations.setdefault(
            sample.con.name, []).append(sample.location)
    for locs in smp_locations.values():
        if len(set(locs)) != len(locs):
            raise TypeError(
                f"There are two or more samples with the same well"
                f" location in request {form_info.req_id}. Please review and"
                f" edit your well locations.")


def eight_well_strip_bind(form_info):
    """Add the eight-well-strip container info to the samples in the form.

    Arguments:
        form_info (api_types.CustomForm): the dataclass holding info on the
            form.
    """
    container_names = []
    tube_numbers = [sample.location for sample in form_info.samples]
    con_num = math.ceil(len(form_info.samples) / 8)

    if len(set(tube_numbers)) != len(tube_numbers):
        raise TypeError(
            f"There are two or more samples with the same tube number in"
            f" request {form_info.req_id}. Please review and edit your"
            f" tube numbers.")

    # Create the list of names for each strip submitted.
    for num in range(con_num):
        container_names.append(f"{form_info.req_id}-{num + 1}")
    for num, sample in enumerate(form_info.samples):
        sample.con = api_types.Container()
        sample.con.name = container_names[num // 8]
        sample.con.con_type = "8-well strip"


def extract_from_grid(field_soup, form_info):
    """Return list of Samples, extracted from grid portion of form xml.

    Arguments:
        field_soup (BeautifulSoup object): The soup of the grid field.
        form_info (api_types.CustomForm): dataclass holding information for the
            form.

    Returns:
        samples (list of Samples): The samples extracted from the grid with as
            much information that the grid provided.

    Restrictions:
        Every grid must start with the sample name (though the header
            doesn't matter).
        The Well Location or Tube Number cannot be empty if the column is
            in the grid or an error will be thrown.
        To allow a submission to have more than one plate on it, place the
            column name "Container Name" in the grid.
        To throw no errors, the columns that hold information for these
            data must be named:
                well location info = "Well Location".
                tube number for 8-strip tubes = "Tube Number".
                container name if the grid holds info for > 1
                    container = "Container Name".
                concentration info = "Concentration (ng/uL)" or
                    "Average Template Concentration (ng/uL)".
                TGM assay names = "TGM Assay".
                Sanger primers = "LVS Primer" or "HVS Primer".
    """

    samples = list()
    column_names = field_soup.find("default").string.split(',')
    sample_values = field_soup.find("value").string
    sample_values = sample_values.replace("null", "None")

    for value in ast.literal_eval(sample_values):
        # If there is not a real udf value, skip it.
        if value[0] in ["", None]:
            continue

        # remove whitespace.
        new_sample_name = value[0].strip()
        # Sanitize the name of the sample.
        new_sample_name = _sanitize_text(new_sample_name)
        # Remove '[:,]' from sample names and replace it with '-'.
        new_sample_name = re.sub(r"[:,.]", "-", new_sample_name)
        new_sample = api_types.Sample(new_sample_name)

        # skip "empty" sample names.
        if new_sample.name.upper().strip() == "EMPTY":
            continue

        # Skip the first column, as that must always be the sample name.
        for udf_name, udf_value in zip(column_names[1:], value[1:]):
            new_sample = udf_parser(
                form_info, new_sample, udf_name, udf_value)

        samples.append(new_sample)

    for sample in samples:
        if "TGM Assay List" in sample.udf_to_value.keys():
            sample.udf_to_value["TGM Assay List"] = sample.udf_to_value[
                "TGM Assay List"].strip(',')

        if "Primer" in sample.udf_to_value.keys():
            sample.udf_to_value["Primer"] = sample.udf_to_value[
                "Primer"].strip(',')

    return samples


def udf_parser(form, new_sample, udf_name, udf_value):
    """Parses udf data from form grid and returns the udf-updated sample.

    Arguments:
        form (api_types.CustomForm): dataclass holding information for the
            form.
        new_sample (api_types.Sample): a Sample dataclass to update with udf
            info.
        udf_name (string): the name of the udf we want to update new_sample
            with.
        udf_value (string): The value to add to new_sample.

    Returns:
        Updated new_sample.
    """
    # Check if there is a poorly inputted sample.
    udf_name = udf_name.strip()
    if udf_value in ["", None]:
        if udf_name in ["Well Location", "Tube Number"]:
            raise TypeError(
                f"The sample {new_sample.name} was given no well location.")
        # Don't add empty values as udf's, and return the sample and
        # con_type unchanged.
        return new_sample

    # Sanitize the udf_value.
    udf_value = _sanitize_text(udf_value)
    # Remove whitespace.
    udf_value = udf_value.strip()

    # Form specific handling.
    # Extract well info for a plate.
    if udf_name == "Well Location":
        new_sample.location = _translate_to_well(udf_value)
        form.con_type = "96 well plate"
        # Do not add Well Location as a udf, and return the modified sample.
        return new_sample

    elif udf_name == "Container Name":
        new_sample.udf_to_value["Container Name"] = re.sub(
            r"[:,.]", "-", udf_value)
        form.con_type = "96 well plate"
        return new_sample

    # Extract well info for strip tubes.
    elif udf_name in ["Tube Number", "Well Number (1-8)"]:
        udf_value = udf_value.upper()
        form.con_type = "8-well strip"
        new_sample.location = _translate_to_well(udf_value, plate=False)
        # Do not add Tube Number as a udf, and return the modified sample.
        return new_sample

    # Adds the adapter information to it's own field.
    elif "Adapter" in udf_name:
        new_sample.adapter = udf_value
        return new_sample

    elif udf_name == "Average Template Length":
        udf_name = "Template Length"

    elif (udf_name in [
            "Average Template Concentration (ng/uL)",
            "Concentration (ng/uL)"]):
        udf_name = "Concentration"

    elif "TGM Assay" in udf_name:
        udf_name = "TGM Assay List"
        new_sample.udf_to_value.setdefault(udf_name, "")
        udf_value = new_sample.udf_to_value[udf_name] + f"{udf_value},"

    elif "HVS Primer" in udf_name or "LVS Primer" in udf_name:
        udf_name = "Primer"
        new_sample.udf_to_value.setdefault("Primer", "")
        udf_value = new_sample.udf_to_value["Primer"] + f"{udf_value},"

    # Scrub client-inputted data that must be numbers AFTER correcting the
    # udf_names (e.g. if the form calls Concentration and Template Length
    # different things, the value still needs to be scrubbed).
    if udf_name in ONLY_INT_FIELDS:
        udf_value = re.sub(r"[^0-9.]", "", udf_value)

    if udf_name in BOOL_FIELDS:
        if udf_value.upper() in ["YES", "TRUE", "AFFIRMATIVE", "Y", "T"]:
            udf_value = "true"
        else:
            udf_value = "false"

    new_sample.udf_to_value[udf_name] = udf_value

    return new_sample


def _sanitize_text(text):
    """Convert text to ascii, replace chars [^a-zA-Z0-9:,.] with '-'."""
    # Replace all not ascii chars with ascii ones
    text = unicodedata.normalize("NFKD", text).encode(
        "ascii", "ignore").decode("ascii")
    # Convert anything that is not alphanumeric or a hyphen to a hyphen.
    text = re.sub(DISALLOWED_CHARS, REPLACE_CHARS, text)
    # Convert '+' to 'plus' to avoid the confusion of changing a '+' to
    # a '-'.
    text = re.sub(r"[+]", "plus", text)

    return text


def _translate_to_well(well, plate=True):
    """Translates any allowed string options A1, A01, 1, or A:01 to A:1."""
    well = well.upper().strip()
    # Do nothing if A:1 - H:12.
    if re.search(r"[A-H]:[1-9][0-3]{0,1}", well) is None:
        # A1-H12.
        if re.search(r"[A-H][1-9][0-3]{0,1}", well):
            well = well[0] + ':' + well[1:]
        # A01-H09 or A:01 - H:09.
        elif re.search(r"[A-H]:{0,1}0[1-9]", well):
            if ':' not in well:
                well = well.replace('0', ':')
            else:
                well = well.replace('0', '')
        # If the well is 1-8, treat as a strip tube.
        elif re.search(r"^[1-8]$", well):
            # If someone has inputted numbers instead of well locations
            #  for a plate format, raise an error.
            if plate:
                raise TypeError(
                    "We don't accept plate indexes of that type.")
            # Convert 1-8 into the strip tube format.
            well = f"A:{well}"
        # Anything else.
        else:
            raise TypeError("We don't accept indexes of that type.")

    return well
