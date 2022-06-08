# Documentation-Automation

This repository will store tools created for documentation automation. The first project being worked on is automation
for the Code Review Report word document.

# Setup Instructions (WIP)

Please update the instructions if there are missing steps and/or you run into problems when setting up your environment.
Or if you think something could be helpful for the next person!

1. Install `pip` if you don't have it installed already
2. Install pipenv
   * `pip install pipenv`
3. `pipenv install` (this should install all packages in the Pipfile)
4. To run this you'll need to update some things in `doc_report_generator.py`:
   * Update `INPUT_DOCUMENT_NAME` - You will need to update it with a template version of the word document (or if you
     already have an example of the word document, just remove all the rows in the table
     under `5.6	Anomaly Review and Change Review (Incremental Review only)`)
   * Update the `user` variable - You will need to update it with your Github username
   * Update the `token` variable - You will need to generate a PAT token with at least read permissions
