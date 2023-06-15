import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from scipy import stats

from typing import List, Optional
from collections import defaultdict

from fp_analysis.Parser import PdfParser
from fp_analysis.Retriever import PdfRetriever
from fp_analysis.Metrics import MetricsCalculator

# region session state setup
if "in_current_analysis_session" not in st.session_state:
    st.session_state["in_current_analysis_session"] = False
if "year" not in st.session_state:
    st.session_state["year"] = None
if "race" not in st.session_state:
    st.session_state["race"] = None
if "sessions" not in st.session_state:
    st.session_state["sessions"] = None
if "current_race_df" not in st.session_state:
    st.session_state["current_race_df"] = None
if "current_sprint_df" not in st.session_state:
    st.session_state["current_sprint_df"] = None
# endregion

# region Introduction to page
st.markdown("# Sprint and Race Analysis")
st.write("## :chart_with_upwards_trend: Plot lots of things! :chart_with_downwards_trend:")
st.write("This page is to analyse MotoGP races.")
st.write("Choose a race weekend and the year.")
st.write("**This page is still under construction and so may change at any moment**")
st.write("I am still figuring out for this page too.")
# endregion


# region helper functions
def melt_df(df_to_melt: pd.DataFrame, new_columns: List[str]) -> pd.DataFrame:
    """Helper function to melt a wide dataframe into a long dataframe."""
    melted_df = df_to_melt.melt().dropna()
    melted_df.columns = new_columns
    return melted_df
# endregion


# todo remove all duplicate code of which there is a lot
# region Analysis
def analyse_dataframe(main_race_df: pd.DataFrame, sprint_race_df: Optional[pd.DataFrame] = None):
    """
    A function to visualise the race pace from main and sprint races.

    :param main_race_df: The data for the main race.
    :param sprint_race_df: The data for the sprint race, this is not available for any race pre-2023.
    """
    st.session_state["in_current_analysis_session"] = True

    with st.expander("Main race analysis"):
        show_race_data = st.checkbox("Show main race raw data")
        if show_race_data:
            st.dataframe(main_race_df)

        st.write("This plot shows the gap in seconds to the winner for each rider for each lap. If a rider is ahead of "
                 "the winner the gap will be positive. A line trending down shows the gap getting larger as the race "
                 "goes on, a line trending up shows a rider getting closer to the winner.")
        winner = main_race_df[main_race_df.columns[0]]
        gap_df = pd.DataFrame()
        for col in main_race_df.columns:
            gap_df[col] = winner - main_race_df[col]
        cum_gap_df = gap_df.cumsum()
        cum_gap_df.reset_index(inplace=True)
        melt_cum_gap_df = cum_gap_df.melt(id_vars=["index"], value_vars=list(main_race_df.columns))
        melt_cum_gap_df.rename(columns={"index": "Lap", "variable": "Rider", "value": "Gap"}, inplace=True)
        gap_to_winner_plotly = px.line(melt_cum_gap_df, x="Lap", y="Gap", color="Rider", markers=True)
        st.plotly_chart(gap_to_winner_plotly)

        st.write("This plot shows the difference between one lap and the next for each rider. A large value indicates "
                 "a long lap or a trip across the gravel trap. Maybe not so useful as they are all very consistent.")
        race_diff_df = main_race_df.diff()
        race_diff_df.reset_index(inplace=True)
        melt_race_diff_df = race_diff_df.melt(id_vars=["index"], value_vars=list(main_race_df.columns))
        melt_race_diff_df.rename(columns={"index": "Lap", "variable": "Rider", "value": "Gap"}, inplace=True)
        race_lap_diff_plotly = px.line(melt_race_diff_df, x="Lap", y="Gap", color="Rider", markers=True)
        st.plotly_chart(race_lap_diff_plotly)

        st.write("This box plot shows the spread of a rider's lap times. The smaller the box the more consistent they "
                 "are. The lower the box the faster they are. Outliers such as the first lap are shown by dots.")
        plotly_box_race_summary_fig = px.box(main_race_df, y=main_race_df.columns, hover_data=[main_race_df.index])
        st.plotly_chart(plotly_box_race_summary_fig)

    with st.expander("Sprint race analysis"):
        show_sprint_data = st.checkbox("Show sprint race raw data")
        if show_sprint_data:
            st.dataframe(sprint_race_df)

        spr_winner = sprint_race_df[sprint_race_df.columns[0]]
        gap_spr_df = pd.DataFrame()
        for col in sprint_race_df.columns:
            gap_spr_df[col] = spr_winner - sprint_race_df[col]
        cum_gap_spr_df = gap_spr_df.cumsum()
        cum_gap_spr_df.reset_index(inplace=True)
        melt_cum_gap_spr_df = cum_gap_spr_df.melt(id_vars=["index"], value_vars=list(sprint_race_df.columns))
        melt_cum_gap_spr_df.rename(columns={"index": "Lap", "variable": "Rider", "value": "Gap"}, inplace=True)
        spr_gap_to_winner_plotly = px.line(melt_cum_gap_spr_df, x="Lap", y="Gap", color="Rider", markers=True)
        st.plotly_chart(spr_gap_to_winner_plotly)

        sprint_diff_df = sprint_race_df.diff()
        sprint_diff_df.reset_index(inplace=True)
        melt_sprint_diff_df = sprint_diff_df.melt(id_vars=["index"], value_vars=list(sprint_race_df.columns))
        melt_sprint_diff_df.rename(columns={"index": "Lap", "variable": "Rider", "value": "Gap"}, inplace=True)
        sprint_lap_diff_plotly = px.line(melt_sprint_diff_df, x="Lap", y="Gap", color="Rider", markers=True)
        st.plotly_chart(sprint_lap_diff_plotly)

        plotly_box_sprint_summary_fig = px.box(
            sprint_race_df,
            y=sprint_race_df.columns,
            hover_data=[sprint_race_df.index]
        )
        st.plotly_chart(plotly_box_sprint_summary_fig)
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
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("Select year", range(2010, 2024), index=13)
        with col2:
            race = st.selectbox("Select race", races, index=5)
        submit = st.form_submit_button("Analyse race")

    if submit:
        if st.session_state["year"] == year and st.session_state["race"] == race:
            analyse_dataframe(st.session_state["current_race_df"], st.session_state["current_sprint_df"])
        with st.spinner("Please wait while files are retrieved and parsed..."):
            exists = pdfs.check_race_exist(year, race)

        if exists:
            all_race_file_names = pdfs.retrieve_race_files(year, race)
            st.success("All available races downloaded")
            st.session_state["year"] = year
            st.session_state["race"] = race
            final_df = pd.DataFrame()
            for file in all_race_file_names:
                if "SPR" in file:
                    sprint_df = parser.parse_pdf(file, delete_if_less_than_three=False)
                    st.session_state["current_sprint_df"] = sprint_df
                elif "RAC" in file:
                    race_df = parser.parse_pdf(file, delete_if_less_than_three=False)
                    st.session_state["current_race_df"] = race_df
                else:
                    st.error("Something went wrong parsing the race data.")
        elif not exists:
            st.write("Race does not exist")
        else:
            st.write("Something else happened")

    if st.session_state["current_race_df"] is not None:
        analyse_dataframe(st.session_state["current_race_df"], st.session_state["current_sprint_df"])
    else:
        st.warning("No sessions to analyse")

