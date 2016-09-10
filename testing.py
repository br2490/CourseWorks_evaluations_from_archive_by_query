import csv
import os
import re
import sys
import getpass

import lxml
from lxml import etree

import requests

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


def parse_data(data):
    evaluations_xml = etree.HTML(data)

    with open('reportname.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile, delimiter=',',
                                quotechar='"')

        # Why is this in all caps? Don't yell.
        csv_writer.writerow(["COURSE", "INSTRUCTOR", "SAMPLE SIZE", "POPULATION SIZE", "R_RATE", "QUESTION_TEXT"])

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
                    # print("ROW--> " + str(question_detail))
                    # question_parsed += [question_detail]
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
                    question_parsed += demographic_data + question
                    csv_writer.writerow(demographic_data + question)
            else:
                continue
    print(question_parsed)


def parse_data_alt(data):
    evaluations_xml = etree.HTML(data)

    for path in PATHS_TO_DEMOGRAPHICS:
        demographics = evaluations_xml.xpath(path)
        print(demographics[0].text)

    evaluation_xpaths = evaluations_xml.xpath(XPATH_TO_QUESTION_TREE, encoding='unicode')
    print(len(evaluation_xpaths))

    for question_package in evaluation_xpaths:
        # This disgusts me. Honestly. Why am I making this such a process?
        if question_package.tag == 'b':
            question_text = question_package.text  # QUESTION DETAILS: TYPE, QUESTION TEXT, HELP TEXT
            print(question_text)
        for answer_data in question_package:
            for response_detail in answer_data:  # ROW
                response_package = response_detail.getchildren()

                if response_package:
                    option = response_package[0].text
                    rate = re.search('\((\d+)\)', str.strip(response_package[1].xpath('.//text()')[1])).group(1)


with open('D:\\GitHub\\CourseWorks_evaluations_from_archive_by_query\\test_data\\report_blank.html', 'r') as myfile:
    # Strip the extra bits.
    data = myfile.read().replace('\n', '').replace('\t', '')
    # Reduce all duplicate spaces; data cleaned.
    data = re.sub(' +', ' ', data)

    parse_data(data)
