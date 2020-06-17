import datetime

import pandas as pd

from covid.extract import DATE_SOURCE_FIELD
from covid.extract import extract_state_population_data
from covid.extract import get_state_abbreviations_to_names
from covid.extract import NEW_CASES_NEGATIVE_SOURCE_FIELD
from covid.extract import NEW_CASES_POSITIVE_SOURCE_FIELD
from covid.extract import STATE_SOURCE_FIELD
from covid.extract import TOTAL_CASES_SOURCE_FIELD
from covid.transform_utils import fit_and_predict_cubic_spline_in_r
from covid.transform_utils import generate_lag_column_name_formatter_and_column_names
from covid.transform_utils import generate_lags
from covid.transform_utils import get_consecutive_positive_or_negative_values
from covid.transform_utils import get_max_run_in_window


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
PERCENT_POSITIVE_NEW_TESTS_FIELD = "percent_positive_new_tests"
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
BASE_ICU_BEDS_FIELD = "% of ICU Beds Occupied"
BASE_INPATIENT_BEDS_FIELD = "% of Inpatient Beds Occupied"
CRITERIA_3A_NUM_CONSECUTIVE_DAYS = 7
CDC_CRITERIA_3A_HOSPITAL_BED_UTILIZATION_FIELD = "CDC Criteria 3A"
CDC_CRITERIA_3_COMBINED_FIELD = "CDC Criteria 3 (Combined)"
PHASE_1_OCCUPATION_THRESHOLD = 0.80  # Beds must be less than 80% full


# Other fields
CDC_CRITERIA_ALL_COMBINED_FIELD = "cdc_criteria_all_combined"
CDC_CRITERIA_ALL_COMBINED_OR_FIELD = "cdc_criteria_all_combined_using_or"
LAST_UPDATED_FIELD = "last_updated"
STATE_FIELD = "State"

# Define the list of columns that should appear in the state summary tab.
STATE_SUMMARY_COLUMNS = [
    STATE_FIELD,
    DATE_SOURCE_FIELD,
    TOTAL_CASES_SOURCE_FIELD,
    TOTAL_CASES_3_DAY_AVERAGE_CUBIC_SPLINE_FIELD,
    NEW_CASES_3DCS_FIELD,
    MAX_RUN_OF_DECREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD,
    CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD,
    MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD,
    CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD,
    NEW_CASES_TODAY_MINUS_NEW_CASES_14_DAYS_AGO_3DCS_FIELD,
    CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD,
    CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE,
    CDC_CRITERIA_1_COMBINED_FIELD,
    CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD,
    CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD,
    CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD,
    CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD,
    CDC_CRITERIA_2_COMBINED_FIELD,
    CDC_CRITERIA_ALL_COMBINED_FIELD,
    CDC_CRITERIA_ALL_COMBINED_OR_FIELD,
    LAST_UPDATED_FIELD,
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
]


def transform_covidtracking_data(df):

    # Replace abbreviations with full names.
    state_abbreviations_to_names = get_state_abbreviations_to_names()
    df = df.replace({STATE_SOURCE_FIELD: state_abbreviations_to_names})
    states = df[STATE_SOURCE_FIELD].unique()

    # Make the date column explicitly a date
    df[DATE_SOURCE_FIELD] = pd.to_datetime(df[DATE_SOURCE_FIELD])

    # Use a multi-index for state and date.
    df.set_index(keys=[STATE_SOURCE_FIELD, DATE_SOURCE_FIELD], inplace=True)

    # Sort by the index: state ascending, date ascending.
    df = df.sort_index()

    # Load state population data.
    state_population_data = extract_state_population_data()

    for state in states:
        print(f"Processing state {state}...")

        ###### Calculate criteria category 1. ######
        # Calculate new cases (raw).
        df.loc[(state,), NEW_CASES_FIELD] = (
            df.loc[(state,), TOTAL_CASES_SOURCE_FIELD].diff(periods=1).values
        )

        # Calculate new cases (raw diff).
        df.loc[(state,), NEW_CASES_DIFF_FIELD] = (
            df.loc[(state,), NEW_CASES_FIELD].diff(periods=1).values
        )

        # Calculate 3-day rolling average of total cases.
        df.loc[(state,), TOTAL_CASES_3_DAY_AVERAGE_FIELD] = (
            df.loc[(state,), TOTAL_CASES_SOURCE_FIELD]
            .rolling(window=3, min_periods=1, center=False)
            .mean()
            .values
        )

        # Calculate the cubic spline on the 3 day average of total cases.
        df.loc[
            (state,), TOTAL_CASES_3_DAY_AVERAGE_CUBIC_SPLINE_FIELD
        ] = fit_and_predict_cubic_spline_in_r(
            series_=df.loc[(state,), TOTAL_CASES_3_DAY_AVERAGE_FIELD],
            smoothing_parameter=0.5,
        ).values

        # Calculate 3-day rolling average of new cases.
        df.loc[(state,), NEW_CASES_3_DAY_AVERAGE_FIELD] = (
            df.loc[(state,), NEW_CASES_FIELD]
            .rolling(window=3, min_periods=1, center=False)
            .mean()
            # Replace NA new cases with `0` to fit the spline.
            .fillna(value=0)
            .values
        )

        # Calculate the cubic spline on the 3 day average of total cases.
        df.loc[(state,), NEW_CASES_3DCS_FIELD] = fit_and_predict_cubic_spline_in_r(
            series_=df.loc[(state,), NEW_CASES_3_DAY_AVERAGE_FIELD],
            smoothing_parameter=0.5,
        ).values

        # Calculate 3DCS new cases diff.
        df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD] = (
            df.loc[(state,), NEW_CASES_3DCS_FIELD].diff(periods=1).values
        )

        # Calculate consecutive increases or decreases.
        df.loc[
            (state,), CONSECUTIVE_INCREASE_NEW_CASES_3DCS_FIELD
        ] = get_consecutive_positive_or_negative_values(
            series_=df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD], positive_values=True
        ).values

        df.loc[
            (state,), CONSECUTIVE_DECREASE_NEW_CASES_3DCS_FIELD
        ] = get_consecutive_positive_or_negative_values(
            series_=df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD], positive_values=False
        ).values

        # Calculate criteria 1A: must see at least 9 days of a decrease in new cases over a 14 day window.
        df.loc[
            (state,), MAX_RUN_OF_DECREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD
        ] = get_max_run_in_window(
            series_=df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD],
            positive_values=False,
            window_size=14,
        ).values

        df.loc[(state,), CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD] = (
            df.loc[
                (state,), MAX_RUN_OF_DECREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD
            ]
            >= 10
        ).values

        # Calculate criteria 1B: must not see 5 or more days of an increase in new cases over a 14 day window.
        df.loc[
            (state,), MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD
        ] = get_max_run_in_window(
            series_=df.loc[(state,), NEW_CASES_3DCS_DIFF_FIELD],
            positive_values=True,
            window_size=14,
        ).values

        df.loc[(state,), CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD] = (
            df.loc[
                (state,), MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD
            ]
            < 5
        ).values

        # Calculate criteria 1C: new cases on T-0 must be < T-14.
        df.loc[(state,), NEW_CASES_TODAY_MINUS_NEW_CASES_14_DAYS_AGO_3DCS_FIELD] = (
            df.loc[(state,), NEW_CASES_3DCS_FIELD].diff(periods=14).values
        )
        df.loc[(state,), CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD] = (
            df.loc[(state,), NEW_CASES_TODAY_MINUS_NEW_CASES_14_DAYS_AGO_3DCS_FIELD] < 0
        ).values

        # Calculate criteria 1D: total cases from the last 14 days must be less than 10 per 100k population.
        df.loc[(state,), TOTAL_NEW_CASES_IN_14_DAY_WINDOW_FIELD] = (
            df.loc[(state,), NEW_CASES_FIELD]
            .fillna(value=0)
            .rolling(window=14, min_periods=1, center=False)
            .sum()
            .values
        )
        state_population = float(state_population_data.loc[state][0])
        df.loc[
            (state,), TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_FIELD
        ] = (
            (100000.0 * df.loc[(state,), TOTAL_NEW_CASES_IN_14_DAY_WINDOW_FIELD])
            / state_population
        ).values

        df.loc[
            (state,),
            TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_LOWER_THAN_THRESHOLD_FIELD,
        ] = (
            df.loc[
                (state,), TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_FIELD
            ]
            <= 10
        ).values

        df.loc[
            (state,),
            TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_PREVIOUSLY_ELEVATED_FIELD,
        ] = (
            (
                df.loc[
                    (state,),
                    TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_LOWER_THAN_THRESHOLD_FIELD,
                ]
                == 0
            ).cumsum()
            > 0
        ).values

        # To be true on 1D, the state must be (1) lower than the threshold, AND (2) previously above the threshold.
        df.loc[(state,), CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE] = (
            df.loc[
                (state,),
                TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_PREVIOUSLY_ELEVATED_FIELD,
            ]
            & df.loc[
                (state,),
                TOTAL_NEW_CASES_IN_14_DAY_WINDOW_PER_100_K_POPULATION_LOWER_THAN_THRESHOLD_FIELD,
            ]
        ).values

        # Calculate a textual indicator function for the rebound.
        df.loc[(state,), INDICATION_OF_NEW_CASES_REBOUND_FIELD] = (
            df.loc[
                (state,),
                [
                    MAX_RUN_OF_INCREASING_NEW_CASES_IN_14_DAY_WINDOW_3DCS_FIELD,
                    CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE,
                ],
            ].apply(func=indication_of_rebound, axis=1)
        ).values

        # Calculate all of the criteria combined in category 1.
        df.loc[(state,), CDC_CRITERIA_1_COMBINED_FIELD] = (
            (
                df.loc[(state,), CDC_CRITERIA_1A_COVID_CONTINUOUS_DECLINE_FIELD]
                & df.loc[(state,), CDC_CRITERIA_1B_COVID_NO_REBOUNDS_FIELD]
                & df.loc[(state,), CDC_CRITERIA_1C_COVID_OVERALL_DECLINE_FIELD]
            )
            | df.loc[(state,), CDC_CRITERIA_1D_COVID_NEAR_ZERO_INCIDENCE]
        ).values

        ###### Calculate criteria category 2. ######
        # For the criteria, we must add positive to negative tests to get the total (discarding inconclusive).
        df.loc[(state,), NEW_TESTS_TOTAL_FIELD] = (
            df.loc[(state,), NEW_CASES_POSITIVE_SOURCE_FIELD]
            + df.loc[(state,), NEW_CASES_NEGATIVE_SOURCE_FIELD]
        ).values

        new_tests_total_negatives_removed = df.loc[
            (state,), NEW_TESTS_TOTAL_FIELD
        ].values
        new_tests_total_negatives_removed[new_tests_total_negatives_removed < 0] = None

        df.loc[(state,), NEW_TESTS_TOTAL_FIELD] = new_tests_total_negatives_removed

        df.loc[(state,), NEW_TESTS_TOTAL_3_DAY_AVERAGE_FIELD] = (
            df.loc[(state,), NEW_TESTS_TOTAL_FIELD]
            .rolling(window=3, min_periods=1, center=False)
            .mean()
            .values
        )

        df.loc[
            (state,), NEW_TESTS_TOTAL_3DCS_FIELD
        ] = fit_and_predict_cubic_spline_in_r(
            series_=df.loc[(state,), NEW_TESTS_TOTAL_3_DAY_AVERAGE_FIELD],
            smoothing_parameter=0.5,
        ).values

        df.loc[(state,), POSITIVE_TESTS_TOTAL_3_DAY_AVERAGE_FIELD] = (
            df.loc[(state,), NEW_CASES_POSITIVE_SOURCE_FIELD]
            .rolling(window=3, min_periods=1, center=False)
            .mean()
            .values
        )

        df.loc[
            (state,), POSITIVE_TESTS_TOTAL_3DCS_FIELD
        ] = fit_and_predict_cubic_spline_in_r(
            series_=df.loc[(state,), POSITIVE_TESTS_TOTAL_3_DAY_AVERAGE_FIELD],
            smoothing_parameter=0.5,
        ).values

        df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_FIELD] = (
            df.loc[(state,), NEW_CASES_POSITIVE_SOURCE_FIELD].astype(float)
            / df.loc[(state,), NEW_TESTS_TOTAL_FIELD]
        ).values

        df.loc[(state,), FRACTION_POSITIVE_NEW_TESTS_3DCS_FIELD] = (
            df.loc[(state,), POSITIVE_TESTS_TOTAL_3DCS_FIELD].astype(float)
            / df.loc[(state,), NEW_TESTS_TOTAL_3DCS_FIELD]
        ).values

        df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD] = (
            100.0 * df.loc[(state,), FRACTION_POSITIVE_NEW_TESTS_3DCS_FIELD]
        ).values

        df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_DIFF_3DCS_FIELD] = (
            df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD].diff(periods=1)
        ).values

        # Calculate 2A: Achieve 14 or more consecutive days of decline in percent positive ... with up to 2-3
        # consecutive days of increasing or stable percent positive allowed as a grace period if data are inconsistent.
        df.loc[
            (state,), MAX_RUN_OF_DECREASING_PERCENT_POSITIVE_TESTS_3DCS_FIELD
        ] = get_max_run_in_window(
            series_=df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_DIFF_3DCS_FIELD],
            window_size=14,
            positive_values=False,
        ).values

        df.loc[
            (state,), MAX_RUN_OF_INCREASING_PERCENT_POSITIVE_TESTS_3DCS_FIELD
        ] = get_max_run_in_window(
            series_=df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_DIFF_3DCS_FIELD],
            window_size=14,
            positive_values=True,
        ).values

        df.loc[(state,), CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD] = (
            df.loc[(state,), MAX_RUN_OF_DECREASING_PERCENT_POSITIVE_TESTS_3DCS_FIELD]
            >= 11
        ).values

        # Calculate 2B: Total test volume is stable or increasing.
        df.loc[(state,), NEW_TESTS_TOTAL_DIFF_3DCS_FIELD] = (
            df.loc[(state,), NEW_TESTS_TOTAL_3DCS_FIELD].diff(periods=1).values
        )

        df.loc[
            (state,), MAX_RUN_OF_INCREASING_TOTAL_TESTS_3DCS_FIELD
        ] = get_max_run_in_window(
            series_=df.loc[(state,), NEW_TESTS_TOTAL_DIFF_3DCS_FIELD],
            window_size=14,
            positive_values=False,
        ).values

        df.loc[(state,), CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD] = (
            df.loc[(state,), NEW_TESTS_TOTAL_3DCS_FIELD].diff(periods=14) >= 0
        ).values

        # Calculate 2C: 14th day [of positive percentage of tests] must be lower than 1st day.
        df.loc[(state,), CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD] = (
            df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD].diff(periods=14) < 0
        ).values

        # Calculate 2D: Near-zero percent positive tests. [What is the explicit threshold here?]
        df.loc[(state,), CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD] = (
            df.loc[(state,), PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD] <= 1
        ).values

        # Calculate all of the criteria combined in category 2.
        df.loc[(state,), CDC_CRITERIA_2_COMBINED_FIELD] = (
            (
                df.loc[(state,), CDC_CRITERIA_2A_COVID_PERCENT_CONTINUOUS_DECLINE_FIELD]
                & df.loc[
                    (state,), CDC_CRITERIA_2B_COVID_TOTAL_TEST_VOLUME_INCREASING_FIELD
                ]
                & df.loc[(state,), CDC_CRITERIA_2C_COVID_PERCENT_OVERALL_DECLINE_FIELD]
            )
            | df.loc[(state,), CDC_CRITERIA_2D_COVID_NEAR_ZERO_POSITIVE_TESTS_FIELD]
        ).values

        # Calculate all of the criteria combined.
        df.loc[(state,), CDC_CRITERIA_ALL_COMBINED_FIELD] = (
            df.loc[(state,), CDC_CRITERIA_1_COMBINED_FIELD]
            & df.loc[(state,), CDC_CRITERIA_2_COMBINED_FIELD]
        ).values

        # Calculate all of the criteria combined.
        df.loc[(state,), CDC_CRITERIA_ALL_COMBINED_OR_FIELD] = (
            df.loc[(state,), CDC_CRITERIA_1_COMBINED_FIELD]
            | df.loc[(state,), CDC_CRITERIA_2_COMBINED_FIELD]
        ).values

    # Add an update time.
    df[LAST_UPDATED_FIELD] = datetime.datetime.now()

    # Remove the multi-index, converting date and state back to just columns.
    df = df.reset_index(drop=False)

    # Join to lags of important variables that we want to plot in sparklines.
    for field_to_lag, num_lags in [
        (NEW_CASES_3DCS_FIELD, 121),
        (PERCENT_POSITIVE_NEW_TESTS_3DCS_FIELD, 31),
        (NEW_TESTS_TOTAL_3DCS_FIELD, 31),
    ]:
        lags = generate_lags(df=df, column=field_to_lag, num_lags=num_lags)
        df = df.merge(
            right=lags, on=[STATE_SOURCE_FIELD, DATE_SOURCE_FIELD], how="left"
        )

    # Drop American Samoa because it's not reporting data
    df = df.loc[
        df[STATE_SOURCE_FIELD] != "American Samoa",
    ]

    # Copy state values into column called "State" instead of "state".
    df[STATE_FIELD] = df[STATE_SOURCE_FIELD]

    return df


def transform_cdc_ili_data(df):
    # Use the first row of the index as the index names.
    df.index.names = df.index[0]

    # Drop the row containing the labels, and set a new multi-index using the region, year, and week.
    df = df.iloc[1:].reset_index()

    # Validate that the only region type is states to sanity check data.
    assert set(df["REGION TYPE"].unique()) == {"States"}

    # Create a new column that combines the `YEAR` and `WEEK` column.
    # Note: The `-6` sets the date field to the start of the weekend (Saturday) for each week. We also subtract 1 week
    #   to start the weeks at zero and ensure that they align with `https://www.epochconverter.com/weeks/2020`.
    df[DATE_SOURCE_FIELD] = pd.to_datetime(
        df["YEAR"] + "-" + (df["WEEK"].astype(int) - 1).astype(str) + "-6",
        format="%Y-%U-%w",
    )

    # Rename the region field to match the `state` field present in other data frames.
    df = df.rename(columns={"REGION": STATE_FIELD})

    # Create a new multi-index containing the state name (`REGION`) and timestamp of the week.
    df = df.set_index(keys=[STATE_FIELD, DATE_SOURCE_FIELD])

    return df


def transform_cdc_data(cdc_current_df, cdc_historical_df):
    # Add date to index
    cdc_df = pd.concat([cdc_current_df, cdc_historical_df], axis=0)
    cdc_df[DATE_SOURCE_FIELD] = pd.to_datetime(cdc_df[DATE_SOURCE_FIELD])
    cdc_df = cdc_df.set_index(DATE_SOURCE_FIELD, append=True)
    cdc_df = cdc_df.sort_index()  # ascending date and state
    cdc_df.index.names = [STATE_FIELD, DATE_SOURCE_FIELD]

    # Drop duplicate dates
    cdc_df = cdc_df.loc[~cdc_df.index.duplicated(), :]

    # Convert data from str to float
    cdc_df[INPATIENT_PERCENT_OCCUPIED] = cdc_df[INPATIENT_PERCENT_OCCUPIED].astype(
        float
    )
    cdc_df[ICU_PERCENT_OCCUPIED] = cdc_df[ICU_PERCENT_OCCUPIED].astype(float)

    # Calculate 3A: ICU and in-patient beds must have < 80% utilization for 7 consecutive days
    # Hack because GROUPBY ROLLING doesn't work for datetimeindex. Thanks Pandas.
    states = cdc_df.index.get_level_values(STATE_FIELD).unique()
    state_dfs = []
    for state in states:
        state_df = cdc_df.xs(state, axis=0, level=STATE_FIELD)
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
        state_dfs.append(state_df)
    combined_df = pd.concat(state_dfs, keys=states, names=[STATE_FIELD])
    combined_df = combined_df.reset_index(drop=False)
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
