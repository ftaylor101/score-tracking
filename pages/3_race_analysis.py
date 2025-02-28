import pandas as pd
import streamlit as st
from copy import deepcopy

from utils.DataWrangler import DataWrangler


# region session state setup
if "current_race_df" not in st.session_state:
    st.session_state["current_race_df"] = None
# endregion

# region Introduction to page
st.markdown("# Sprint and Race Analysis")
st.write("## :chart_with_upwards_trend: Plot lots of things! :chart_with_downwards_trend:")
st.write("This page is to analyse races from most classes within the MotoGP championship.")
st.write("Choose a category, the race and the year.")
st.write("**This page is still under construction and so may change at any moment**")
st.write("MotoE to come as a later update.")
# endregion


# region Analysis
def visualise_race(the_race_df: pd.DataFrame):
    """
    A function to visualise the race pace from main and sprint races.

    :param the_race_df: The data for the race.
    """
    data_df = data_wrangler.drop_column(the_race_df, "Session")

    show_race_data = st.checkbox("Show race raw data")
    if show_race_data:
        st.dataframe(data_df)

    st.write("This plot shows the gap in seconds to the winner for each rider for each lap. If a rider is ahead of "
             "the winner the gap will be positive. A line trending down shows the gap getting larger as the race "
             "goes on, a line trending up shows a rider getting closer to the winner.")
    winner = data_wrangler.values_of_first_column(data_df)
    cum_gap_df = data_wrangler.gap_between_column_and_dataframe(data_df, winner)
    melt_cum_gap_df = data_wrangler.melt_on_lap(cum_gap_df, list(data_wrangler.get_column_names(data_df)))
    melt_cum_gap_df = data_wrangler.rename_columns(
        melt_cum_gap_df, {"index": "Lap", "variable": "Rider", "value": "Gap"}
    )
    gap_to_winner_plotly = data_wrangler.plotly_line_chart(melt_cum_gap_df, "Lap", "Gap", "Rider")
    st.plotly_chart(gap_to_winner_plotly)

    st.write("This plot shows the spread of a rider's lap times. The smaller the box the more consistent they "
             "are. The lower the box the faster they are. Outliers such as the first lap are shown by dots. The middle "
             "50% of lap times are covered by the box. Actual times and lap time distribution is shown in the violin "
             "plot. (Select an area on the plot to zoom in.)")

    plot_type = st.radio(label="Select plot type", options=["Box plot", "Violin plot"])
    if plot_type == "Violin plot":
        plotly_race_summary_fig = data_wrangler.plotly_standard_violin(
            data_df, list(data_wrangler.get_column_names(data_df))
        )
    else:
        plotly_race_summary_fig = data_wrangler.plotly_box_plot(data_df)
    st.plotly_chart(plotly_race_summary_fig)
# endregion


if __name__ == "__main__":
    data_wrangler = DataWrangler()

    categories = ["MotoGP", "Moto2", "Moto3"]
    session_names = ["RAC", "SPR"]
    races = [
        "THA", "ARG", "AME", "QAT", "SPA", "FRA", "GBR", "ARA", "ITA", "NED", "GER", "AUT", "CZE", "HUN", "CAT", "RSM",
        "JPN", "INA", "AUS", "MAL", "POR", "VAL"
    ]
    with st.form('my_form'):
        # race_category = st.radio("Select race", ["MotoGP Race", "MotoGP Sprint", "Moto2", "Moto3"])
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            race_class = st.selectbox("Select class", categories, index=0)
        with col2:
            year = st.selectbox("Select year", range(2010, 2026), index=14)
        with col3:
            race = st.selectbox("Select race", races, index=5)
        with col4:
            race_type = st.selectbox("Select race type", session_names, index=0)
        analyse = st.form_submit_button("Analyse race")

    if analyse:
        if race_type == "SPR" and race_class != "MotoGP":
            st.error("Sprint selected for non MotoGP class")
            st.stop()
        data = data_wrangler.get_race(race_class, year, race, race_type)
        st.session_state["current_race_df"] = deepcopy(data)
        visualise_race(data)
    elif st.session_state["current_race_df"] is not None:
        visualise_race(st.session_state["current_race_df"])
