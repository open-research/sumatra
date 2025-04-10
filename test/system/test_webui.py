"""
Tests of the web browser interface (smtweb) using Selenium

"""

import os
import shutil
import tempfile
from time import sleep
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    have_selenium = True
except ImportError:
    have_selenium = False

import sarge

import pytest

from utils import (run_test, build_command, assert_in_output, assert_label_equal,
                   edit_parameters, substitute_labels)


pytest.mark.skipif(not have_selenium, reason="Tests require Selenium")

#repository = "https://github.com/apdavison/ircr2013"
repository = "/Users/adavison/projects/projectglass-git"



def modify_script(filename, working_dir):
    def wrapped():
        with open(os.path.join(working_dir, filename), 'r') as fp:
            script = fp.readlines()
        with open(os.path.join(working_dir, filename), 'w') as fp:
            for line in script:
                if "print(mean_bubble_size, median_bubble_size)" in line:
                    fp.write('print("Mean:", mean_bubble_size)\n')
                    fp.write('print("Median:", median_bubble_size)\n')
                else:
                    fp.write(line)
    return wrapped


@pytest.fixture(scope="module")
def env():
    return {"labels": []}


@pytest.fixture(scope="module")
def server(env):
    temporary_dir = os.path.realpath(tempfile.mkdtemp())
    working_dir = os.path.join(temporary_dir, "sumatra_exercise")
    os.mkdir(working_dir)
    env["working_dir"] = working_dir

    setup_steps = [
        ("Get the example code",
        "git clone %s ." % repository,
        assert_in_output, "done."),
        ("Set up a Sumatra project",
        "smt init -d Data -i . -e python -m glass_sem_analysis.py --on-changed=store-diff ProjectGlass",
        assert_in_output, "Sumatra project successfully set up"),
        ("Run the ``glass_sem_analysis.py`` script with Sumatra",
        "smt run -r 'initial run' default_parameters MV_HFV_012.jpg",
        assert_in_output, ("2416.86315789", "histogram.png")),
        ("Comment on the outcome",
        "smt comment 'works fine'"),
        edit_parameters("default_parameters", "no_filter", "filter_size", 1, working_dir),
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
        modify_script("glass_sem_analysis.py", working_dir),
        ("Run the modified code",
        "smt run -r 'Added labels to output' default_parameters MV_HFV_012.jpg"),
    ]

    for step in setup_steps:
        if callable(step):
            step()
        else:
            print(step[0])  # description
            run_test(*step[1:], env=env)

    print(f"Running smtweb in {working_dir}")
    server = sarge.Command("smtweb -p 8765 --no-browser", cwd=working_dir,
                           stdout=sarge.Capture(), stderr=sarge.Capture())
    server.run(async_=True)
    yield server
    server.terminate()
    shutil.rmtree(temporary_dir)


@pytest.fixture(scope="module")
def driver(server):
    # note that for now we have to use Chrome, as `test_comparison_view` gives
    # a scrolling error with Firefox
    # These bug reports seem to be relevant:
    #   - https://github.com/mozilla/geckodriver/issues/776#issuecomment-355086173
    #   - https://github.com/robotframework/SeleniumLibrary/issues/1780
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.close()


def test_start_page(driver, server, env):
    driver.get("http://127.0.0.1:8765")
    # on homepage
    assert driver.title == "List of projects"
    # assert there is one project, named "ProjectGlass"
    projects = driver.find_elements(By.TAG_NAME, "h3")
    assert len(projects) == 1
    assert projects[0].text == "ProjectGlass"
    # click on ProjectGlass --> record list
    projects[0].click()
    assert driver.title == "ProjectGlass: List of records"
    assert driver.current_url == "http://127.0.0.1:8765/ProjectGlass/"


def test_record_list(driver, env):
    driver.get("http://127.0.0.1:8765/ProjectGlass/")
    # assert there are four records
    rows = driver.find_elements(By.TAG_NAME, 'tr')
    assert len(rows) == 4 + 1  # first row is the header
    column_headers = [elem.text for elem in rows[0].find_elements(By.TAG_NAME, 'th')]
    # assert the labels are correct and that the reason and outcome fields are correct
    expected_content = substitute_labels([
         {'label': 0, 'outcome': 'works fine', 'reason': 'initial run',
          'version': 'e74b39374…', 'main': 'glass_sem_analysis.py'},
         {'label': 1, 'outcome': '', 'reason': 'No filtering'},
         {'label': 2, 'outcome': 'The default colourmap is nicer', 'reason': 'Trying a different colourmap'},
         {'label': 3, 'outcome': '', 'reason': 'Added labels to output', 'version': 'e74b39374…*'}])(env)
    for row, expected in zip(rows[1:], reversed(expected_content)):
        cells = row.find_elements(By.TAG_NAME, 'td')
        label = cells[0].text
        assert row.get_attribute('id') == label
        actual = dict((key.lower(), cell.text) for key, cell in zip(column_headers, cells))
        assert actual == actual | expected   # this uses the dictionary unary operator


def test_column_settings_dialog(driver):
    driver.get("http://127.0.0.1:8765/ProjectGlass/")
    # test the column settings dialog
    row0 = driver.find_element(By.TAG_NAME, 'tr')
    column_headers = [elem.text for elem in row0.find_elements(By.TAG_NAME, 'th')]
    cog = driver.find_element(By.CLASS_NAME, "glyphicon-cog")
    cog.click()
    sleep(0.5)
    options = driver.find_elements(By.CLASS_NAME, "checkbox")
    displayed_columns = [option.text for option in options if option.find_element(By.TAG_NAME, "input").is_selected()]
    assert displayed_columns == column_headers[1:]  # can't turn off "Label" column
    # turn on all columns
    for option in options:
        checkbox = option.find_element(By.TAG_NAME, "input")
        if not checkbox.is_selected():
            checkbox.click()
    apply_button, = [elem for elem in driver.find_elements(By.TAG_NAME, "button") if elem.text == "Apply"]
    apply_button.click()
    sleep(0.5)
    column_headers = [elem.text for elem in row0.find_elements(By.TAG_NAME, 'th')]
    assert column_headers == [
        "Label", "Date/Time", "Reason", "Outcome", "Input data", "Output data",
        "Duration", "Processes", "Executable", "Main", "Version", "Arguments", "Tags"]


def test_comparison_view(driver, env):
    driver.get("http://127.0.0.1:8765/ProjectGlass/")
    # test that "Compare selected" gives an error message with no records selected
    alert = driver.find_element(By.ID, "alert")
    assert not alert.is_displayed()
    compare_button, = [elem for elem in driver.find_elements(By.TAG_NAME, "button") if "Compare" in elem.text]
    compare_button.click()
    sleep(0.5)
    assert alert.is_displayed()
    assert "Need at least two records to compare" in alert.text
    alert.click()
    sleep(0.5)
    assert not alert.is_displayed()

    # select two records and click on compare selected
    rows = driver.find_elements(By.TAG_NAME, 'tr')
    target_records = env["labels"][::2]
    for row in rows[1:]:
        if row.get_attribute("id") in target_records:
            #row.location_once_scrolled_into_view
            #driver.execute_script("arguments[0].scrollIntoView();", row)
            row.click()

    # scroll back to the top of the screen
    driver.execute_script("window.scrollTo(0, 0)")
    compare_button.click()
    # assert go to comparison page
    assert "compare" in driver.current_url


def test_data_detail_view(driver, env):
    driver.get("http://127.0.0.1:8765/ProjectGlass/")
    rows = driver.find_elements(By.TAG_NAME, 'tr')
    rows[1].find_element(By.TAG_NAME, 'td').find_element(By.TAG_NAME, 'a').click()
    assert driver.current_url == "http://127.0.0.1:8765/ProjectGlass/{}/".format(env["labels"][-1])

    dl = driver.find_element(By.TAG_NAME, 'dl')
    general_attributes = dict(zip((item.text for item in dl.find_elements(By.TAG_NAME, "dt")),
                                  (item.text for item in dl.find_elements(By.TAG_NAME, "dd"))))
    assert general_attributes["Code version:"] == 'e74b39374b0a1a401848b05ba9c86042aac4d8e4* (diff)'
    assert "Added labels to output" in general_attributes["Reason:"]
