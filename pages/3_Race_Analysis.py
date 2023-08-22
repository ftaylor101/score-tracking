import pandas as pd
import streamlit as st
import plotly.express as px

from typing import List

from utils.Parser import PdfParser
from utils.Retriever import PdfRetriever
from fp_analysis.Metrics import MetricsCalculator


# region session state setup
if "in_current_analysis_session" not in st.session_state:
    st.session_state["in_current_analysis_session"] = False
if "year" not in st.session_state:
    st.session_state["year"] = None
if "race" not in st.session_state:
    st.session_state["race"] = None
if "current_race_df" not in st.session_state:
    st.session_state["current_race_df"] = None
if "category" not in st.session_state:
    st.session_state["category"] = None
# endregion

# region Introduction to page
st.markdown("# Sprint and Race Analysis")
st.write("## :chart_with_upwards_trend: Plot lots of things! :chart_with_downwards_trend:")
st.write("This page is to analyse races from most classes within the MotoGP championship.")
st.write("Choose a category, the race and the year.")
st.write("**This page is still under construction and so may change at any moment**")
st.write("MotoE to come as a later update.")

# endregion


# region helper functions
def melt_df(df_to_melt: pd.DataFrame, new_columns: List[str]) -> pd.DataFrame:
    """Helper function to melt a wide dataframe into a long dataframe."""
    melted_df = df_to_melt.melt().dropna()
    melted_df.columns = new_columns
    return melted_df
# endregion


# region Analysis
def analyse_dataframe(the_race_df: pd.DataFrame):
    """
    A function to visualise the race pace from main and sprint races.

    :param the_race_df: The data for the race.
    """
    st.session_state["in_current_analysis_session"] = True

    show_race_data = st.checkbox("Show race raw data")
    if show_race_data:
        st.dataframe(the_race_df)

    st.write("This plot shows the gap in seconds to the winner for each rider for each lap. If a rider is ahead of "
             "the winner the gap will be positive. A line trending down shows the gap getting larger as the race "
             "goes on, a line trending up shows a rider getting closer to the winner.")
    winner = the_race_df[the_race_df.columns[0]]
    gap_df = pd.DataFrame()
    for col in the_race_df.columns:
        gap_df[col] = winner - the_race_df[col]
    cum_gap_df = gap_df.cumsum()
    cum_gap_df.reset_index(inplace=True)
    melt_cum_gap_df = cum_gap_df.melt(id_vars=["index"], value_vars=list(the_race_df.columns))
    melt_cum_gap_df.rename(columns={"index": "Lap", "variable": "Rider", "value": "Gap"}, inplace=True)
    gap_to_winner_plotly = px.line(melt_cum_gap_df, x="Lap", y="Gap", color="Rider", markers=True)
    st.plotly_chart(gap_to_winner_plotly)

    st.write("This box plot shows the spread of a rider's lap times. The smaller the box the more consistent they "
             "are. The lower the box the faster they are. Outliers such as the first lap are shown by dots. The middle "
             "50% of lap times are covered by the box.")
    plotly_box_race_summary_fig = px.box(the_race_df, y=the_race_df.columns, hover_data=[the_race_df.index])
    st.plotly_chart(plotly_box_race_summary_fig)

# endregion


if __name__ == "__main__":
    # region Analysis Class instantiation
    pdfs = PdfRetriever()
    parser = PdfParser()
    metric_calculator = MetricsCalculator()
    # endregion

    races = [
        "QAT", "INA", "ARG", "AME", "POR", "SPA", "FRA", "ITA", "CAT", "GER", "NED", "GBR", "AUT", "RSM", "ARA", "JPN",
        "THA", "AUS", "MAL", "VAL"
    ]
    with st.form('my_form'):
        race_category = st.radio("Select race", ["MotoGP Race", "MotoGP Sprint", "Moto2", "Moto3"])
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("Select year", range(2010, 2024), index=13)
        with col2:
            race = st.selectbox("Select race", races, index=5)
        analyse = st.form_submit_button("Analyse race")

    if analyse:
        if st.session_state["year"] == year and st.session_state["race"] == race \
                and st.session_state["category"] == race_category:
            analyse_dataframe(the_race_df=st.session_state["current_race_df"])
        with st.spinner("Please wait while files are retrieved and parsed..."):
            exists = pdfs.check_race_exist(year, race, race_category)

        if exists:
            race_file_name = pdfs.retrieve_race_files(year, race, race_category, "analysis")
            st.success("Available race downloaded")
            st.session_state["year"] = year
            st.session_state["race"] = race
            st.session_state["category"] = race_category
            final_df = pd.DataFrame()
            if race_file_name:
                race_df = parser.parse_pdf(race_file_name, delete_if_less_than_three=False)
                st.session_state["current_race_df"] = race_df
            else:
                st.error("Something went wrong parsing the race data.")
        elif not exists:
            st.write("Race does not exist")
        else:
            st.write("Something else happened")

    if st.session_state["current_race_df"] is not None:
        analyse_dataframe(the_race_df=st.session_state["current_race_df"])
    else:
        st.warning("No sessions to analyse")
