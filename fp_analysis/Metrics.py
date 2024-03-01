import numpy as np
import matplotlib.pyplot as plt

from sklearn.neighbors import KernelDensity
# from sklearn.cluster import HDBSCAN
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

    # def cluster(self, X: np.ndarray):
    #     """Wrapper around Scikit-Learn HDBSCAN."""
    #     fig, axes = plt.subplots(3, 1, figsize=(10, 12))
    #     hdb = HDBSCAN()
    #     for idx, scale in enumerate([1, 0.5, 3]):
    #         hdb.fit(X * scale)
    #         self.plot(
    #             X * scale,
    #             hdb.labels_,
    #             hdb.probabilities_,
    #             ax=axes[idx],
    #             parameters={"scale": scale},
    #         )
    #     plt.show()

    @staticmethod
    def plot(X, labels, probabilities=None, parameters=None, ground_truth=False, ax=None):
        if ax is None:
            _, ax = plt.subplots(figsize=(10, 4))
        labels = labels if labels is not None else np.ones(X.shape[0])
        probabilities = probabilities if probabilities is not None else np.ones(X.shape[0])
        # Black removed and is used for noise instead.
        unique_labels = set(labels)
        colors = [plt.cm.Spectral(each) for each in np.linspace(0, 1, len(unique_labels))]
        # The probability of a point belonging to its labeled cluster determines
        # the size of its marker
        proba_map = {idx: probabilities[idx] for idx in range(len(labels))}
        for k, col in zip(unique_labels, colors):
            if k == -1:
                # Black used for noise.
                col = [0, 0, 0, 1]

            class_index = np.where(labels == k)[0]
            for ci in class_index:
                ax.plot(
                    X[ci, 0],
                    1.0,
                    "x" if k == -1 else "o",
                    markerfacecolor=tuple(col),
                    markeredgecolor="k",
                    markersize=4 if k == -1 else 1 + 5 * proba_map[ci],
                )
        n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        preamble = "True" if ground_truth else "Estimated"
        title = f"{preamble} number of clusters: {n_clusters_}"
        if parameters is not None:
            parameters_str = ", ".join(f"{k}={v}" for k, v in parameters.items())
            title += f" | {parameters_str}"
        ax.set_title(title)
        plt.tight_layout()
