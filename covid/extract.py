import json
import logging
from io import BytesIO

import pandas as pd
import requests
from df2gspread import gspread2df

import covid.extract_config.cdc_govcloud as cgc
from covid.extract_utils import unzip_string


# Define the names of the CSVs returned by the CDC's FluView dashboard API.
# Note: data contained in these CSVs are used to calculate influenza-like-illness (ILI) criteria.
ILI_NET_CSV = "ILINet.csv"
WHO_NREVSS_PUBLIC_HEALTH_LABS_CSV = "WHO_NREVSS_Public_Health_Labs.csv"
WHO_NREVSS_CLINICAL_LABS_CSV = "WHO_NREVSS_Clinical_Labs.csv"


DATE_SOURCE_FIELD = "date"
STATE_SOURCE_FIELD = "state"
STATE_FIELD = "State"
TOTAL_CASES_SOURCE_FIELD = "positive"
NEW_CASES_NEGATIVE_SOURCE_FIELD = "negativeIncrease"
NEW_CASES_POSITIVE_SOURCE_FIELD = "positiveIncrease"
LAST_UPDATED_SOURCE_FIELD = "dateModified"

# For bed utilization data
CATEGORY_3_DATA_GOOGLE_SHEET_KEY = "1-BSd5eFbNsypygMkhuGX1OWoUsF2u4chpsu6aC4cgVo"
CATEGORY_3_HISTORICAL_DATA_TAB = "Historical Data"

logger = logging.getLogger(__name__)


def extract_covidtracking_current_data():
    current_url = "https://covidtracking.com/api/v1/states/current.json"
    current_data = requests.get(current_url).json()
    current_df = pd.DataFrame(current_data)

    return current_df


def extract_covidtracking_historical_data():
    historical_url = "https://covidtracking.com/api/v1/states/daily.json"
    historical_data = requests.get(historical_url).json()
    historical_df = pd.DataFrame(historical_data)

    historical_df[DATE_SOURCE_FIELD] = historical_df[DATE_SOURCE_FIELD].astype(str)

    return historical_df


def extract_state_population_data():
    # Note that the working directory is assumed to be the repository root.
    df = pd.read_csv("./covid/data/population.csv")

    df = df.set_index(keys=[STATE_SOURCE_FIELD])

    return df


def get_state_abbreviations_to_names():
    with open("./covid/data/us_state_abbreviations.json") as state_abbreviations_file:
        abbreviations = json.load(state_abbreviations_file)

    return abbreviations


def power_bi_extractor(response):
    data = json.loads(response.text)
    timestamp = extract_cdc_data_date()
    value_list = data["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][1]["DM1"]
    for vl in value_list:
        data_row = vl["C"]
        if len(data_row) == 3:
            yield vl["C"] + [timestamp]
        else:
            logger.warning(f"Unexpected power BI response value: {data_row}")


def extract_cdc_data_date():
    # Get data date as seen on the website
    response = requests.post(
        cgc.URL,
        headers={**cgc.BASE_HEADERS, **cgc.DATA_DATE_HEADERS},
        data=open("./covid/extract_config/data_date.json"),
    )

    data = json.loads(response.text)
    return data["results"][0]["result"]["data"]["dsr"]["DS"][0]["PH"][0]["DM0"][0]["M0"]


def extract_cdc_inpatient_beds():
    # State Representative Estimates for Percentage of Inpatient Beds Occupied (All Patients)
    response = requests.post(
        cgc.URL,
        headers={**cgc.BASE_HEADERS, **cgc.INPATIENT_BED_HEADERS},
        data=open("./covid/extract_config/inpatient_bed_query.json"),
    )

    df = pd.DataFrame(
        power_bi_extractor(response),
        columns=[
            STATE_FIELD,
            "inpatient_bed_percent_occupied",
            "inpatient_beds_occupied",
            DATE_SOURCE_FIELD,
        ],
    )

    df = df.set_index(STATE_FIELD)

    return df


def extract_cdc_icu_beds():
    # State Representative Estimates for Percentage of ICU Beds Occupied (All Patients)
    response = requests.post(
        cgc.URL,
        headers={**cgc.BASE_HEADERS, **cgc.ICU_BED_HEADERS},
        data=open("./covid/extract_config/icu_bed_query.json"),
    )

    df = pd.DataFrame(
        power_bi_extractor(response),
        columns=[
            STATE_FIELD,
            "icu_percent_occupied",
            "icu_beds_occupied",
            DATE_SOURCE_FIELD,
        ],
    )

    df = df.set_index(STATE_FIELD)

    return df


def extract_cdc_facilities_reporting():
    response = requests.post(
        cgc.URL,
        headers={**cgc.BASE_HEADERS, **cgc.FACILITIES_REPORTING_HEADERS},
        data=open("./covid/extract_config/facilities_reporting_query.json"),
    )

    df = pd.DataFrame(
        power_bi_extractor(response),
        columns=[
            STATE_FIELD,
            "facilities_percent_reporting",
            "facilities_reporting",
            DATE_SOURCE_FIELD,
        ],
    )

    df = df.set_index(STATE_FIELD)

    return df


def extract_cdc_ili_data():
    current_url = "https://gis.cdc.gov/grasp/flu2/PostPhase02DataDownload"
    payload = {
        "AppVersion": "Public",
        "DatasourceDT": [{"ID": 0, "Name": "WHO_NREVSS"}, {"ID": 1, "Name": "ILINet"}],
        "RegionTypeId": 5,
        # Request all 59 regions.
        "SubRegionsDT": [{"ID": i, "Name": i} for i in range(1, 60)],
        "SeasonsDT": [{"ID": 59, "Name": "59"}],
    }

    response = requests.post(
        url=current_url,
        headers={"Content-Type": "application/json;charset=UTF-8"},
        data=json.dumps(payload),
    )
    filenames_to_contents_map = unzip_string(response.content)

    df = pd.read_csv(
        filepath_or_buffer=BytesIO(filenames_to_contents_map[ILI_NET_CSV]), skiprows=1
    )

    return df


def extract_cdc_beds_current_data():
    inpatient_bed_df = extract_cdc_inpatient_beds()
    icu_bed_df = extract_cdc_icu_beds()
    hospitals_reporting_df = extract_cdc_facilities_reporting()
    cdc_df = pd.concat([inpatient_bed_df, icu_bed_df, hospitals_reporting_df], axis=1)
    cdc_df = cdc_df.loc[:, ~cdc_df.columns.duplicated()]
    return cdc_df


def extract_cdc_beds_historical_data(credentials):
    cdc_historical_df = gspread2df.download(
        CATEGORY_3_DATA_GOOGLE_SHEET_KEY,
        CATEGORY_3_HISTORICAL_DATA_TAB,
        credentials=credentials,
        col_names=True,
    )
    cdc_historical_df = cdc_historical_df.set_index(STATE_FIELD)

    return cdc_historical_df


def extract_rt_live_data():
    rt_live_url = "https://d14wlfuexuxgcm.cloudfront.net/covid/rt.csv"
    rt_live_df = pd.read_csv(rt_live_url)

    return rt_live_df
