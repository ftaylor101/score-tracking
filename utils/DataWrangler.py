import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff
from copy import deepcopy
from typing import List, Union, Tuple, Any, Dict
from collections import defaultdict

from utils.Parser import PdfParser
from utils.Retriever import PdfRetriever
from fp_analysis.Metrics import MetricsCalculator

import matplotlib as mpl
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

from sklearn.mixture import BayesianGaussianMixture
from sklearn.datasets import make_blobs

class DataWrangler:
    """
    A class to manage all aspects of the data to be presented, from retrieving, parsing, combining and preparing.
    """
    def __init__(self):
        self.pdf_retriever = PdfRetriever()
        self.pdf_parser = PdfParser()
        self.metrics_calculator = MetricsCalculator()

    def get_race(self, category: str, year: int, race: str, session: str) -> Union[pd.DataFrame, None]:
        """
        A method to check if a race exists, retrieves it and parses the file to extract all lap times.

        :param category: The racing class for which to retrieve the race analysis.
        :param year: The year of the desired race.
        :param race: The race 3-letter code.
        :param session: The race type, either RAC or SPR.
        :return: The dataframe with all lap times from all riders.
        """
        exist = self.pdf_retriever.check_sessions_exist(category, year, race, session)
        out = None
        if exist:
            race_file_name = self.pdf_retriever.retrieve_race_files(category, year, race, session, "analysis")
            if race_file_name:
                out = self.pdf_parser.parse_pdf(race_file_name, delete_if_less_than_three=False, is_race=True)
        return out

    def get_practice_sessions(self, category: str, year: int, race: str, session: str) -> Union[pd.DataFrame, None]:
        """
        A method to check which sessions exist, retrieves them and parses the files to extract all lap times.

        :param category: The racing class for which to retrieve the sessions.
        :param year: The year of the desired sessions.
        :param race: The race of the desired sessions.
        :param session: The format of the desired sessions.
        :return: The dataframe with all lap times for all riders for all practice sessions.
        """
        exists = self.pdf_retriever.check_sessions_exist(category, year, race, session)
        out = None
        if exists:
            all_session_file_names = self.pdf_retriever.retrieve_practice_files(category, year, race, session)
            final_df = pd.DataFrame()
            for file in all_session_file_names:
                tmp_df = self.pdf_parser.parse_pdf(file, delete_if_less_than_three=True, is_race=False)
                final_df = pd.concat([final_df, tmp_df], ignore_index=True)
            out = final_df
        return out

    def get_race_pace_for_practice_comparison(self, year: int, race: str) -> Union[pd.DataFrame, None]:
        """
        A method to get the full Sunday race lap times to overlay on practice data for MotoGP only.

        :param year: The year of the desired sessions.
        :param race: The race of the desired sessions.
        :return:
        """
        exists = self.pdf_retriever.check_sessions_exist("MotoGP", year, race, "RAC")
        out = None
        if exists:
            race_session_file = self.pdf_retriever.retrieve_race_files(year, race, "MotoGP Race", "analysis")
            race_df = self.pdf_parser.parse_pdf(race_session_file, delete_if_less_than_three=False, is_race=True)
            race_df.replace("Analysis", "RAC", inplace=True)
            out = race_df
        return out

    @staticmethod
    def vertically_concat_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        """A helper method to concatenate two dataframes across rows (stacking vertically)."""
        return pd.concat([df1, df2], axis="rows")

    @staticmethod
    def horizontally_concat_dataframes(df1, df2):
        """A helper method to concatenate two dataframes across columns (adding horizontally)."""
        return pd.concat([df1, df2], axis="columns")

    @staticmethod
    def copy_df(df: pd.DataFrame):
        """A wrapper around deepcopy. For debug purposes."""
        return deepcopy(df)

    @staticmethod
    def drop_column(df: pd.DataFrame, col: str) -> pd.DataFrame:
        """A wrapper around the pandas code to drop a column. For debug purposes."""
        return df.drop(labels=[col], axis="columns")

    @staticmethod
    def median_of_all_columns(df: pd.DataFrame) -> float:
        """A helper method to find the single median of a dataframe."""
        return df.median().median()

    @staticmethod
    def minimum_of_all_columns(df: pd.DataFrame) -> Tuple[float, Any]:
        """A helper method to find the single minimum of a dataframe."""
        return df.min().min(), df.min().idxmin()

    @staticmethod
    def mask_df(df: pd.DataFrame, min_value: float, max_value: float) -> pd.DataFrame:
        """A helper method to mask values above and below the min and max values provided."""
        return df.mask((df < min_value) | (df > max_value))

    @staticmethod
    def sort_by_median(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Index]:
        """A helper method to sort a dataframe, ordering the columns from left to right in ascending median value."""
        med = df.median()
        med = med.sort_values()
        df = df[med.index]
        col_names = df.columns
        return df, col_names

    @staticmethod
    def melt_on_session(df: pd.DataFrame) -> pd.DataFrame:
        """A helper method to melt a dataframe."""
        return df.melt(id_vars="Session", var_name="Riders", value_name="LapTimes").dropna()

    @staticmethod
    def melt_on_lap(df: pd.DataFrame, values: List) -> pd.DataFrame:
        """A helper method to melt a dataframe around the lap variable (represented by index)."""
        return df.melt(id_vars=["index"], value_vars=values)

    @staticmethod
    def filter_on_columns(df: pd.DataFrame, column_names: List[str]) -> pd.DataFrame:
        """A helper method to filter a dataframe on column names."""
        return df[column_names]

    @staticmethod
    def get_column_names(df: pd.DataFrame) -> pd.Index:
        """A helper method to return the column names of a dataframe."""
        return df.columns

    @staticmethod
    def rename_columns(df: pd.DataFrame, new_names: Dict) -> pd.DataFrame:
        """A helper method to rename the columns of dataframe."""
        return df.rename(columns=new_names)

    @staticmethod
    def dataframe_from_dictionary(data_dict: Dict) -> pd.DataFrame:
        """A helper method to convert a dictionary to a dataframe."""
        tmp_df = pd.DataFrame.from_dict(data_dict, orient="index").T
        idxs = list(tmp_df.columns)
        tmp_df["Rider"] = idxs
        new_tmp_df = tmp_df.set_index("Rider")
        return new_tmp_df

    @staticmethod
    def make_histogram_data(df: pd.DataFrame, column_names: List[str]) -> List[Union[np.ndarray, List]]:
        """A helper method to extract the values from each named column, drop NaNs and append the values to a list."""
        out_list = list()
        for col in column_names:
            out_list.append(df[col].dropna().values)
        return out_list

    @staticmethod
    def values_of_first_column(df: pd.DataFrame) -> pd.Series:
        """A helper method to get the values of the first column."""
        return df[df.columns[0]]

    @staticmethod
    def gap_between_column_and_dataframe(df: pd.DataFrame, column: pd.Series) -> pd.DataFrame:
        """A helper method to find the difference between a series and each column of a dataframe."""
        out_df = pd.DataFrame()
        for col in df.columns:
            out_df[col] = column - df[col]
        cumulative_out_df = out_df.cumsum()
        cumulative_out_df.reset_index(inplace=True)
        return cumulative_out_df

    @staticmethod
    def plotly_strip_chart(df: pd.DataFrame, x_name: str, y_name: str, colour: str):
        """A helper method to create a plotly strip chart and order the y axis."""
        fig = px.strip(df, x=x_name, y=y_name, color=colour)
        y_axes_order = np.flip(df["Riders"].unique())
        fig.update_yaxes(categoryorder="array", categoryarray=y_axes_order)
        return fig

    @staticmethod
    def plotly_box_plot(df: pd.DataFrame):
        """A helper method to create box plots. Data in the columns is set as the y-axis value."""
        return px.box(df, y=df.columns, hover_data=[df.index])

    @staticmethod
    def plotly_distribution_plot(data: List[Union[np.ndarray, List]], labels: List[str], show_histogram: bool):
        """A helper method to create a histogram."""
        fig = ff.create_distplot(data, labels, show_hist=show_histogram)
        fig.update_layout(title='Probability Density Function')
        return fig

    @staticmethod
    def plotly_standard_violin(df: pd.DataFrame, y_values: List[float]):
        """A helper method to make a violin plot for all entries in the dataframe."""
        return px.violin(df, y=y_values, box=True, points="all")

    @staticmethod
    def plotly_stacked_violin_figure(df: pd.DataFrame, labels: List[str]):
        """A helper method to make a stacked violin plot for the given labels."""
        fig = go.Figure()
        for label in labels:
            fig.add_trace(go.Violin(x=df["Riders"][df["Riders"] == label],
                                    y=df["LapTimes"][df["Riders"] == label],
                                    name=label,
                                    box_visible=True,
                                    meanline_visible=True,
                                    points="all"
                                    ))
        return fig

    @staticmethod
    def plotly_heatmap(df:pd.DataFrame):
        """A helper method to display a dataframe as a heatmap."""
        return px.imshow(df, color_continuous_scale='RdBu_r')

    @staticmethod
    def plotly_ecdf_plot(df: pd.DataFrame, x_values: List[str]):
        """A helper method to plot an empirical cumulative distribution function for the given x values."""
        return px.ecdf(df, x=x_values)

    @staticmethod
    def plotly_line_chart(df: pd.DataFrame, x_values: str, y_values: str, colour: str):
        """A helper method to create a plotly line chart with markers."""
        return px.line(df, x=x_values, y=y_values, color=colour, markers=True)

    def relative_freq_hist_calculation(self, df: pd.DataFrame, low_bin: float, high_bin: float, bin_num: int) -> Dict:
        """A helper method to find the relative frequency of each riders' laps."""
        out_dict = dict()
        for col in df.columns:
            values = df[col].dropna().values
            res = self.metrics_calculator.relative_frequency_histogram(
                arr=values, bin_bounds=(low_bin, high_bin), num_of_bins=bin_num
            )
            out_dict[col] = res
        return out_dict

    def bhattacharyya_coefficients(self, data: Dict) -> Dict:
        """A helper method to calculate Bhattacharyya coefficients."""
        rider_coeffs = defaultdict(list)
        for rider_a, ra_rel_freqs in data.items():
            for rider_b, rb_rel_freqs in data.items():
                if rider_a == rider_b:
                    b_c = 0
                else:
                    b_c = self.metrics_calculator.calculate_bhattacharyya_coefficient(
                        p=ra_rel_freqs[0],
                        q=rb_rel_freqs[0]
                    )
                rider_coeffs[rider_a].append(b_c)
        return rider_coeffs


if __name__ == "__main__":
    dw = DataWrangler()
    year = 2023
    race = "QAT"
    session = "Latest style"
    practice_df = dw.get_practice_sessions(year, race, session)
    race_df = dw.get_race_pace_for_practice_comparison(year, race)
    combined_df = dw.vertically_concat_dataframes(practice_df, race_df)

    sess_df = dw.copy_df(combined_df["Session"])
    data_df = dw.drop_column(combined_df, "Session")

    med_value = dw.median_of_all_columns(data_df)
    min_lap = med_value * 0.9
    max_lap = med_value * 1.3
    masked_df = dw.mask_df(data_df, min_lap, max_lap)

    fastest_lap, fastest_rider = dw.minimum_of_all_columns(masked_df)
    print(f"Fastest lap was {fastest_lap} by {fastest_rider}")

    sorted_df, riders = dw.sort_by_median(masked_df)

    with_sess_df = dw.horizontally_concat_dataframes(sorted_df, sess_df)

    melt_with_sess_df = dw.melt_on_session(with_sess_df)

    centers = [[1, 1], [-1, -1], [1.5, -1.5]]
    X, labels_true = make_blobs(
        n_samples=750, centers=centers, cluster_std=[0.4, 0.1, 0.75], random_state=0
    )
    d = np.expand_dims(melt_with_sess_df["LapTimes"].values, axis=1)
    dw.metrics_calculator.cluster(d)
    b = 2
    #
    # plotly_strip_fig = dw.plotly_strip_chart(melt_with_sess_df, "LapTimes", "Riders", "Session")
    # # plotly_strip_fig.show()
    #
    # plotly_box_fig = dw.plotly_box_plot(sorted_df)
    # # plotly_box_fig.show()
    #
    # selected_riders = dw.get_column_names(sorted_df)
    # hist_data = dw.make_histogram_data(sorted_df, selected_riders)
    # pdf_fig = dw.plotly_distribution_plot(hist_data, selected_riders, False)
    # # pdf_fig.show()
    #
    # low_bin = 96.6
    # high_bin = 103.577
    # num_bin = 28
    #
    # rrl = dw.relative_freq_hist_calculation(sorted_df, low_bin, high_bin, num_bin)
    # rc = dw.bhattacharyya_coefficients(rrl)
    # new_df = dw.dataframe_from_dictionary(rc)
    # heatmap = dw.plotly_heatmap(new_df)
    # heatmap.show()

    # year = 2023
    # race = "INA"
    # category = "Moto2"
    # raw_df = dw.get_race(year, race, category)
    # data_df = dw.drop_column(raw_df, "Session")
    #
    # winner = dw.values_of_first_column(data_df)
    # gap_df = dw.gap_between_column_and_dataframe(data_df, winner)
    # melt_gap_df = dw.melt_on_lap(gap_df, list(dw.get_column_names(data_df)))
    # melt_gap_df = dw.rename_columns(melt_gap_df, {"index": "Lap", "variable": "Rider", "value": "Gap"})
    # line_fig = dw.plotly_line_chart(melt_gap_df, "Lap", "Gap", "Rider")
    # line_fig.show()
    #
    # violin_fig = dw.plotly_standard_violin(data_df, list(dw.get_column_names(data_df)))
    # violin_fig.show()
    #
    # box_fig = dw.plotly_box_plot(data_df)
    # box_fig.show()

    a = 1

