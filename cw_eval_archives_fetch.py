import os
import csv
import sys
import getpass
import requests
from lxml import etree
import pdfkit

# This is SO LAZY it is sad. Time restrictions.
# Demographic information.
XPATH_TO_COURSE = "//table/tbody/tr[1]/td/table/tbody/tr[2]/td[2]/b"
XPATH_TO_FACULTY = "//table/tbody/tr[1]/td/table/tbody/tr[3]/td[2]/b"
XPATH_TO_DATA_SAMPLE_SIZE = "//table/tbody/tr[1]/td/table/tbody/tr[6]/td[2]"
XPATH_TO_DATA_POPULATION_SIZE = "//table/tbody/tr[1]/td/table/tbody/tr[7]/td[2]"
XPATH_TO_RESPONSE_RATE = "//table/tbody/tr[1]/td/table/tbody/tr[8]/td[2]/b"

# Questions and response data
XPATH_TO_QUESTIONS = "//table/tbody/tr[2]/td/table"
XPATH_TO_QUESTION_TREE = ''.join([XPATH_TO_QUESTIONS, "/tbody/tr/td/*"])  # The whole tree.

# These are unused, but left if I revist this code
XPATH_TO_QUESTION_TEXT = ''.join([XPATH_TO_QUESTIONS, "/tbody/tr/td/b/text()"])  # The question's text or group
XPATH_TO_QUESTION_BASE = ''.join([XPATH_TO_QUESTIONS, "/tbody/tr/td/table/tbody/tr/td"])
XPATH_TO_QUESTION_PACKAGE = ''.join(
    [XPATH_TO_QUESTION_BASE, '[contains(@width,"25%")]/text() | ', XPATH_TO_QUESTION_BASE,
     '[contains(@width,"75%")]/text()'])

PATHS_TO_DEMOGRAPHICS = [XPATH_TO_COURSE, XPATH_TO_FACULTY, XPATH_TO_DATA_SAMPLE_SIZE, XPATH_TO_DATA_POPULATION_SIZE,
                         XPATH_TO_RESPONSE_RATE]


def get_job():
    # Create a CSV file, open a writer.

    # user = input("Enter your UNI (you must be an admin): ")
    user = 'xxxxxxx'
    # password = getpass.getpass(prompt='Password: ', stream=None)
    password = 'xxxxxxxx'
    # instructor_uni = input("Instructor UNI: ")
    # get year
    # get term
    # get type
    # NOPE!

    get_evaluation(user, password, 'REPORTS')
    # pass: csv_writer.


def get_evaluation(login_uni, password, instructors_uni):
    payload = {
        '_username': login_uni,
        '_password': password
    }
    # Configure our session
    webworker = requests.session()
    # Login to CourseWorks.
    webworker.post('https://courseworks.columbia.edu/direct/session.json?', data=payload)
    # Get our SESSION info.
    response = webworker.get('https://courseworks.columbia.edu/direct/session.json')
    if response.status_code != 200:
        print('Error: Received a non-200 response during login.')
        sys.exit(1)

    # Set reply to JSON and parse.
    reply_json = response.json()
    user_eid = reply_json['session_collection'][0]['userEid']
    if user_eid != login_uni:
        print('Error: Could not login as user ' + login_uni)
        sys.exit(1)

    print('Logged in as: ' + user_eid)

    url = 'https://courseworks.columbia.edu/portal/tool/3b923cb5-ed21-4340-9273-67f4569a3c2d/report_search_archive?mergeReports=false&startSearch=&canSelectGroups=true&instructor=&external=false&settingsByEvaluation=true&courseId=FYSBX&schoolCode=&type=g&showSettingsDetail=false&assistant=&returnTo=0&term=&directView=false'

    results = webworker.get(url)

    evaluations_xml = etree.HTML(results.text)

    # Get our evaluation xpaths - we need to know the data about the row and the URL to fetch the evaluation.
    evaluation_xpaths = evaluations_xml.xpath('//tr[contains(@class,"search-result-table-row")]/td//text() | '
                                              '//tr[contains(@class,"search-result-table-row")]/td//a/@href')
    if evaluation_xpaths == '':
        print('Error: NO REPORTS FOUND')
        sys.exit(1)

    # Now we need to parse our the unnecessary line return and tab characters.
    # and build a composite list that has each evaluation in its own list, within our master list.
    junk_values = '\n\t\t\t\t\t\t'
    filtered_list = [cell for cell in evaluation_xpaths if cell not in junk_values]
    master_eval_list = [filtered_list[x:x + 7] for x in range(0, len(filtered_list), 7)]
    
    # Make a directory to throw up in.
    try:
        os.stat(instructors_uni)
    except:
        os.mkdir(instructors_uni)
    print('Created a directory for these reports named: ' + instructors_uni)

    # We purposefully left some unnecessary characters in our master list which will help us set the course title
    # of courses with multiple evaluations. We need this so we know how to name the file!
    last_title = ''

    for evaluation_row in master_eval_list:
        if evaluation_row[0] != '\n\t\t\t\t\t\t\n\t\t\t\t\t':
            last_title = evaluation_row[0]
        else:
            evaluation_row[0] = last_title

        # Finally we kick our row to the fetcher and saver function for -this- evaluation row.
        if "type=CO" in evaluation_row[5]:
            fetch_and_save_evaluations(evaluation_row, webworker)

    print('All reports have been saved.')


def parse_report(data, csv_writer):
    evaluations_xml = etree.HTML(data)

    demographic_data = []
    for path in PATHS_TO_DEMOGRAPHICS:
        demographics = evaluations_xml.xpath(path)
        demographic_data += [demographics[0].text]

    evaluation_xpaths = evaluations_xml.xpath(XPATH_TO_QUESTION_TREE, encoding='unicode')

    question_parsed = []
    for line in evaluation_xpaths:
        if line.tag == 'b':
            question_detail = line.text
            if question_detail:
                question = [question_detail]
        elif line.tag == 'table':
            # Question Response Data Packet
            for child in line:
                for response_detail in child:
                    response_package = response_detail.getchildren()
                    if response_package:
                        choice = response_package[0].text
                        frequency = re.search('\((\d+)\)',
                                              str.strip(response_package[1].xpath('.//text()')[1])).group(1)

                        question += ["choice::" + choice, frequency if frequency else '0']
                    question_parsed += demographic_data + question if question else ""
            # csv_writer.writerow(demographic_data + question)
        else:
            continue
    print(question_parsed)


def fetch_and_save_evaluations(evaluation_row, webworker):
    fetch_url = evaluation_row[5]
    evaluation = webworker.get(fetch_url)
    parse_report(evaluation.content, '')

    # print('Getting evaluation: ' + filename)
    # evaluation = webworker.get(fetch_url)
    # if evaluation.status_code != 200:
    #     print('Error: Failed to fetch: ' + filename)
    #     return


if __name__ == "__main__":
    get_job()
else:
    print('Cannot be run non-interactively (yet)')
    sys.exit(1)
