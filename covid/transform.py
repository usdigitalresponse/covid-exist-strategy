import datetime

import pandas as pd

from covid.extract import DATE_SOURCE_FIELD
from covid.extract import extract_state_population_data
from covid.extract import get_state_abbreviations_to_names
from covid.extract import NEW_CASES_NEGATIVE_SOURCE_FIELD
from covid.extract import NEW_CASES_POSITIVE_SOURCE_FIELD
from covid.extract import STATE_SOURCE_FIELD
from covid.extract import TOTAL_CASES_SOURCE_FIELD
from covid.extract import ICU_BEDS_PERCENT_SOURCE_FIELD
from covid.extract import INPATIENT_BEDS_PERCENT_SOURCE_FIELD
from covid.transform_utils import calculate_consecutive_boolean_series
from covid.transform_utils import calculate_consecutive_positive_or_negative_values
from covid.transform_utils import calculate_max_run_in_window
from covid.transform_utils import fit_and_predict_cubic_spline_in_r
from covid.transform_utils import generate_lag_column_name_formatter_and_column_names
from covid.transform_utils import generate_lags


# Define output field names.
# Criteria Category 1 Fields.
TOTAL_CASES_3_DAY_AVERAGE_FIELD = "total_cases_3_day_average"
TOTAL_CASES_3_DAY_AVERAGE_CUBIC_SPLINE_FIELD = "total_cases_3_day_average_cubic_spline"
NEW_CASES_3_DAY_AVERAGE_FIELD = "new_cases_3_day_average"
NEW_CASES_3DCS_FIELD = "New Cases (3DCS)"
NEW_CASES_FIELD = "new_cases"
NEW_CASES_DIFF_FIELD = "new_cases_compared_to_yesterday"
NEW_CASES_3DCS_DIFF_FIELD = "new_cases_compared_to_yesterday_3DCS"
CONSECUTIVE_INCREASE_NEW_CASES_3DCS_FIELD = (
    "Consecutive Days Increasing New Cases (3DCS)"
)
CONSECUTIVE_DECREASE_NEW_CASES_3DCS_FIELD = (
    "Consecutive Days Decreasing New Cases (3DCS)"
)
MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD = (
    "Max Days Increasing in 14 Day Window (3DCS)"
)
INDICATION_OF_NEW_CASES_REBOUND_FIELD = "Indication of Rebound"
MAX_RUN_OF_DECREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD = (
    "Max Days Decreasing in 14 Day Window (3DCS)"
)
TOTAL_NEW_CASES_IN_14_DAY_WINDOW_FIELD = "total_new_cases_in_14_day_window"
TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_FIELD = (
    "total_new_cases_in_14_day_window_per_100k_population"
)
TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_LOWER_THAN_THRESHOLD_FIELD = (
    "total_new_cases_in_14_day_window_per_100k_population_lower_than_threshold"
)
TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_PREVIOUSLY_ELEVATED_FIELD = "total_new_cases_in_14_day_window_per_100k_population_previously_higher_than_threshold"
CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD = "CDC Criteria 1A"
CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD = "CDC Criteria 1B"
NEW_CASES_TODAY_MINUS_NEW_CASES_14_DAYS_AGO_3DCS_FIELD = (
    "new_cases_compared_to_14_days_ago_3DCS"
)
CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD = "CDC Criteria 1C"
CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE = "CDC Criteria 1D"
CDC_CRITERIA_1_COMBINED_FIELD = "CDC Criteria 1 (Combined)"

# Criteria Category 2 Fields.
NEW_TESTS_TOTAL_FIELD = "new_tests_total"
NEW_TESTS_TOTAL_3_DAY_AVERAGE_FIELD = "new_tests_total_3_day_average"
NEW_TESTS_TOTAL_3DCS_FIELD = "New Tests (3DCS)"
POSITIVE_TESTS_TOTAL_3_DAY_AVERAGE_FIELD = "positive_tests_3_day_average"
POSITIVE_TESTS_TOTAL_3DCS_FIELD = "positive_tests_3dcs"
NEW_TESTS_TOTAL_DIFF_3DCS_FIELD = "new_tests_total_compared_to_yesterday_3dcs"
FRACTION_POSITIVE_NEW_TESTS_FIELD = "fraction_positive_new_tests"
PERCENT_POSITIVE_NEW_TESTS_FIELD = "% Positive Tests"
FRACTION_POSITIVE_NEW_TESTS_3DCS_FIELD = "Fraction Postive Tests (3DCS)"
PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD = "% Positive Tests (3DCS)"
PERCENT_POSITIVE_NEW_TESTS_DIFF_3DCS_FIELD = (
    "percent_positive_new_tests_compared_to_yesterday_3dcs"
)
MAX_RUN_OF_INCREASING_PERCENT_POSITIVE_TESTS_3DCS_FIELD = (
    "max_run_of_increasing_percent_positive_tests_3dcs"
)
MAX_RUN_OF_DECREASING_PERCENT_POSITIVE_TESTS_3DCS_FIELD = (
    "max_run_of_decreasing_percent_positive_tests_3dcs"
)
MAX_RUN_OF_INCREASING_TOTAL_TESTS_3DCS_FIELD = "max_run_of_increasing_total_tests_3dcs"

CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD = "CDC Criteria 2A"
CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD = "CDC Criteria 2B"
CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD = "CDC Criteria 2C"
CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD = "CDC Criteria 2D"
CDC_CRITERIA_2_COMBINED_FIELD = "CDC Criteria 2 (Combined)"

# Criteria Category 3 Fields.
MAX_ICU_BED_OCCUPATION_7_DAYS = "max_icu_bed_occupation_7_days"
MAX_INPATIENT_BED_OCCUPATION_7_DAYS = "max_inpatient_bed_occupation_7_days"
ICU_PERCENT_OCCUPIED = "icu_percent_occupied"
INPATIENT_PERCENT_OCCUPIED = "inpatient_bed_percent_occupied"
CRITERIA_3A_NUM_CONSECUTIVE_DAYS = 7
CDC_CRITERIA_3A_HOSPITAL_BED_UTILIZATION_FIELD = "CDC Criteria 3A"
CDC_CRITERIA_3_COMBINED_FIELD = "CDC Criteria 3 (Combined)"
PHASE_1_OCCUPATION_THRESHOLD = 0.80  # Beds must be less than 80% full

# Criteria Category 5 Fields.
PERCENT_ILI_SOURCE = "%UNWEIGHTED ILI"
PERCENT_ILI = "Percent ILI"
PERCENT_ILI_TODAY_MINUS_PERCENT_ILI_14_DAYS_AGO = "Percent ILI today minus 2 weeks ago"
PERCENT_ILI_SPLINE = "Percent ILI (Weekly Cubic Spline)"
PERCENT_ILI_SPLINE_DIFF = "Change in Percent ILI (WCS)"
MAX_RUN_OF_DECREASING_PERCENT_ILI_SPLINE_DIFF = (
    "Max Run of Decreasing Percent ILI (WCS)"
)
TOTAL_ILI_SOURCE = "ILITOTAL"
TOTAL_ILI = "Total ILI"
TOTAL_ILI_TODAY_MINUS_TOTAL_ILI_14_DAYS_AGO = "Total ILI today minus 2 weeks ago"
TOTAL_ILI_SPLINE = "Total ILI (WCS)"
TOTAL_ILI_SPLINE_DIFF = "Change in Total ILI (WCS)"
MAX_RUN_OF_DECREASING_TOTAL_ILI_SPLINE_DIFF = "Max Run of Decreasing Total ILI (WCS)"
CDC_CRITERIA_5A_14_DAY_DECLINE_TOTAL_ILI = "CDC Criteria 5A"
CDC_CRITERIA_5B_OVERALL_DECLINE_TOTAL_ILI = "CDC Criteria 5B"
CDC_CRITERIA_5C_14_DAY_DECLINE_PERCENT_ILI = "CDC Criteria 5C"
CDC_CRITERIA_5D_OVERALL_DECLINE_PERCENT_ILI = "CDC Criteria 5D"
CDC_CRITERIA_5_COMBINED = "CDC Criteria 5 (Partially combined, 5A-5D)"

# We choose 10 because that represents 9 weeks (63 days).
PERCENT_ILI_NUM_LAGS = 10
TOTAL_ILI_NUM_LAGS = 10
# Criteria 6A requires <= 20%.
CDC_CRITERIA_6A_MAX_PERCENT_THRESHOLD = 20

# Criteria Category 6 Fields.
PERCENT_POSITIVE_NEW_TESTS_NUM_LAGS = 61
MAX_PERCENT_POSITIVE_TESTS_14_DAYS_FIELD = "Highest % Positive (14 day window)"
MAX_PERCENT_POSITIVE_TESTS_14_DAYS_3DCS_FIELD = (
    "Highest % Positive (14 day window, 3DCS)"
)
PERCENT_POSITIVE_NEW_TESTS_3D_FIELD = "% Positive (3-day average)"
MAX_PERCENT_POSITIVE_TESTS_14_DAYS_3D_FIELD = (
    "Highest % Positive (14 day window, 3-day average)"
)
CDC_CRITERIA_6A_14_DAY_MAX_PERCENT_POSITIVE = "CDC Criteria 6A"

# Other fields
CDC_CRITERIA_ALL_COMBINED_FIELD = "cdc_criteria_all_combined"
CDC_CRITERIA_ALL_COMBINED_OR_FIELD = "cdc_criteria_all_combined_using_or"
LAST_RAN_FIELD = "script_last_ran"
LAST_UPDATED_FIELD = "data_last_changed"
STATE_FIELD = "State"

# Define a pre-formatted string to be used for CDC criteria positive and negative streak fields.
CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT = "{criteria_field} Positive Streak"
CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT = "{criteria_field} Negative Streak"

# Define the list of CDC Criteria 1 fields that should have streak fields appear in the state summary tab.
_CDC_CRITERIA_1_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD,
    CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD,
    CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD,
    CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE,
    CDC_CRITERIA_1_COMBINED_FIELD,
]

# Define the list of CDC Criteria 2 fields that should have streak fields appear in the state summary tab.
_CDC_CRITERIA_2_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD,
    CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD,
    CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD,
    CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD,
    CDC_CRITERIA_2_COMBINED_FIELD,
]

# Define the list of CDC Criteria 3 fields that should have streak fields appear in the state summary tab.
_CDC_CRITERIA_3_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_3A_HOSPITAL_BED_UTILIZATION_FIELD,
    CDC_CRITERIA_3_COMBINED_FIELD,
]

# Define the list of CDC Criteria 5 fields that should have streak fields appear in the state summary tab.
_CDC_CRITERIA_5_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_5A_14_DAY_DECLINE_TOTAL_ILI,
    CDC_CRITERIA_5B_OVERALL_DECLINE_TOTAL_ILI,
    CDC_CRITERIA_5C_14_DAY_DECLINE_PERCENT_ILI,
    CDC_CRITERIA_5D_OVERALL_DECLINE_PERCENT_ILI,
    CDC_CRITERIA_5_COMBINED,
]

# Define the list of CDC Criteria 6 fields that should have streak fields appear in the state summary tab.
_CDC_CRITERIA_6_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_6A_14_DAY_MAX_PERCENT_POSITIVE
]


# Define the list of CDC Criteria 1 positive streak fields that should appear in the state summary tab.
CDC_CRITERIA_1_POSITIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_1_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 1 negative streak fields that should appear in the state summary tab.
CDC_CRITERIA_1_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_1_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 2 positive streak fields that should appear in the state summary tab.
CDC_CRITERIA_2_POSITIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_2_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 2 negative streak fields that should appear in the state summary tab.
CDC_CRITERIA_2_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_2_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 3 positive streak fields that should appear in the state summary tab.
CDC_CRITERIA_3_POSITIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_3_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 3 negative streak fields that should appear in the state summary tab.
CDC_CRITERIA_3_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_3_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 5 positive streak fields that should appear in the state summary tab.
CDC_CRITERIA_5_POSITIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_5_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 5 negative streak fields that should appear in the state summary tab.
CDC_CRITERIA_5_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_5_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 6 positive streak fields that should appear in the state summary tab.
CDC_CRITERIA_6_POSITIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_6_STREAK_STATE_SUMMARY_FIELDS
]

# Define the list of CDC Criteria 6 negative streak fields that should appear in the state summary tab.
CDC_CRITERIA_6_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS = [
    CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT.format(criteria_field=criteria_field)
    for criteria_field in _CDC_CRITERIA_6_STREAK_STATE_SUMMARY_FIELDS
]


# Define the list of columns that should appear in summary workbooks.
# TODO: is there a smarter way to keep these in sync with what's generated?
_, new_cases_3dcs_lag_fields = generate_lag_column_name_formatter_and_column_names(
    column_name=NEW_CASES_3DCS_FIELD, num_lags=121
)

CRITERIA_1_SUMMARY_COLUMNS = [
    STATE_FIELD,
    CDC_CRITERIA_1_COMBINED_FIELD,
    # Unpack all of the T-120 to T-0 lag fields.
    *new_cases_3dcs_lag_fields,
    NEW_CASES_3DCS_FIELD,
    CONSECUTIVE_DECREASE_NEW_CASES_3DCS_FIELD,
    MAX_RUN_OF_DECREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD,
    INDICATION_OF_NEW_CASES_REBOUND_FIELD,
    CONSECUTIVE_INCREASE_NEW_CASES_3DCS_FIELD,
    MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD,
    CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD,
    CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD,
    CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD,
    CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE,
    # Add streak fields.
    *CDC_CRITERIA_1_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_1_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    LAST_RAN_FIELD,
    LAST_UPDATED_FIELD,
]


(
    _,
    percent_positive_3dcs_lag_fields,
) = generate_lag_column_name_formatter_and_column_names(
    column_name=PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD, num_lags=31
)

_, test_volume_lag_fields = generate_lag_column_name_formatter_and_column_names(
    column_name=NEW_TESTS_TOTAL_3DCS_FIELD, num_lags=31
)


CRITERIA_2_SUMMARY_COLUMNS = [
    STATE_FIELD,
    CDC_CRITERIA_2_COMBINED_FIELD,
    # Unpack all of the T-30 to T-0 lag fields.
    *test_volume_lag_fields,
    # Repeat the T-0 new cases field to serve as a spacer between sparklines.
    NEW_TESTS_TOTAL_3DCS_FIELD,
    *percent_positive_3dcs_lag_fields,
    # Repeat the T-0 percent positive field to serve as a spacer between sparklines.
    PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD,
    CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD,
    CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD,
    CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD,
    CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD,
    # Add streak fields.
    *CDC_CRITERIA_2_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_2_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    LAST_RAN_FIELD,
    LAST_UPDATED_FIELD,
]


CRITERIA_3_SUMMARY_COLUMNS = [
    STATE_FIELD,
    MAX_ICU_BED_OCCUPATION_7_DAYS,
    MAX_INPATIENT_BED_OCCUPATION_7_DAYS,
    CDC_CRITERIA_3A_HOSPITAL_BED_UTILIZATION_FIELD,
    CDC_CRITERIA_3_COMBINED_FIELD,
    INPATIENT_PERCENT_OCCUPIED,
    ICU_PERCENT_OCCUPIED,
    # Add streak fields.
    *CDC_CRITERIA_3_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_3_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    LAST_RAN_FIELD,
    LAST_UPDATED_FIELD,
]

# Define the list of columns that should appear in summary workbooks.
# TODO: is there a smarter way to keep these in sync with what's generated?
_, total_ili_lag_fields = generate_lag_column_name_formatter_and_column_names(
    column_name=TOTAL_ILI, num_lags=TOTAL_ILI_NUM_LAGS
)

_, percent_ili_lag_fields = generate_lag_column_name_formatter_and_column_names(
    column_name=PERCENT_ILI, num_lags=PERCENT_ILI_NUM_LAGS
)

CRITERIA_5_SUMMARY_COLUMNS = [
    STATE_FIELD,
    # Unpack all of the lag fields.
    *total_ili_lag_fields,
    # Repeat the T-0 field to serve as a spacer between sparklines.
    TOTAL_ILI,
    *percent_ili_lag_fields,
    PERCENT_ILI,
    CDC_CRITERIA_5A_14_DAY_DECLINE_TOTAL_ILI,
    CDC_CRITERIA_5B_OVERALL_DECLINE_TOTAL_ILI,
    CDC_CRITERIA_5C_14_DAY_DECLINE_PERCENT_ILI,
    CDC_CRITERIA_5D_OVERALL_DECLINE_PERCENT_ILI,
    CDC_CRITERIA_5_COMBINED,
    # Add streak fields.
    *CDC_CRITERIA_5_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_5_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    LAST_RAN_FIELD,
    LAST_UPDATED_FIELD,
]


CRITERIA_6_SUMMARY_COLUMNS = [
    STATE_FIELD,
    # Unpack all of the lag fields.
    *percent_positive_3dcs_lag_fields,
    # Repeat the T-0 field to serve as a spacer between sparklines.
    MAX_PERCENT_POSITIVE_TESTS_14_DAYS_3DCS_FIELD,
    PERCENT_POSITIVE_NEW_TESTS_FIELD,
    CDC_CRITERIA_6A_14_DAY_MAX_PERCENT_POSITIVE,
    # Add streak fields.
    *CDC_CRITERIA_6_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_6_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    LAST_RAN_FIELD,
    LAST_UPDATED_FIELD,
]

CRITERIA_COMBINED_SUMMARY_COLUMNS = [
    STATE_FIELD,
    CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD,
    CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD,
    CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD,
    CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE,
    CDC_CRITERIA_1_COMBINED_FIELD,
    *CDC_CRITERIA_1_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_1_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD,
    CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD,
    CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD,
    CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD,
    CDC_CRITERIA_2_COMBINED_FIELD,
    *CDC_CRITERIA_2_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_2_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    # TODO(lbrown): Un-comment these when we find a path forward for CDC bed data.
    # CDC_CRITERIA_3A_HOSPITAL_BED_UTILIZATION_FIELD,
    # CDC_CRITERIA_3_COMBINED_FIELD,
    # *CDC_CRITERIA_3_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    # *CDC_CRITERIA_3_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    CDC_CRITERIA_5A_14_DAY_DECLINE_TOTAL_ILI,
    CDC_CRITERIA_5B_OVERALL_DECLINE_TOTAL_ILI,
    CDC_CRITERIA_5C_14_DAY_DECLINE_PERCENT_ILI,
    CDC_CRITERIA_5D_OVERALL_DECLINE_PERCENT_ILI,
    CDC_CRITERIA_5_COMBINED,
    *CDC_CRITERIA_5_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_5_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    CDC_CRITERIA_6A_14_DAY_MAX_PERCENT_POSITIVE,
    # Add streak fields.
    *CDC_CRITERIA_6_POSITIVE_STREAK_STATE_SUMMARY_FIELDS,
    *CDC_CRITERIA_6_NEGATIVE_STREAK_STATE_SUMMARY_FIELDS,
    LAST_RAN_FIELD,
    LAST_UPDATED_FIELD,
]


def transform_covidtracking_data(covidtracking_df):
    """Transforms data from https://covidtracking.com/ and calculates CDC Criteria 1 (A, B, C, D) and 2 (A, B, C, D)."""
    # Rename state field into column called "State" instead of "state".
    covidtracking_df = covidtracking_df.rename(
        columns={STATE_SOURCE_FIELD: STATE_FIELD}
    )

    # Replace abbreviations with full names.
    state_abbreviations_to_names = get_state_abbreviations_to_names()
    covidtracking_df = covidtracking_df.replace(
        {STATE_FIELD: state_abbreviations_to_names}
    )

    states = covidtracking_df[STATE_FIELD].unique()

    # Make the date column explicitly a date
    covidtracking_df[DATE_SOURCE_FIELD] = pd.to_datetime(
        covidtracking_df[DATE_SOURCE_FIELD]
    )

    # Use a multi-index for state and date.
    covidtracking_df.set_index(keys=[STATE_FIELD, DATE_SOURCE_FIELD], inplace=True)

    # Sort by the index: state ascending, date ascending.
    covidtracking_df = covidtracking_df.sort_index()

    # Load state population data.
    state_population_data = extract_state_population_data()

    for state in states:
        print(f"Processing covid tracking data for state {state}...")

        ###### Calculate criteria category 1. ######
        # Calculate new cases (raw).
        covidtracking_df.loc[(state,), NEW_CASES_FIELD] = (
            covidtracking_df.loc[(state,), TOTAL_CASES_SOURCE_FIELD]
            .diff(periods=1)
            .values
        )

        # Calculate new cases (raw diff).
        covidtracking_df.loc[(state,), NEW_CASES_DIFF_FIELD] = (
            covidtracking_df.loc[(state,), NEW_CASES_FIELD].diff(periods=1).values
        )

        # Calculate 3-day rolling average of total cases.
        covidtracking_df.loc[(state,), TOTAL_CASES_3_DAY_AVERAGE_FIELD] = (
            covidtracking_df.loc[(state,), TOTAL_CASES_SOURCE_FIELD]
            .rolling(window=3, min_periods=1, center=False)
            .mean()
            .values
        )

        # Calculate the cubic spline on the 3 day average of total cases.
        covidtracking_df.loc[
            (state,), TOTAL_CASES_3_DAY_AVERAGE_CUBIC_SPLINE_FIELD
        ] = fit_and_predict_cubic_spline_in_r(
            series_=covidtracking_df.loc[(state,), TOTAL_CASES_3_DAY_AVERAGE_FIELD],
            smoothing_parameter=0.5,
        ).values

        # Calculate 3-day rolling average of new cases.
        covidtracking_df.loc[(state,), NEW_CASES_3_DAY_AVERAGE_FIELD] = (
            covidtracking_df.loc[(state,), NEW_CASES_FIELD]
            .rolling(window=3, min_periods=1, center=False)
            .mean()
            # Replace NA new cases with `0` to fit the spline.
            .fillna(value=0)
            .values
        )

        # Calculate the cubic spline on the 3 day average of total cases.
        covidtracking_df.loc[
            (state,), NEW_CASES_3DCS_FIELD
        ] = fit_and_predict_cubic_spline_in_r(
            series_=covidtracking_df.loc[(state,), NEW_CASES_3_DAY_AVERAGE_FIELD],
            smoothing_parameter=0.5,
        ).values

        # Calculate 3DCS new cases diff.
        covidtracking_df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD] = (
            covidtracking_df.loc[(state,), NEW_CASES_3DCS_FIELD].diff(periods=1).values
        )

        # Calculate consecutive increases or decreases.
        covidtracking_df.loc[
            (state,), CONSECUTIVE_INCREASE_NEW_CASES_3DCS_FIELD
        ] = calculate_consecutive_positive_or_negative_values(
            series_=covidtracking_df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD],
            positive_values=True,
        ).values

        covidtracking_df.loc[
            (state,), CONSECUTIVE_DECREASE_NEW_CASES_3DCS_FIELD
        ] = calculate_consecutive_positive_or_negative_values(
            series_=covidtracking_df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD],
            positive_values=False,
        ).values

        # Calculate criteria 1A: must see at least 9 days of a decrease in new cases over a 14 day window.
        covidtracking_df.loc[
            (state,), MAX_RUN_OF_DECREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD
        ] = calculate_max_run_in_window(
            series_=covidtracking_df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD],
            positive_values=False,
            window_size=14,
        ).values

        covidtracking_df.loc[
            (state,), CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD
        ] = (
            covidtracking_df.loc[
                (state,), MAX_RUN_OF_DECREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD
            ]
            >= 10
        ).values

        # Calculate criteria 1B: must not see 5 or more days of an increase in new cases over a 14 day window.
        covidtracking_df.loc[
            (state,), MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD
        ] = calculate_max_run_in_window(
            series_=covidtracking_df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD],
            positive_values=True,
            window_size=14,
        ).values

        covidtracking_df.loc[(state,), CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD] = (
            covidtracking_df.loc[
                (state,), MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD
            ]
            < 5
        ).values

        # Calculate criteria 1C: new cases on T-0 must be < T-14.
        covidtracking_df.loc[
            (state,), NEW_CASES_TODAY_MINUS_NEW_CASES_14_DAYS_AGO_3DCS_FIELD
        ] = (
            covidtracking_df.loc[(state,), NEW_CASES_3DCS_FIELD].diff(periods=14).values
        )
        covidtracking_df.loc[(state,), CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD] = (
            covidtracking_df.loc[
                (state,), NEW_CASES_TODAY_MINUS_NEW_CASES_14_DAYS_AGO_3DCS_FIELD
            ]
            < 0
        ).values

        # Calculate criteria 1D: total cases from the last 14 days must be less than 10 per 100k population.
        covidtracking_df.loc[(state,), TOTAL_NEW_CASES_IN_14_DAY_WINDOW_FIELD] = (
            covidtracking_df.loc[(state,), NEW_CASES_FIELD]
            .fillna(value=0)
            .rolling(window=14, min_periods=1, center=False)
            .sum()
            .values
        )
        state_population = float(state_population_data.loc[state][0])
        covidtracking_df.loc[
            (state,), TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_FIELD
        ] = (
            (
                100000.0
                * covidtracking_df.loc[(state,), TOTAL_NEW_CASES_IN_14_DAY_WINDOW_FIELD]
            )
            / state_population
        ).values

        covidtracking_df.loc[
            (state,),
            TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_LOWER_THAN_THRESHOLD_FIELD,
        ] = (
            covidtracking_df.loc[
                (state,), TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_FIELD
            ]
            <= 10
        ).values

        covidtracking_df.loc[
            (state,),
            TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_PREVIOUSLY_ELEVATED_FIELD,
        ] = (
            (
                covidtracking_df.loc[
                    (state,),
                    TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_LOWER_THAN_THRESHOLD_FIELD,
                ]
                == 0
            ).cumsum()
            > 0
        ).values

        # To be true on 1D, the state must be (1) lower than the threshold, AND (2) previously above the threshold.
        covidtracking_df.loc[(state,), CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE] = (
            covidtracking_df.loc[
                (state,),
                TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_PREVIOUSLY_ELEVATED_FIELD,
            ]
            & covidtracking_df.loc[
                (state,),
                TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_LOWER_THAN_THRESHOLD_FIELD,
            ]
        ).values

        # Calculate a textual indicator function for the rebound.
        covidtracking_df.loc[(state,), INDICATION_OF_NEW_CASES_REBOUND_FIELD] = (
            covidtracking_df.loc[
                (state,),
                [
                    MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD,
                    CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE,
                ],
            ].apply(func=indication_of_rebound, axis=1)
        ).values

        # Calculate all of the criteria combined in category 1.
        covidtracking_df.loc[(state,), CDC_CRITERIA_1_COMBINED_FIELD] = (
            (
                covidtracking_df.loc[
                    (state,), CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD
                ]
                & covidtracking_df.loc[
                    (state,), CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD
                ]
                & covidtracking_df.loc[
                    (state,), CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD
                ]
            )
            | covidtracking_df.loc[(state,), CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE]
        ).values

        ###### Calculate criteria category 2. ######
        # For the criteria, we must add positive to negative tests to get the total (discarding inconclusive).
        covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_FIELD] = (
            covidtracking_df.loc[(state,), NEW_CASES_POSITIVE_SOURCE_FIELD]
            + covidtracking_df.loc[(state,), NEW_CASES_NEGATIVE_SOURCE_FIELD]
        ).values

        new_tests_total_negatives_removed = covidtracking_df.loc[
            (state,), NEW_TESTS_TOTAL_FIELD
        ].values
        new_tests_total_negatives_removed[new_tests_total_negatives_removed < 0] = None

        covidtracking_df.loc[
            (state,), NEW_TESTS_TOTAL_FIELD
        ] = new_tests_total_negatives_removed

        covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_3_DAY_AVERAGE_FIELD] = (
            covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_FIELD]
            .rolling(window=3, min_periods=1, center=False)
            .mean()
            .values
        )

        covidtracking_df.loc[
            (state,), NEW_TESTS_TOTAL_3DCS_FIELD
        ] = fit_and_predict_cubic_spline_in_r(
            series_=covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_3_DAY_AVERAGE_FIELD],
            smoothing_parameter=0.5,
        ).values

        covidtracking_df.loc[(state,), POSITIVE_TESTS_TOTAL_3_DAY_AVERAGE_FIELD] = (
            covidtracking_df.loc[(state,), NEW_CASES_POSITIVE_SOURCE_FIELD]
            .rolling(window=3, min_periods=1, center=False)
            .mean()
            .values
        )

        covidtracking_df.loc[
            (state,), POSITIVE_TESTS_TOTAL_3DCS_FIELD
        ] = fit_and_predict_cubic_spline_in_r(
            series_=covidtracking_df.loc[
                (state,), POSITIVE_TESTS_TOTAL_3_DAY_AVERAGE_FIELD
            ],
            smoothing_parameter=0.5,
        ).values

        covidtracking_df.loc[(state,), FRACTION_POSITIVE_NEW_TESTS_FIELD] = (
            covidtracking_df.loc[(state,), NEW_CASES_POSITIVE_SOURCE_FIELD].astype(
                float
            )
            / covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_FIELD]
        ).values

        covidtracking_df.loc[(state,), FRACTION_POSITIVE_NEW_TESTS_3DCS_FIELD] = (
            covidtracking_df.loc[(state,), POSITIVE_TESTS_TOTAL_3DCS_FIELD].astype(
                float
            )
            / covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_3DCS_FIELD]
        ).values

        covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD] = (
            100.0
            * covidtracking_df.loc[(state,), FRACTION_POSITIVE_NEW_TESTS_3DCS_FIELD]
        ).values

        covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_DIFF_3DCS_FIELD] = (
            covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD].diff(
                periods=1
            )
        ).values

        # Calculate 2A: Achieve 14 or more consecutive days of decline in percent positive ... with up to 2-3
        # consecutive days of increasing or stable percent positive allowed as a grace period if data are inconsistent.
        covidtracking_df.loc[
            (state,), MAX_RUN_OF_DECREASING_PERCENT_POSITIVE_TESTS_3DCS_FIELD
        ] = calculate_max_run_in_window(
            series_=covidtracking_df.loc[
                (state,), PERCENT_POSITIVE_NEW_TESTS_DIFF_3DCS_FIELD
            ],
            window_size=14,
            positive_values=False,
        ).values

        covidtracking_df.loc[
            (state,), MAX_RUN_OF_INCREASING_PERCENT_POSITIVE_TESTS_3DCS_FIELD
        ] = calculate_max_run_in_window(
            series_=covidtracking_df.loc[
                (state,), PERCENT_POSITIVE_NEW_TESTS_DIFF_3DCS_FIELD
            ],
            window_size=14,
            positive_values=True,
        ).values

        covidtracking_df.loc[
            (state,), CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD
        ] = (
            covidtracking_df.loc[
                (state,), MAX_RUN_OF_DECREASING_PERCENT_POSITIVE_TESTS_3DCS_FIELD
            ]
            >= 11
        ).values

        # Calculate 2B: Total test volume is stable or increasing.
        covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_DIFF_3DCS_FIELD] = (
            covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_3DCS_FIELD]
            .diff(periods=1)
            .values
        )

        covidtracking_df.loc[
            (state,), MAX_RUN_OF_INCREASING_TOTAL_TESTS_3DCS_FIELD
        ] = calculate_max_run_in_window(
            series_=covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_DIFF_3DCS_FIELD],
            window_size=14,
            positive_values=False,
        ).values

        covidtracking_df.loc[
            (state,), CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD
        ] = (
            covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_3DCS_FIELD].diff(periods=14)
            >= 0
        ).values

        # Calculate 2C: 14th day [of positive percentage of tests] must be lower than 1st day.
        covidtracking_df.loc[
            (state,), CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD
        ] = (
            covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD].diff(
                periods=14
            )
            < 0
        ).values

        # Calculate 2D: Near-zero percent positive tests. [What is the explicit threshold here?]
        covidtracking_df.loc[
            (state,), CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD
        ] = (
            covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD] <= 1
        ).values

        # Calculate all of the criteria combined in category 2.
        covidtracking_df.loc[(state,), CDC_CRITERIA_2_COMBINED_FIELD] = (
            (
                covidtracking_df.loc[
                    (state,), CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD
                ]
                & covidtracking_df.loc[
                    (state,), CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD
                ]
                & covidtracking_df.loc[
                    (state,), CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD
                ]
            )
            | covidtracking_df.loc[
                (state,), CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD
            ]
        ).values

        # Calculate Criteria 6A
        covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_FIELD] = (
            covidtracking_df.loc[(state,), FRACTION_POSITIVE_NEW_TESTS_FIELD] * 100
        ).values

        covidtracking_df.loc[(state,), MAX_PERCENT_POSITIVE_TESTS_14_DAYS_FIELD] = (
            covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_FIELD]
            .rolling("14D")
            .max()
            .values
        )

        covidtracking_df.loc[
            (state,), MAX_PERCENT_POSITIVE_TESTS_14_DAYS_3DCS_FIELD
        ] = (
            covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD]
            .rolling("14D")
            .max()
            .values
        )

        covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3D_FIELD] = (
            100
            * covidtracking_df.loc[(state,), POSITIVE_TESTS_TOTAL_3_DAY_AVERAGE_FIELD]
            / covidtracking_df.loc[(state,), NEW_TESTS_TOTAL_3_DAY_AVERAGE_FIELD]
        ).values

        covidtracking_df.loc[(state,), MAX_PERCENT_POSITIVE_TESTS_14_DAYS_3D_FIELD] = (
            covidtracking_df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3D_FIELD]
            .rolling("14D")
            .max()
            .values
        )

        covidtracking_df.loc[(state,), CDC_CRITERIA_6A_14_DAY_MAX_PERCENT_POSITIVE] = (
            covidtracking_df.loc[
                (state,), MAX_PERCENT_POSITIVE_TESTS_14_DAYS_3DCS_FIELD
            ]
            <= CDC_CRITERIA_6A_MAX_PERCENT_THRESHOLD
        ).values

        # Calculate all of the criteria combined.
        covidtracking_df.loc[(state,), CDC_CRITERIA_ALL_COMBINED_FIELD] = (
            covidtracking_df.loc[(state,), CDC_CRITERIA_1_COMBINED_FIELD]
            & covidtracking_df.loc[(state,), CDC_CRITERIA_2_COMBINED_FIELD]
        ).values

        # Calculate all of the criteria combined.
        covidtracking_df.loc[(state,), CDC_CRITERIA_ALL_COMBINED_OR_FIELD] = (
            covidtracking_df.loc[(state,), CDC_CRITERIA_1_COMBINED_FIELD]
            | covidtracking_df.loc[(state,), CDC_CRITERIA_2_COMBINED_FIELD]
        ).values

        # Calculate criteria streaks for Criteria 1 (A, B, C, D, Combined), Criteria 2 (A, B, C, D, Combined), and
        # Criteria 6 (A).
        for criteria_field in [
            CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD,
            CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD,
            CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD,
            CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE,
            CDC_CRITERIA_1_COMBINED_FIELD,
            CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD,
            CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD,
            CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD,
            CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD,
            CDC_CRITERIA_2_COMBINED_FIELD,
            CDC_CRITERIA_6A_14_DAY_MAX_PERCENT_POSITIVE,
        ]:
            # Calculate both the negative (not meeting criteria) and positive (meeting criteria) streak series.
            (
                positive_streak_series,
                negative_streak_series,
            ) = calculate_consecutive_boolean_series(
                boolean_series=covidtracking_df.loc[(state,), criteria_field]
            )

            # Add the positive streak series to the combined frame.
            covidtracking_df.loc[
                (state,),
                CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT.format(
                    criteria_field=criteria_field
                ),
            ] = positive_streak_series.values

            # Add the negative streak series to the combined frame.
            covidtracking_df.loc[
                (state,),
                CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT.format(
                    criteria_field=criteria_field
                ),
            ] = negative_streak_series.values

    # Add an update time.
    covidtracking_df[LAST_RAN_FIELD] = datetime.datetime.now()

    # Remove the multi-index, converting date and state back to just columns.
    covidtracking_df = covidtracking_df.reset_index(drop=False)

    # Use the date for each data entry as when the data were last updated.
    covidtracking_df[LAST_UPDATED_FIELD] = covidtracking_df[DATE_SOURCE_FIELD]

    # Join to lags of important variables that we want to plot in sparklines.
    for field_to_lag, num_lags in [
        (NEW_CASES_3DCS_FIELD, 121),
        (PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD, 31),
        (NEW_TESTS_TOTAL_3DCS_FIELD, 31),
    ]:
        lags = generate_lags(
            df=covidtracking_df, column=field_to_lag, num_lags=num_lags
        )
        covidtracking_df = covidtracking_df.merge(
            right=lags, on=[STATE_FIELD, DATE_SOURCE_FIELD], how="left"
        )

    # Drop American Samoa because it's not reporting data
    covidtracking_df = covidtracking_df.loc[
        covidtracking_df[STATE_FIELD] != "American Samoa",
    ]

    return covidtracking_df


def transform_cdc_ili_data(ili_df):
    """Transforms data from https://gis.cdc.gov/grasp/fluview/fluportaldashboard.html and calculates CDC Criteria 5
    (A, B, C).
    """
    # Validate that the only region type is states to sanity check data.
    assert set(ili_df["REGION TYPE"].unique()) == {"States"}

    # Create a new column that combines the `YEAR` and `WEEK` column.
    # Note: The `-6` sets the date field to the start of the weekend (Saturday) for each week. We also subtract 1 week
    #   to start the weeks at zero and ensure that they align with `https://www.epochconverter.com/weeks/2020`.
    ili_df[DATE_SOURCE_FIELD] = pd.to_datetime(
        ili_df["YEAR"].astype(str)
        + "-"
        + (ili_df["WEEK"].astype(int) - 1).astype(str)
        + "-6",
        format="%Y-%U-%w",
    )

    # Rename the region field to match the `state` field present in other data frames.
    ili_df = ili_df.rename(
        columns={
            "REGION": STATE_FIELD,
            PERCENT_ILI_SOURCE: PERCENT_ILI,
            TOTAL_ILI_SOURCE: TOTAL_ILI,
        }
    )

    states = ili_df[STATE_FIELD].unique()

    # Create a new multi-index containing the state name (`REGION`) and timestamp of the week.
    ili_df = ili_df.set_index(keys=[STATE_FIELD, DATE_SOURCE_FIELD])

    # Sort by the index: state ascending, date ascending.
    ili_df = ili_df.sort_index()

    # Replace `X` with null.
    ili_df = ili_df.replace(to_replace="X", value=None)

    # Convert to floats.
    ili_df[TOTAL_ILI] = ili_df[TOTAL_ILI].astype(float)
    ili_df[PERCENT_ILI] = ili_df[PERCENT_ILI].astype(float)

    for state in states:
        print(f"Processing CDC ILI data for state {state}...")

        ###### Calculate criteria category 5. ######
        # Calculate total cases (spline).
        ili_df.loc[(state,), TOTAL_ILI_SPLINE] = fit_and_predict_cubic_spline_in_r(
            series_=ili_df.loc[(state,), TOTAL_ILI], smoothing_parameter=0.5
        ).values

        # Calculate percent cases (spline).
        ili_df.loc[(state,), PERCENT_ILI_SPLINE] = fit_and_predict_cubic_spline_in_r(
            series_=ili_df.loc[(state,), PERCENT_ILI], smoothing_parameter=0.5
        ).values

        # Calculate change in total ILI
        ili_df.loc[(state,), TOTAL_ILI_SPLINE_DIFF] = (
            ili_df.loc[(state,), TOTAL_ILI_SPLINE].diff(periods=1).values
        )

        # Calculate change in percent ILI
        ili_df.loc[(state,), PERCENT_ILI_SPLINE_DIFF] = (
            ili_df.loc[(state,), PERCENT_ILI_SPLINE].diff(periods=1).values
        )

        # Calculate criteria 5A: must see two consecutive declines in weekly total ILI data.
        ili_df.loc[
            (state,), MAX_RUN_OF_DECREASING_TOTAL_ILI_SPLINE_DIFF
        ] = calculate_max_run_in_window(
            series_=ili_df.loc[(state,), TOTAL_ILI_SPLINE_DIFF],
            positive_values=False,
            window_size=2,
        ).values

        ili_df.loc[(state,), CDC_CRITERIA_5A_14_DAY_DECLINE_TOTAL_ILI] = (
            ili_df.loc[(state,), MAX_RUN_OF_DECREASING_TOTAL_ILI_SPLINE_DIFF] >= 2
        ).values

        # Calculate criteria 5B: weekly total must be lower than weekly total 2 weeks ago.
        ili_df.loc[(state,), TOTAL_ILI_TODAY_MINUS_TOTAL_ILI_14_DAYS_AGO] = (
            ili_df.loc[(state,), TOTAL_ILI].diff(periods=2).values
        )
        ili_df.loc[(state,), CDC_CRITERIA_5B_OVERALL_DECLINE_TOTAL_ILI] = (
            ili_df.loc[(state,), TOTAL_ILI_TODAY_MINUS_TOTAL_ILI_14_DAYS_AGO] < 0
        ).values

        # Calculate criteria 5C: must see two consecutive declines in weekly percent ILI data.
        ili_df.loc[
            (state,), MAX_RUN_OF_DECREASING_PERCENT_ILI_SPLINE_DIFF
        ] = calculate_max_run_in_window(
            series_=ili_df.loc[(state,), PERCENT_ILI_SPLINE_DIFF],
            positive_values=False,
            window_size=2,
        ).values

        ili_df.loc[(state,), CDC_CRITERIA_5C_14_DAY_DECLINE_PERCENT_ILI] = (
            ili_df.loc[(state,), MAX_RUN_OF_DECREASING_PERCENT_ILI_SPLINE_DIFF] >= 2
        ).values

        # Calculate criteria 5D: weekly percent must be lower than weekly percent 2 weeks ago.
        ili_df.loc[(state,), PERCENT_ILI_TODAY_MINUS_PERCENT_ILI_14_DAYS_AGO] = (
            ili_df.loc[(state,), PERCENT_ILI].diff(periods=2).values
        )
        ili_df.loc[(state,), CDC_CRITERIA_5D_OVERALL_DECLINE_PERCENT_ILI] = (
            ili_df.loc[(state,), PERCENT_ILI_TODAY_MINUS_PERCENT_ILI_14_DAYS_AGO] < 0
        ).values

        # Calculate the combined rating so far.
        ili_df.loc[(state,), CDC_CRITERIA_5_COMBINED] = (
            ili_df.loc[(state,), CDC_CRITERIA_5A_14_DAY_DECLINE_TOTAL_ILI]
            & ili_df.loc[(state,), CDC_CRITERIA_5B_OVERALL_DECLINE_TOTAL_ILI]
            & ili_df.loc[(state,), CDC_CRITERIA_5C_14_DAY_DECLINE_PERCENT_ILI]
            & ili_df.loc[(state,), CDC_CRITERIA_5D_OVERALL_DECLINE_PERCENT_ILI]
        ).values

        # Calculate criteria streaks for Criteria 5 (A, B, C, D, Combined).
        for criteria_field in [
            CDC_CRITERIA_5A_14_DAY_DECLINE_TOTAL_ILI,
            CDC_CRITERIA_5B_OVERALL_DECLINE_TOTAL_ILI,
            CDC_CRITERIA_5C_14_DAY_DECLINE_PERCENT_ILI,
            CDC_CRITERIA_5D_OVERALL_DECLINE_PERCENT_ILI,
            CDC_CRITERIA_5_COMBINED,
        ]:
            # Calculate both the negative (not meeting criteria) and positive (meeting criteria) streak series.
            (
                positive_streak_series,
                negative_streak_series,
            ) = calculate_consecutive_boolean_series(
                boolean_series=ili_df.loc[(state,), criteria_field]
            )

            # Add the positive streak series to the combined frame.
            ili_df.loc[
                (state,),
                CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT.format(
                    criteria_field=criteria_field
                ),
            ] = positive_streak_series.values

            # Add the negative streak series to the combined frame.
            ili_df.loc[
                (state,),
                CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT.format(
                    criteria_field=criteria_field
                ),
            ] = negative_streak_series.values

    # Remove the multi-index, converting date and state back to just columns.
    ili_df = ili_df.reset_index(drop=False)

    # Join to lags of important variables that we want to plot in sparklines.
    for field_to_lag, num_lags in [
        (PERCENT_ILI, PERCENT_ILI_NUM_LAGS),
        (TOTAL_ILI, TOTAL_ILI_NUM_LAGS),
    ]:
        lags = generate_lags(
            df=ili_df,
            column=field_to_lag,
            num_lags=num_lags,
            lag_timedelta=datetime.timedelta(days=7),
        )
        ili_df = ili_df.merge(
            right=lags, on=[STATE_FIELD, DATE_SOURCE_FIELD], how="left"
        )

    ili_df[LAST_UPDATED_FIELD] = ili_df[DATE_SOURCE_FIELD]
    ili_df[LAST_RAN_FIELD] = datetime.datetime.now()

    return ili_df


def transform_hhs_beds_data(hhs_beds_current_df, hhs_beds_historical_df='TODO'):
    """Transforms data from TKTK and calculates CDC Criteria 3
    (A).
    """
    # Add date to index
    # TODO hhs_df = pd.concat([hhs_beds_current_df, hhs_beds_historical_df], axis=0)
    hhs_df = hhs_beds_current_df
    hhs_df[DATE_SOURCE_FIELD] = pd.to_datetime(hhs_df[DATE_SOURCE_FIELD])
    hhs_df = hhs_df.set_index(DATE_SOURCE_FIELD, append=True)
    hhs_df.index.names = [STATE_FIELD, DATE_SOURCE_FIELD]
    hhs_df.rename(
        {ICU_BEDS_PERCENT_SOURCE_FIELD: ICU_PERCENT_OCCUPIED,
         INPATIENT_BEDS_PERCENT_SOURCE_FIELD: INPATIENT_PERCENT_OCCUPIED},
        axis=1,
        inplace=True)

    # Drop duplicate dates
    hhs_df = hhs_df.loc[~hhs_df.index.duplicated(), :]

    # Drop nan-index data.
    hhs_df = hhs_df.loc[hhs_df.index.dropna()]

    # Replace empty data with None
    hhs_df[ICU_PERCENT_OCCUPIED] = (
        hhs_df[ICU_PERCENT_OCCUPIED].astype(str).replace("", None)
    )
    hhs_df[INPATIENT_PERCENT_OCCUPIED] = (
        hhs_df[INPATIENT_PERCENT_OCCUPIED].astype(str).replace("", None)
    )

    # Convert data from str to float
    hhs_df[INPATIENT_PERCENT_OCCUPIED] = hhs_df[INPATIENT_PERCENT_OCCUPIED].astype(
        float
    )
    hhs_df[ICU_PERCENT_OCCUPIED] = hhs_df[ICU_PERCENT_OCCUPIED].astype(float)

    hhs_df = hhs_df.sort_index()  # ascending date and state

    # Calculate 3A: ICU and in-patient beds must have < 80% utilization for 7 consecutive days
    # Hack because GROUPBY ROLLING doesn't work for datetimeindex. Thanks Pandas.
    states = hhs_df.index.get_level_values(STATE_FIELD).unique()
    state_dfs = []
    for state in states:
        print(f"Transforming CDC beds data for state {state}...")
        state_df = hhs_df.xs(state, axis=0, level=STATE_FIELD)
        state_df[MAX_INPATIENT_BED_OCCUPATION_7_DAYS] = (
            state_df[INPATIENT_PERCENT_OCCUPIED]
            .rolling(f"{CRITERIA_3A_NUM_CONSECUTIVE_DAYS}D")
            .max()
        )
        state_df[MAX_ICU_BED_OCCUPATION_7_DAYS] = (
            state_df[ICU_PERCENT_OCCUPIED]
            .rolling(f"{CRITERIA_3A_NUM_CONSECUTIVE_DAYS}D")
            .max()
        )
        state_df[CDC_CRITERIA_3A_HOSPITAL_BED_UTILIZATION_FIELD] = (
            state_df[MAX_INPATIENT_BED_OCCUPATION_7_DAYS] < PHASE_1_OCCUPATION_THRESHOLD
        ) & (state_df[MAX_ICU_BED_OCCUPATION_7_DAYS] < PHASE_1_OCCUPATION_THRESHOLD)
        state_df[CDC_CRITERIA_3_COMBINED_FIELD] = state_df[
            CDC_CRITERIA_3A_HOSPITAL_BED_UTILIZATION_FIELD
        ]

        # Calculate criteria streaks for Criteria 5 (A, B, C, D, Combined).
        for criteria_field in [
            CDC_CRITERIA_3A_HOSPITAL_BED_UTILIZATION_FIELD,
            CDC_CRITERIA_3_COMBINED_FIELD,
        ]:
            # Calculate both the negative (not meeting criteria) and positive (meeting criteria) streak series.
            (
                positive_streak_series,
                negative_streak_series,
            ) = calculate_consecutive_boolean_series(
                boolean_series=state_df[criteria_field]
            )

            # Add the positive streak series to the combined frame.
            state_df[
                CDC_CRITERIA_POSITIVE_STREAK_FIELD_PRE_FORMAT.format(
                    criteria_field=criteria_field
                )
            ] = positive_streak_series.values

            # Add the negative streak series to the combined frame.
            state_df[
                CDC_CRITERIA_NEGATIVE_STREAK_FIELD_PRE_FORMAT.format(
                    criteria_field=criteria_field
                )
            ] = negative_streak_series.values

        state_dfs.append(state_df)

    combined_df = pd.concat(state_dfs, keys=states, names=[STATE_FIELD])

    # Reindex so gaps are NaN instead of missing
    unique_dates = combined_df.index.get_level_values(level=DATE_SOURCE_FIELD).unique()
    unique_states = combined_df.index.get_level_values(level=STATE_FIELD).unique()
    combined_df = combined_df.reindex(
        pd.MultiIndex.from_product([unique_states, unique_dates])
    )
    combined_df = combined_df.reset_index(drop=False)
    combined_df[LAST_UPDATED_FIELD] = combined_df[DATE_SOURCE_FIELD]
    combined_df[LAST_RAN_FIELD] = datetime.datetime.now()
    return combined_df


def indication_of_rebound(series_):
    indicator = None
    if series_[CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE] is True:
        indicator = "Low Case Count"
    else:
        if series_[MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD] >= 0:
            indicator = "Clear"
        if series_[MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD] >= 3:
            indicator = "Caution"
        if series_[MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD] >= 5:
            indicator = "Rebound"

    return indicator
