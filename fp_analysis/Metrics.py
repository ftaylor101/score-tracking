import numpy as np

from sklearn.neighbors import KernelDensity
from scipy.special import kl_div, softmax
from scipy import stats
from typing import Tuple


class MetricsCalculator:
    """
    A class to calculate various metrics and distances between samples and distributions.
    """
    def __init__(self):
        pass

    @staticmethod
    def calculate_bhattacharyya_coefficient(p: np.ndarray, q: np.ndarray) -> float:
        """
        This finds the coefficient for 2 distributions.
        - Using the relative frequency of each bin, multiply the rel. freq. of each corresponding bin from the two
        distributions
        - Then sqrt and sum up the results

        - https://www.eecs.yorku.ca/research/techreports/2015/EECS-2015-02.pdf

        :param p: The relative frequency of the values from distribution P
        :param q: The relative frequency of the values from distribution Q
        :return: The Bhattacharyya coefficient
        """
        if len(p) != len(q):
            raise ValueError("p and q must be of same size")
        assert isinstance(p, np.ndarray)
        assert isinstance(q, np.ndarray)

        return np.sum(np.sqrt(p*q))

    @staticmethod
    def calculate_kde(p: np.ndarray, bandwidth: float = 0.5, kernel: str = "gaussian") -> object:
        shaped_p = np.reshape(p, (len(p), 1))
        kde = KernelDensity(kernel=kernel, bandwidth=bandwidth).fit(shaped_p)
        return kde

    @staticmethod
    def sample(kde: object, num_sample: int) -> np.ndarray:
        kde: KernelDensity
        out = kde.sample(num_sample)
        return out

    @staticmethod
    def calculate_kl_divergence(p: np.ndarray, q: np.ndarray) -> float:
        if len(p) != len(q):
            raise ValueError("p and q must be of same size")
        assert isinstance(p, np.ndarray)
        assert isinstance(q, np.ndarray)

        return sum(kl_div(p, q))

    @staticmethod
    def relative_frequency_histogram(arr: np.ndarray, bin_bounds: Tuple, num_of_bins: int):
        """
        Wrapper around stats.relfreq to create a relative frequency histogram for a given dataset and the bins.

        :param arr: The dataset for which to find the frequency.
        :param bin_bounds: The lower and upper bound of the bins.
        :param num_of_bins: The number of bins.
        :return: A stats.relfreq object containing frequency data for each bin.
        """
        return stats.relfreq(
            a=arr,
            defaultreallimits=bin_bounds,
            numbins=num_of_bins
        )

