import streamlit as st
import pandas as pd
import numpy as np
from copy import deepcopy

from utils.DataWrangler import DataWrangler


# region session state setup
if "current_analysis_df" not in st.session_state:
    st.session_state["current_analysis_df"] = None
# endregion

# region Introduction to page
st.markdown("# Free Practice Analysis")
st.write("## :chart_with_upwards_trend: Plot lots of things! :chart_with_downwards_trend:")
st.write("This page is to analyse MotoGP/2/3 practice sessions.")
# st.write("If the race has completed (for GP only currently), the data can be added for comparison. "
#          "Tick the box above 'Get sessions' button.")
st.write("Choose a race weekend, choose the sessions to display and the year.")
st.write("The **session choice** is important as the session names have changed over the years. If the incorrect "
         "session name is picked, it will result in missing data.")
st.write("**This page is still under construction and so may change at any moment**")
st.write("I am still figuring out what is useful and what is not, and how best to incorporate tyre compound and life "
         "into the analysis.")
# endregion


# region Analysis
def visualise_data(full_df: pd.DataFrame):
    orig_df = data_wrangler.copy_df(full_df)
    sessions = data_wrangler.copy_df(full_df["Session"])
    orig_laps_only_df = data_wrangler.drop_column(full_df, "Session")
    data_df = data_wrangler.drop_column(full_df, "Session")

    # remove any short laps where riders take a shortcut to the pits or slow/cool down laps
    upper_tol = st.number_input(
        "Select maximum lap time",
        min_value=data_wrangler.median_of_all_columns(data_df),
        max_value=data_wrangler.median_of_all_columns(data_df) + 50.0,
        value=data_wrangler.median_of_all_columns(data_df) + 1.0,
        step=0.001,
        format="%.3f",
        help="Any laps slower than this value will be ignored",
        key=1
    )

    # fastest lap is assumed to be only up to 10% faster
    min_lap_time_allowed = data_wrangler.median_of_all_columns(data_df) * 0.9
    max_lap_time_allowed = upper_tol  # slowest lap used in analysis is set by user

    # make a new filtered dataframe after getting rid of unhelpful lap times
    df = data_wrangler.mask_df(data_df, min_lap_time_allowed, max_lap_time_allowed)

    # get fastest lap for relative comparison purposes
    fastest_lap, fastest_rider = data_wrangler.minimum_of_all_columns(df)
    st.write(f"Fastest lap was {fastest_lap} by {fastest_rider}")

    # sort the dataframe by median, from lowest to highest
    df, riders = data_wrangler.sort_by_median(df)

    show_data = st.checkbox("Show data")
    if show_data:
        st.dataframe(df)  # show data

    # with st.expander("See all rider summary plots"):
    with_sessions_df = data_wrangler.horizontally_concat_dataframes(df, sessions)
    with_sessions_melt_df = data_wrangler.melt_on_session(with_sessions_df)

    st.write("The plot below shows all the lap times recorded by a rider for all available sessions. Clicking on the "
             "rider name on the right hand side hides the data, double clicking shows only their data. Clicking on "
             "other riders will add/remove their data.")
    plot_colours = st.radio(
        label="Choose what the colours represent:",
        options=["Colour by rider", "Colour by session"]
    )
    colour = "Session" if plot_colours == "Colour by session" else "Riders"
    plotly_strip_summary_fig = data_wrangler.plotly_strip_chart(
        with_sessions_melt_df, x_name="LapTimes", y_name="Riders", colour=colour
    )
    st.plotly_chart(plotly_strip_summary_fig)

    st.write("The box plot below shows the spread of the data. If the rider's laps are arranged from fastest to "
             "slowest with times shown on the vertical axis. The box represents the middle 50% of laps, the line in "
             "the middle of the box is the median, which is the middle lap in terms of lap time. 50% of the rider's "
             "laps will be faster than this, and 50% will be slower. Points are outliers, so either a particularly "
             "quick or slow lap.")
    plotly_box_summary_fig = data_wrangler.plotly_box_plot(df)
    st.plotly_chart(plotly_box_summary_fig)

    with st.form("rider_picker"):
        selected_riders = st.multiselect(
            "Pick riders to compare or leave blank for all (but really just select a couple)", riders)
        riders_picked = st.form_submit_button(label="Plot lap times")

    if riders_picked:
        if len(selected_riders) > 0:
            rider_laps = data_wrangler.filter_on_columns(df, selected_riders)
        else:
            rider_laps = df
            selected_riders = data_wrangler.get_column_names(df)

        # plotting the PDF of the lap times
        rider_laps = data_wrangler.horizontally_concat_dataframes(rider_laps, sessions)
        # hist_data = data_wrangler.make_histogram_data(rider_laps, selected_riders)
        # pdf_fig = data_wrangler.plotly_distribution_plot(hist_data, selected_riders, False)
        # st.plotly_chart(pdf_fig)

        rider_laps_melt = data_wrangler.melt_on_session(rider_laps)
        plotly_strip_select_riders_fig = data_wrangler.plotly_strip_chart(
            rider_laps_melt, "LapTimes", "Riders", "Session"
        )
        st.plotly_chart(plotly_strip_select_riders_fig)

        # filtered_df = data_wrangler.filter_on_columns(df, selected_riders)
        # plotly_box_fig = data_wrangler.plotly_box_plot(filtered_df)
        # st.plotly_chart(plotly_box_fig)

        st.write("The violin plot below shows a little more data than the summarising box plot in the section above. "
                 "The curved line shows the distribution of laps, so a peak (though the distribution is shown "
                 "vertically) means more laps are concentrated around this lap time. A wider, flatter curve means "
                 "the laps are spread across a larger range.")
        violin_fig = data_wrangler.plotly_stacked_violin_figure(rider_laps_melt, selected_riders)
        st.plotly_chart(violin_fig)

        # plot empirical cumulative distribution functions for each selected rider
        # ecdf_fig = data_wrangler.plotly_ecdf_plot(rider_laps, selected_riders)
        # st.plotly_chart(ecdf_fig)

    st.write("## Further comparisons")
    st.write("This heatmap is all about how riders compare to each other and not who is fastest. "
             "The higher the number the more similar the lap times were between the two riders.")
    st.write("Increasing the tolerance means more laps are considered in this analysis (therefore including some slow "
             "down laps) and widening the bins will mean more laps from a rider will overlap with laps from other "
             "riders.")
    st.write("A larger overlap leads to a higher similarity score due to the reduced granularity in the comparison. "
             "However, if the bin width is too small then it will decrease the ability to compare laps between "
             "riders.")
    st.write("Tyres are not yet taken into account, so a rider setting a number of fast laps on brand new soft tyres "
             "might show a lot of similarity to a faster rider using harder, more worn tyres.")
    # Using the fastest lap, bin width and a tolerance, reduce each riders' set of laps to a useful set
    # From that set, calculate the relative frequency and from there the Bhattacharyya coefficient
    lap_tolerance = st.number_input(
        "Set tolerance (%)", min_value=1.0, value=7.0, step=0.25,
        help="The laps to be considered will be within this percentage of the fastest lap.", key=2
    )
    bin_width = st.number_input(
        "Set bin width (seconds)", min_value=0.05, value=0.25, step=0.05,
        help="Laps are grouped together in bins, and this sets the width of each bin.", key=3
    )
    maximum_lap_time = fastest_lap * (1 + lap_tolerance/100)
    st.write(f"Slowest lap time considered will be {np.round(maximum_lap_time, 3)}")
    lowest_bin_limit = fastest_lap - 0.1
    highest_bin_limit = maximum_lap_time + 0.1
    num_of_bins = int(np.ceil(highest_bin_limit - lowest_bin_limit) / bin_width)
    st.write(f"Low bin = {lowest_bin_limit}, high bin = {highest_bin_limit}, num bins = {num_of_bins}")

    rider_relative_laps = data_wrangler.relative_freq_hist_calculation(
        df, lowest_bin_limit, highest_bin_limit, num_of_bins
    )

    rider_coeffs = data_wrangler.bhattacharyya_coefficients(rider_relative_laps)
    new_bc_df = data_wrangler.dataframe_from_dictionary(rider_coeffs)
    heatmap_fig = data_wrangler.plotly_heatmap(new_bc_df)
    st.plotly_chart(heatmap_fig)
# endregion


if __name__ == "__main__":
    data_wrangler = DataWrangler()

    sessions_names = [
        "GP: FP1, PR, FP2, WUP",
        "GP: P1, P2, FP, WUP",
        "GP: FP1, FP2, FP3, FP4, WUP",
        "GP: FP1, FP2, FP3, WUP",
        "2: P1, P2, P3",
        "2: FP1, FP2, FP3, WUP",
        "3: P1, P2, P3",
        "3: FP1, FP2, FP3, WUP"
    ]

    races = [
        "THA", "ARG", "AME", "QAT", "SPA", "FRA", "GBR", "ARA", "ITA", "NED", "GER", "AUT", "CZE", "HUN", "CAT", "RSM",
        "JPN", "INA", "AUS", "MAL", "POR", "VAL"
    ]
    categories = ["MotoGP", "Moto2", "Moto3"]
    with st.form('my_form'):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
        with col1:
            category = st.selectbox("Select class", categories, index=0)
        with col2:
            year = st.selectbox("Select year", range(2010, 2025), index=14)
        with col3:
            race = st.selectbox("Select race", races, index=5)
        with col4:
            session = st.selectbox(
                label="Select session",
                options=sessions_names,
                index=0,
                help="Pick the session names that the event you wish to analyse actually had."
            )
        # race_laps = st.checkbox("Include full race lap times (not sprint)", )
        race_laps = False
        submit = st.form_submit_button("Get sessions")

    if submit:
        data = data_wrangler.get_practice_sessions(category, year, race, session)
        if race_laps:
            race_df = data_wrangler.get_race_pace_for_practice_comparison(year, race)
            if race_df is not None:
                data = data_wrangler.vertically_concat_dataframes(data, race_df)
        st.session_state["current_analysis_df"] = deepcopy(data)
        visualise_data(data)
    elif st.session_state["current_analysis_df"] is not None:
        visualise_data(st.session_state["current_analysis_df"])
