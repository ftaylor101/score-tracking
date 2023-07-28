import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from scipy import stats

from typing import List
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
if "current_analysis_df" not in st.session_state:
    st.session_state["current_analysis_df"] = None
if "original_df" not in st.session_state:
    st.session_state["original_df"] = None
# endregion

# region Introduction to page
st.markdown("# Free Practice Analysis")
st.write("## :chart_with_upwards_trend: Plot lots of things! :chart_with_downwards_trend:")
st.write("This page is to analyse MotoGP practice sessions.")
st.write("Choose a race weekend, choose the sessions to analyse and the year.")
st.write("**This page is still under construction and so may change at any moment**")
st.write("I am still figuring out what is useful and what is not, and how best to incorporate tyre compound and life "
         "into the analysis.")
# endregion


# region helper functions
def melt_df(df_to_melt: pd.DataFrame, new_columns: List[str]) -> pd.DataFrame:
    """Helper function to melt a wide dataframe into a long dataframe."""
    melted_df = df_to_melt.melt().dropna()
    melted_df.columns = new_columns
    return melted_df
# endregion


# region Analysis
def analyse_dataframe(full_df: pd.DataFrame):
    st.session_state["in_current_analysis_session"] = True

    # remove any short laps where riders take a shortcut to the pits or slow/cool down laps
    upper_tol = st.number_input(
        "Select maximum lap time",
        min_value=full_df.median().median(),
        max_value=full_df.median().median() + 50.0,
        value=full_df.median().median() + 1.0,
        step=0.001,
        format="%.3f")
    min_lap_time_allowed = full_df.median().median() * 0.9  # fastest lap is assumed to be only up to 10% faster
    max_lap_time_allowed = upper_tol  # slowest lap used in analysis is set by user

    # make a new filtered dataframe and work with that
    df = full_df.mask(full_df < min_lap_time_allowed)
    df.mask(df > max_lap_time_allowed, inplace=True)

    # get fastest lap for relative comparison purposes
    fastest_lap = df.min().min()
    fastest_rider = df.min().idxmin()
    st.write(f"Fastest lap was {fastest_lap} by {fastest_rider}")

    # sort the dataframe by median, from lowest to highest
    med = df.median()
    med = med.sort_values()
    df = df[med.index]
    riders = df.columns

    show_data = st.checkbox("Show data")
    if show_data:
        st.dataframe(df)  # show data

    with st.expander("See all rider summary plots"):
        rider_summary_melt = melt_df(df, ["Riders", "LapTimes"])

        plotly_strip_summary_fig = px.strip(rider_summary_melt, x="LapTimes", y="Riders", color="Riders")
        st.plotly_chart(plotly_strip_summary_fig)

        plotly_box_summary_fig = px.box(df, y=df.columns, hover_data=[df.index])
        st.plotly_chart(plotly_box_summary_fig)

    with st.form("lap_time_picker"):
        # times = st.slider(
        #     "Select lower and upper lap times (this does nothing!)", 70.0, 150.0, (100.0, 125.0), step=0.5
        # )
        selected_riders = st.multiselect(
            "Pick riders to compare or leave blank for all (but really just select a couple)", riders)
        times_picked = st.form_submit_button(
            label="Plot lap times"
        )

    if times_picked:
        if len(selected_riders) > 0:
            rider_laps = df[selected_riders]
        else:
            rider_laps = df
            selected_riders = df.columns

        # plotting the PDF of the lap times
        hist_data = list()
        for rider in selected_riders:
            hist_data.append(rider_laps[rider].dropna().values)
        pdf_fig = ff.create_distplot(hist_data, selected_riders, show_hist=False)
        pdf_fig.update_layout(title='Probability Density Function')
        st.plotly_chart(pdf_fig)

        rider_laps_melt = melt_df(rider_laps, ["Riders", "LapTimes"])

        plotly_strip_fig = px.strip(rider_laps_melt, x="LapTimes", y="Riders", color="Riders")
        st.plotly_chart(plotly_strip_fig)

        filtered_df = df[selected_riders]
        plotly_box_fig = px.box(filtered_df, y=filtered_df.columns, hover_data=[filtered_df.index])
        st.plotly_chart(plotly_box_fig)

        violin_fig = go.Figure()
        for rider in selected_riders:
            violin_fig.add_trace(go.Violin(x=rider_laps_melt["Riders"][rider_laps_melt["Riders"] == rider],
                                           y=rider_laps_melt["LapTimes"][rider_laps_melt["Riders"] == rider],
                                           name=rider,
                                           box_visible=True,
                                           meanline_visible=True,
                                           points="all"))
        st.plotly_chart(violin_fig)

        # plot empirical cumulative distribution functions for each selected rider
        ecdf_fig = px.ecdf(rider_laps, x=selected_riders)
        st.plotly_chart(ecdf_fig)

    # with st.form("Comparison analysis"):
    #     rider_metrics_melt = melt_df(df, ["Riders", "LapTimes"])
    #     two_selected_riders = st.multiselect("Select only 2 riders", riders)
    #
    #     calculate = st.form_submit_button("Calculate metrics!")
    #
    #     if calculate:
    #         rider_a = two_selected_riders[0]
    #         rider_b = two_selected_riders[1]
    #
    #         rider_a_laps = rider_metrics_melt[rider_metrics_melt["Riders"] == rider_a]["LapTimes"]
    #         rider_b_laps = rider_metrics_melt[rider_metrics_melt["Riders"] == rider_b]["LapTimes"]
    #
    #         rider_a_kde = metric_calculator.calculate_kde(np.array(rider_a_laps))
    #         rider_b_kde = metric_calculator.calculate_kde(np.array(rider_b_laps))
    #
    #         rider_a_samples = metric_calculator.sample(rider_a_kde, 50)
    #         rider_b_samples = metric_calculator.sample(rider_b_kde, 50)
    #
    #         kl_div = metric_calculator.calculate_kl_divergence(
    #             p=rider_a_samples,
    #             q=rider_b_samples
    #         )
    #
    #         st.write(f"The KL Divergence is {kl_div}")

    st.write("## Further comparisons")
    st.write("This heatmap is all about how riders compare to each other and not who is fastest. "
             "The higher the number the more similar the lap times were between the two riders.")
    st.write("Increasing the tolerance means more laps are considered in this analysis (therefore including some slow "
             "down laps) and widening the bins will mean more laps from a rider will overlap with laps from other "
             "riders.")
    st.write("A larger overlap leads to a higher similarity score due to the reduced granularity in the comparison. "
             "However, if the bin width is too small then it will decrease the ability to compare laps between "
             "riders.")
    # Using the fastest lap, bin width and a tolerance, reduce each riders' set of laps to a useful set
    # From that set, calculate the relative frequency and from there the Bhattacharyya coefficient
    lap_tolerance = st.number_input("Set tolerance (%)", min_value=1.0, value=7.0, step=0.25,
                                    help="The laps to be considered will be within this percentage of the fastest lap.")
    bin_width = st.number_input("Set bin width (seconds)", min_value=0.05, value=0.25, step=0.05,
                                help="Laps are grouped together in bins, and this sets the width of each bin.")
    maximum_lap_time = fastest_lap * (1 + lap_tolerance/100)
    st.write(f"Slowest lap time considered will be {np.round(maximum_lap_time, 3)}")
    rider_relative_laps = dict()
    lowest_bin_limit = fastest_lap - 0.1
    highest_bin_limit = maximum_lap_time + 0.1
    num_of_bins = int(np.ceil(highest_bin_limit - lowest_bin_limit) / bin_width)
    st.write(f"Low bin = {lowest_bin_limit}, high bin = {highest_bin_limit}, num bins = {num_of_bins}")
    for rider in df.columns:
        rider_lap_times = df[rider].dropna().values
        # todo move stats.relfreq to metrics class
        res = stats.relfreq(
            a=rider_lap_times,
            defaultreallimits=(lowest_bin_limit, highest_bin_limit),
            numbins=num_of_bins
        )
        rider_relative_laps[rider] = res
    # st.write(rider_relative_laps)

    rider_coeffs = defaultdict(list)
    for rider_a, ra_rel_freqs in rider_relative_laps.items():
        for rider_b, rb_rel_freqs in rider_relative_laps.items():
            if rider_a == rider_b:
                b_c = 0
            else:
                b_c = metric_calculator.calculate_bhattacharyya_coefficient(
                    p=ra_rel_freqs[0],
                    q=rb_rel_freqs[0]
                )
            rider_coeffs[rider_a].append(b_c)
            # st.write(f"{rider_a} and {rider_b} have coeff {b_c}")
    # st.write(rider_coeffs)

    bc_df = pd.DataFrame.from_dict(rider_coeffs, orient='index').T
    idxs = list(bc_df.columns)
    bc_df["Rider"] = idxs
    new_bc_df = bc_df.set_index("Rider")
    heatmap_fig = px.imshow(new_bc_df, color_continuous_scale='RdBu_r')
    st.plotly_chart(heatmap_fig)

    st.write("Anderson-Darling test")
    dists = ['norm', 'expon', 'logistic', 'gumbel', 'gumbel_l', 'gumbel_r', 'extreme1', 'weibull_min']
    with st.form("stats_section"):
        selected_rider = st.selectbox("Pick a rider", riders)
        distribution = st.selectbox("Pick a distribution", dists)
        calc_stat = st.form_submit_button(
            label="Calculate the AD statistic"
        )
    if calc_stat:
        data = df[selected_rider].dropna()
        # st.write(data)
        st.write(f"Distribution = {distribution}")
        res = stats.anderson(x=data, dist=distribution)
        st.write(f"statistic = {res.statistic}")
        st.write(f"critical values = {res.critical_values}")
        st.write(f"significance levels = {res.significance_level}")
        result = res.statistic - res.critical_values[-1]
        if result < 0:
            st.write(f"Accept null hypothesis that the data came from a {distribution} distribution")
        else:
            st.write(f"Reject the null hypothesis")

        ad_fig = plt.figure()
        ad_ax = res.fit_result.plot(plot_type='hist')
        ad_fig.add_axes(ad_ax)
        st.pyplot(ad_fig)

        gompertz = stats.gompertz
        rv = gompertz.fit(data)
        st.write(f"gompertz params = {rv}")


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
        col1, col2, col3 = st.columns(3)
        with col1:
            year = st.selectbox("Select year", range(2010, 2024), index=13)
        with col2:
            race = st.selectbox("Select race", races, index=5)
        with col3:
            session = st.selectbox(
                label="Select session",
                options=["Old style", "New style"],
                index=1,
                help="New style is for P1, P2 and FP, Old style is for FP1, FP2 etc."
            )
        submit = st.form_submit_button("Get sessions")

    if submit:
        if st.session_state["year"] == year and st.session_state["race"] == race and \
                st.session_state["sessions"] == session:
            analyse_dataframe(st.session_state["current_analysis_df"])
        with st.spinner("Please wait while files are retrieved and parsed..."):
            exists = pdfs.check_sessions_exist(year, race, session)

        if exists:
            all_session_file_names = pdfs.retrieve_practice_files(year, race, session)
            st.success("All available sessions downloaded")
            st.session_state["year"] = year
            st.session_state["race"] = race
            st.session_state["sessions"] = session
            final_df = pd.DataFrame()
            for file in all_session_file_names:
                tmp_df = parser.parse_pdf(file, delete_if_less_than_three=True)
                final_df = pd.concat([final_df, tmp_df], ignore_index=True)
            st.session_state["current_analysis_df"] = final_df
            st.session_state["original_df"] = final_df
        elif not exists:
            st.write("Sessions do not exist")
        else:
            st.write("Something else happened")

    if st.session_state["current_analysis_df"] is not None:
        analyse_dataframe(st.session_state["current_analysis_df"])
    else:
        st.warning("No sessions to analyse")

