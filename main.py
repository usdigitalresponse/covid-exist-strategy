# Define source field names.
import functools
import os

import pandas as pd

from covid.constants import PATH_TO_SERVICE_ACCOUNT_KEY
from covid.extract import extract_cdc_ili_data
from covid.extract import extract_covidtracking_historical_data
from covid.load import get_sheets_client
from covid.load import post_dataframe_to_google_sheets
from covid.load_utils import sleep_and_log
from covid.transform import CRITERIA_1_SUMMARY_COLUMNS
from covid.transform import CRITERIA_2_SUMMARY_COLUMNS
from covid.transform import CRITERIA_5_SUMMARY_COLUMNS
from covid.transform import CRITERIA_6_SUMMARY_COLUMNS
from covid.transform import CRITERIA_COMBINED_SUMMARY_COLUMNS
from covid.transform import STATE_FIELD
from covid.transform import transform_cdc_ili_data
from covid.transform import transform_covidtracking_data
from covid.transform_utils import calculate_state_summary

# Define the names of the tabs to upload to.
FOR_WEBSITE_TAB_NAME = "For Website"
ALL_STATE_DATA_TAB_NAME = "All State Data"
WORK_IN_PROGRESS_NY_ONLY_TAB_NAME = f"{ALL_STATE_DATA_TAB_NAME} (NY Only)"
STATE_SUMMARY_TAB_NAME = "State Summary"

CDC_CRITERIA_1_GOOGLE_WORKBOOK_KEY = "17L2TUH03_43YDoqBoDq13HMZG1V92kw49ESIuQNTHbU"
CDC_CRITERIA_2_GOOGLE_WORKBOOK_KEY = "1OrpOScYpPchM2Ug9fXdQRIl2Rlc_HCQ2KEdJm2fgh_s"
CDC_CRITERIA_3_GOOGLE_WORKBOOK_KEY = "10mBKVrDVL63vcBORo3tMBTEnR9DNW7xQ0XpEO29yG20"
CDC_CRITERIA_5_GOOGLE_WORKBOOK_KEY = "1Jqf6JAm03iM_tSZx6z3gEWOC1l27lri_hZgsJOiQ5Bw"
CDC_CRITERIA_6_GOOGLE_WORKBOOK_KEY = "11NX0rXhwTRahIJASMGUCqnaVH_FUtlyQuWrzgWEf4zc"
CDC_CRITERIA_SUMMARY_GOOGLE_WORKBOOK_KEY = (
    "1Lprw-UYnr6DX0rgS1fh2-mxuZWFAXv_ezuDQ2L8sF60"
)

# Note: if you'd like to run the full pipeline, you'll need to generate a service account keyfile for an account
# that has been given write access to the Google Sheet.


def extract_transform_and_load_covid_data(post_to_google_sheets=True):
    """Runs the entire pipeline to produce data for Covid Exit Strategy data sources.

    Workbooks are found in: https://drive.google.com/drive/u/1/folders/15j1iyyJtJ8BmK3y-HO6cLp-7R7nAoSml.

    Args:
        post_to_google_sheets (bool): whether or not to attempt to post to google sheets; set to False for faster
            debugging of data processing

    """
    print("Starting to ETL...")

    client, credentials = get_sheets_client(
        credential_file_path=os.path.abspath(PATH_TO_SERVICE_ACCOUNT_KEY)
    )

    # TODO(lbrown): Un-comment these when we find a path forward for CDC bed data.
    # cdc_beds_current_df = extract_cdc_beds_current_data()
    # cdc_beds_historical_df = extract_cdc_beds_historical_data(credentials=credentials)

    # transformed_cdc_beds_df = transform_cdc_beds_data(
    #     cdc_beds_current_df=cdc_beds_current_df,
    #     cdc_beds_historical_df=cdc_beds_historical_df,
    # )

    # Upload category 3A data.
    # criteria_3_summary_df = calculate_state_summary(
    #     transformed_df=transformed_cdc_beds_df, columns=CRITERIA_3_SUMMARY_COLUMNS
    # )
    # post_dataframe_to_google_sheets(
    #     df=criteria_3_summary_df,
    #     workbook_key=CDC_CRITERIA_3_GOOGLE_WORKBOOK_KEY,
    #     tab_name=STATE_SUMMARY_TAB_NAME,
    #     credentials=credentials,
    # )
    #
    # sleep_and_log()
    #
    # post_dataframe_to_google_sheets(
    #     df=transformed_cdc_beds_df,
    #     workbook_key=CDC_CRITERIA_3_GOOGLE_WORKBOOK_KEY,
    #     tab_name="Historical Data",
    #     credentials=credentials,
    # )

    covidtracking_df = extract_covidtracking_historical_data()
    cdc_ili_df = extract_cdc_ili_data()

    transformed_cdc_ili_df = transform_cdc_ili_data(ili_df=cdc_ili_df)

    transformed_covidtracking_df = transform_covidtracking_data(
        covidtracking_df=covidtracking_df
    )

    # Upload Criteria 1 workbook for all states.
    criteria_1_summary_df = calculate_state_summary(
        transformed_df=transformed_covidtracking_df, columns=CRITERIA_1_SUMMARY_COLUMNS
    )

    if post_to_google_sheets:
        post_dataframe_to_google_sheets(
            df=criteria_1_summary_df,
            workbook_key=CDC_CRITERIA_1_GOOGLE_WORKBOOK_KEY,
            tab_name=STATE_SUMMARY_TAB_NAME,
            credentials=credentials,
        )

        sleep_and_log()

    # Upload Criteria 2 workbook for all states.
    criteria_2_summary_df = calculate_state_summary(
        transformed_df=transformed_covidtracking_df, columns=CRITERIA_2_SUMMARY_COLUMNS
    )
    if post_to_google_sheets:
        post_dataframe_to_google_sheets(
            df=criteria_2_summary_df,
            workbook_key=CDC_CRITERIA_2_GOOGLE_WORKBOOK_KEY,
            tab_name=STATE_SUMMARY_TAB_NAME,
            credentials=credentials,
        )

        sleep_and_log()

    # Upload Criteria 5 workbook
    # Upload all data tab for Criteria 5.
    if post_to_google_sheets:
        post_dataframe_to_google_sheets(
            df=transformed_cdc_ili_df,
            workbook_key=CDC_CRITERIA_5_GOOGLE_WORKBOOK_KEY,
            tab_name=ALL_STATE_DATA_TAB_NAME,
            credentials=credentials,
        )

        sleep_and_log()

    # Upload state summary tab for Criteria 5.
    criteria_5_summary_df = calculate_state_summary(
        transformed_df=transformed_cdc_ili_df, columns=CRITERIA_5_SUMMARY_COLUMNS
    )
    if post_to_google_sheets:
        post_dataframe_to_google_sheets(
            df=criteria_5_summary_df,
            workbook_key=CDC_CRITERIA_5_GOOGLE_WORKBOOK_KEY,
            tab_name=STATE_SUMMARY_TAB_NAME,
            credentials=credentials,
        )

        sleep_and_log()

    # Upload state summary tab for Criteria 6.
    criteria_6_summary_df = calculate_state_summary(
        transformed_df=transformed_covidtracking_df, columns=CRITERIA_6_SUMMARY_COLUMNS
    )
    if post_to_google_sheets:
        post_dataframe_to_google_sheets(
            df=criteria_6_summary_df,
            workbook_key=CDC_CRITERIA_6_GOOGLE_WORKBOOK_KEY,
            tab_name=STATE_SUMMARY_TAB_NAME,
            credentials=credentials,
        )

        sleep_and_log()

    # Merge all the summary data frames so that we can create a single summary sheet.
    combined_df = functools.reduce(
        # Use an inner join so that you'll only get entities that are represented in all criteria.
        # E.g., you'll not include Guam, NYC, etc which are reported separately in some of the sources.
        lambda left, right: pd.merge(
            left, right, on=[STATE_FIELD], how="inner", suffixes=["", "_y"]
        ),
        [
            criteria_1_summary_df,
            criteria_2_summary_df,
            # TODO(lbrown): Un-comment this when we find a path forward for CDC bed data.
            # criteria_3_summary_df,
            criteria_5_summary_df,
            criteria_6_summary_df,
        ],
    )

    if post_to_google_sheets:
        post_dataframe_to_google_sheets(
            df=combined_df.loc[:, CRITERIA_COMBINED_SUMMARY_COLUMNS],
            workbook_key=CDC_CRITERIA_SUMMARY_GOOGLE_WORKBOOK_KEY,
            tab_name=STATE_SUMMARY_TAB_NAME,
            credentials=credentials,
        )

        sleep_and_log()


if __name__ == "__main__":
    # Note: for faster debugging during development, you can set `post_to_google_sheets` to `False`.
    extract_transform_and_load_covid_data(post_to_google_sheets=True)
