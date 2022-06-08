import re
import requests
import sys
import json

from typing import List
from docx import Document
from docx.table import Table


# TODO: Move this class to a separate file
class Change:
    def __init__(self, ticket_number: int, anomaly_change_id: str, description: str, source_modules_modified: str):
        self.ticket_number = ticket_number
        self.anomaly_change_id = anomaly_change_id
        self.description = description
        self.source_modules_modified = source_modules_modified


ANOMALY_REVIEW_AND_CHANGE_REVIEW_TABLE_COLUMN_NAMES = ['Anomaly/\nChange ID', 'Description', 'Source Modules Modified']
ANOMALY_REVIEW_AND_CHANGE_REVIEW_TABLE_NUM_OF_COLUMNS = len(ANOMALY_REVIEW_AND_CHANGE_REVIEW_TABLE_COLUMN_NAMES)
f = open('config.json')
data = json.load(f)
PR_TITLE_FIELD_NAME = data['PR_TITLE_FIELD_NAME']
INPUT_DOCUMENT_NAME = data['INPUT_DOCUMENT_NAME']
OUTPUT_DOCUMENT_NAME = data['OUTPUT_DOCUMENT_NAME']
f.close()


# PR_TITLE_FIELD_NAME = 'title'
# INPUT_DOCUMENT_NAME = 'CORPFT-000157 Code Review Report RPT Template.docx'
# OUTPUT_DOCUMENT_NAME = 'RPT-XXXXXX-name-goes-here.docx'


def main():
    document = Document(INPUT_DOCUMENT_NAME)
    anomaly_review_and_change_review_table = get_anomaly_review_and_change_review_table(document)

    pull_requests = get_pull_requests()
    ticket_numbers = []
    change_ids = []
    descriptions = []

    pull_requests = [pull_request for pull_request in pull_requests if (
            'NONFUNC' not in pull_request[PR_TITLE_FIELD_NAME].upper() and 'NON-FUNC' not in pull_request[
        PR_TITLE_FIELD_NAME].upper())]

    for pull_request in pull_requests:
        pull_request_title = pull_request[PR_TITLE_FIELD_NAME]

        # Regex search removes 'PLT- and '[PLT-' (we could also try splitting on spaces, may be a better idea)
        ticket_number = re.search('(?<=PLT-).{4}', pull_request_title, re.IGNORECASE).group()
        change_id = re.search(r'PLT-.{4}', pull_request_title,
                              re.IGNORECASE).group().upper()  # TODO: !! Handle 5 digit ticket id !!
        # Regex search removes 'PLT-####' and '[PLT-####]'
        description = \
            (re.findall('(?<=PLT-.{4} ).*$', pull_request_title, re.IGNORECASE) or \
             re.findall('(?<=\[PLT-.{4}\] ).*$', pull_request_title, re.IGNORECASE))

        if not ticket_number or not change_id or not description:
            sys.exit(1)

        ticket_numbers.append(int(ticket_number))
        change_ids.append(change_id)
        descriptions += description  # description is a list so use concatenation

    descriptions = [description.capitalize() for description in
                    descriptions]  # Start all descriptions with a capital letter
    change_list = [
        Change(
            ticket_numbers[idx],
            change_ids[idx],
            descriptions[idx],
            f"Please see: PR# {pull_request['number']}"
            # TODO: !!! Handle multiple PRs?? - make dictionary w/ key = Ticket Number or Anomaly/Change ID
        ) for idx, pull_request in enumerate(pull_requests)
    ]

    """ In order to do this we need to get the ticket description from Jira (export tickets from Jira?)
    change_list = {}
    for idx, pull_request in enumerate(pull_requests):
        ticket_number, change_id, description = ticket_numbers[idx], change_ids[idx], descriptions[idx]

        if change_id in change_list:
            change_list[change_id] += Change(
                ticket_number,
                change_id,
                description,
                f"" # TODO: We should not use this and instead have a .build() which will take all the Changes for a ticket and build the Source Modules Modified text
            )
        else:
            change_list[change_id] = [Change(
                ticket_number,
                change_id,
                description,
                f"Please see: PR# {pull_request['number']}"  # TODO: We should not use this and instead have a .build() which will take all the Changes for a ticket and build the Source Modules Modified text
            )]
    """

    change_list.sort(key=lambda change: change.ticket_number)  # Sort by ticket number?
    add_changes_to_word_document(anomaly_review_and_change_review_table, change_list)
    document.save(OUTPUT_DOCUMENT_NAME)


def get_pull_requests():
    ##### Configablerize Section #####
    f = open('config.json')
    data = json.load(f)

    user = data['user']
    token = data['token']
    auth = (user, token)
    organization = data['organization']
    repository = data['repository']
    labels = data['labels']
    date = None
    milestone = None

    f.close()

    """ user = 'shreyatendulkar02' #shreyatendulkar02  # asosa0506
    token = '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'  #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 # Should only need a PAT that has all read permissions #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     #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
    auth = (user, token)

    organization = 'sweetspot'
    repository = 'cams'
    labels = 'global-cams'  # This is the label used for the upcoming release
    date = None
    milestone = None
    ##### Configablerize Section #####
    """

    return get_pull_requests_by_query(auth, organization, repository, labels, date, milestone)


def add_changes_to_word_document(table: Table, change_list: List[Change]) -> None:
    for change in change_list:
        table.add_row()
        new_row = table.rows[-1]
        old_row = table.rows[-2]
        # print(change.ticket_number)

        new_row.cells[0].text = change.anomaly_change_id
        new_row.cells[1].text = change.description
        new_row.cells[2].text = change.source_modules_modified

        # print("new:",new_row.cells[0].text)
        # print("old:",old_row.cells[0].text)

        if new_row.cells[0].text == old_row.cells[0].text:
            old_row.cells[1].merge(new_row.cells[1])
            old_row.cells[2].merge(new_row.cells[2])
            old_row.cells[0].text = old_row.cells[0].text


def get_anomaly_review_and_change_review_table(document: Document) -> Table:
    for table in document.tables:
        found_table = True
        for cell in table._cells[:ANOMALY_REVIEW_AND_CHANGE_REVIEW_TABLE_NUM_OF_COLUMNS]:
            if cell.text not in ANOMALY_REVIEW_AND_CHANGE_REVIEW_TABLE_COLUMN_NAMES:
                found_table = False
                print(cell.text)
        if found_table:
            return table


# Belongs in separate file
# This code has been (for the most part) taken from Code Review Report Generator
# See 'get_pr_nums_by_query()'
def get_pull_requests_by_query(auth, organization, repository, labels, date, milestone):
    print('Enumerating PRs...')

    # Base url and parameters
    url = f'https://api.github.com/repos/{organization}/{repository}/issues'
    params = {'state': 'closed', 'per_page': '100'}
    if labels:
        params['labels'] = labels
    if date:
        params['since'] = date
    if milestone:
        params['milestone'] = milestone

    page = 1

    # Iterate through pages until empty response
    while True:

        # Set page count and increment
        params['page'] = str(page)
        page = page + 1

        response = requests.get(url, auth=auth, params=params)
        if response.status_code >= 300:
            print(f"HTTP Response Code ({response.status_code:d}):")
            print(response.text)
            sys.exit(0)
        response = json.loads(response.text)
        if len(response) < 100:
            break

    return response


if __name__ == '__main__':
    main()
