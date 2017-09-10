"""
Tests of the web browser interface (smtweb) using Selenium


"""

from __future__ import print_function
from __future__ import unicode_literals
import os
from time import sleep
from builtins import input
from unittest import SkipTest
try:
    from selenium import webdriver
    have_selenium = True
except ImportError:
    have_selenium = False

from subprocess import PIPE
import sarge

from nose.tools import assert_equal, assert_dict_contains_subset, assert_in

import utils
from utils import (setup as default_setup, teardown as default_teardown,
                   run, run_test, build_command, assert_file_exists, assert_in_output,
                   assert_config, assert_label_equal, assert_records, assert_return_code,
                   edit_parameters, expected_short_list, substitute_labels)


repository = "https://bitbucket.org/apdavison/ircr2013"
#repository = "/Users/andrew/dev/ircr2013"


def modify_script(filename):
    def wrapped():
        with open(os.path.join(utils.working_dir, filename), 'r') as fp:
            script = fp.readlines()
        with open(os.path.join(utils.working_dir, filename), 'w') as fp:
            for line in script:
                if "print(mean_bubble_size, median_bubble_size)" in line:
                    fp.write('print("Mean:", mean_bubble_size)\n')
                    fp.write('print("Median:", median_bubble_size)\n')
                else:
                    fp.write(line)
    return wrapped


setup_steps = [
    ("Get the example code",
     "hg clone %s ." % repository,
     assert_in_output, "updating to branch default"),
    ("Set up a Sumatra project",
     "smt init -d Data -i . -e python -m glass_sem_analysis.py --on-changed=store-diff ProjectGlass",
     assert_in_output, "Sumatra project successfully set up"),
    ("Run the ``glass_sem_analysis.py`` script with Sumatra",
     "smt run -r 'initial run' default_parameters MV_HFV_012.jpg",
     assert_in_output, ("2416.86315789 60.0", "histogram.png")),
    ("Comment on the outcome",
     "smt comment 'works fine'"),
    edit_parameters("default_parameters", "no_filter", "filter_size", 1),
    ("Run with changed parameters and user-defined label",
     "smt run -l example_label -r 'No filtering' no_filter MV_HFV_012.jpg",
     assert_in_output, "phases.png",
     assert_label_equal, "example_label"),
    ("Change parameters from the command line",
     "smt run -r 'Trying a different colourmap' default_parameters MV_HFV_012.jpg phases_colourmap=hot"),
    ("Add another comment",
     "smt comment 'The default colourmap is nicer'"),  # TODO  add a comment to an older record (e.g. this colourmap is nicer than 'hot')")
    ("Add tags on the command line",
     build_command("smt tag mytag {0} {1}", "labels")),
    modify_script("glass_sem_analysis.py"),
    ("Run the modified code",
     "smt run -r 'Added labels to output' default_parameters MV_HFV_012.jpg"),
]


def setup():
    global server, driver
    if not have_selenium:
        raise SkipTest("Tests require Selenium")
    default_setup()
    for step in setup_steps:
        if callable(step):
            step()
        else:
            print(step[0])  # description
            run_test(*step[1:])

    server = sarge.Command("smtweb -p 8765 --no-browser", cwd=utils.working_dir,
                           stdout=sarge.Capture(), stderr=sarge.Capture())
    server.run(async=True)
    driver = webdriver.Firefox()


def teardown():
    driver.close()
    server.terminate()
    default_teardown()


def test_start_page():
    driver.get("http://127.0.0.1:8765")
    # on homepage
    assert_equal(driver.title, "List of projects")
    # assert there is one project, named "ProjectGlass"
    projects = driver.find_elements_by_tag_name("h3")
    assert_equal(len(projects), 1)
    assert_equal(projects[0].text, "ProjectGlass")
    # click on ProjectGlass --> record list
    projects[0].click()
    assert_equal(driver.title, "ProjectGlass: List of records")
    assert_equal(driver.current_url, "http://127.0.0.1:8765/ProjectGlass/")


def test_record_list():
    driver.get("http://127.0.0.1:8765/ProjectGlass/")
    # assert there are four records
    rows = driver.find_elements_by_tag_name('tr')
    assert_equal(len(rows), 4 + 1)  # first row is the header
    column_headers = [elem.text for elem in rows[0].find_elements_by_tag_name('th')]
    # assert the labels are correct and that the reason and outcome fields are correct
    expected_content = substitute_labels([
         {'label': 0, 'outcome': 'works fine', 'reason': 'initial run',
          'version': '6038f9c...', 'main': 'glass_sem_analysis.py'},
         {'label': 1, 'outcome': '', 'reason': 'No filtering'},
         {'label': 2, 'outcome': 'The default colourmap is nicer', 'reason': 'Trying a different colourmap'},
         {'label': 3, 'outcome': '', 'reason': 'Added labels to output', 'version': '6038f9c...*'}])(utils.env)
    for row, expected in zip(rows[1:], reversed(expected_content)):
        cells = row.find_elements_by_tag_name('td')
        label = cells[0].text
        assert_equal(row.get_attribute('id'), label)
        actual = dict((key.lower(), cell.text) for key, cell in zip(column_headers, cells))
        assert_dict_contains_subset(expected, actual)


def test_column_settings_dialog():
    driver.get("http://127.0.0.1:8765/ProjectGlass/")
    # test the column settings dialog
    row0 = driver.find_element_by_tag_name('tr')
    column_headers = [elem.text for elem in row0.find_elements_by_tag_name('th')]
    cog = driver.find_element_by_class_name("glyphicon-cog")
    cog.click()
    sleep(0.5)
    options = driver.find_elements_by_class_name("checkbox")
    displayed_columns = [option.text for option in options if option.find_element_by_tag_name("input").is_selected()]
    assert_equal(displayed_columns, column_headers[1:])  # can't turn off "Label" column
    # turn on all columns
    for option in options:
        checkbox = option.find_element_by_tag_name("input")
        if not checkbox.is_selected():
            checkbox.click()
    apply_button, = [elem for elem in driver.find_elements_by_tag_name("button") if elem.text == "Apply"]
    apply_button.click()
    sleep(0.5)
    column_headers = [elem.text for elem in row0.find_elements_by_tag_name('th')]
    assert_equal(column_headers,
                 ["Label", "Date/Time", "Reason", "Outcome", "Input data", "Output data",
                  "Duration", "Processes", "Executable", "Main", "Version", "Arguments", "Tags"])


def test_comparison_view():
    driver.get("http://127.0.0.1:8765/ProjectGlass/")
    # test that "Compare selected" gives an error message with no records selected
    alert = driver.find_element_by_id("alert")
    assert not alert.is_displayed()
    compare_button, = [elem for elem in driver.find_elements_by_tag_name("button") if "Compare" in elem.text]
    compare_button.click()
    sleep(0.5)
    assert alert.is_displayed()
    assert "Need at least two records to compare" in alert.text
    alert.click()
    sleep(0.5)
    assert not alert.is_displayed()

    # select two records and click on compare selected
    rows = driver.find_elements_by_tag_name('tr')
    target_records = utils.env["labels"][::2]
    for row in rows[1:]:
        if row.get_attribute("id") in target_records:
            row.click()

    # scroll back to the top of the screen
    driver.execute_script("window.scrollTo(0, 0)")
    compare_button.click()
    # assert go to comparison page
    assert_in("compare", driver.current_url)


def test_data_detail_view():
    driver.get("http://127.0.0.1:8765/ProjectGlass/")
    rows = driver.find_elements_by_tag_name('tr')
    rows[1].find_element_by_tag_name('td').find_element_by_tag_name('a').click()
    assert_equal(driver.current_url, "http://127.0.0.1:8765/ProjectGlass/{}/".format(utils.env["labels"][-1]))

    dl = driver.find_element_by_tag_name('dl')
    general_attributes = dict(zip((item.text for item in dl.find_elements_by_tag_name("dt")),
                                  (item.text for item in dl.find_elements_by_tag_name("dd"))))
    assert_equal(general_attributes["Code version:"], '6038f9c500d1* (diff)')
    assert_in("Added labels to output", general_attributes["Reason:"])


if __name__ == '__main__':
    # Run the tests without using Nose.
    setup()
    try:
        test_start_page()
        test_record_list()
        test_column_settings_dialog()
        test_comparison_view()
        test_data_detail_view()
        # test filter by tags
        # test editing reason
        # test "Add outcome" button
        # test deleting records
    except Exception as err:
        print(err)
    response = input("Do you want to delete the temporary directory (default: yes)? ")
    if response not in ["n", "N", "no", "No"]:
        teardown()
    else:
        print("Temporary directory %s not removed" % utils.temporary_dir)