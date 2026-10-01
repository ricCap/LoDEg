import pandas as pd
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.preprocessing import StandardScaler, LabelBinarizer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import GridSearchCV
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn import cluster, mixture
from sklearn.neighbors import kneighbors_graph

import time
import warnings
import numpy as np


class DataFrameSelector(BaseEstimator, TransformerMixin):
    """Selector used in pipelines along with dataframes"""

    def __init__(self, attribute_names):
        self.attribute_names = attribute_names

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.attribute_names].values


_stats_whitelist = [
    'number_of_notes',
    'notes_over_session_duration',
    'number_of_jumps',
    'average_jumps_length',
    'total_jumps_length'
]

_num_attribs = _stats_whitelist
_cat_attribs = []


def migrateStatsToDataFrames(courseInfo: dict, ml_mem_opt: bool = True):
    """Migrate user stats to course level dataframe.

    Args:
        courseInfo (dict):  The dictionary that will be populated with the computed statistic;
        mem_opt (bool): If set, user level statistics are discarded during the migration to the dataframe.
    """
    series_dict = {}
    for user, userInfo in courseInfo['users'].items():
        # Populate a dataframe with the required statistics
        values = []
        keys = []
        for key, value in userInfo.items():
            if key in _stats_whitelist:
                keys.append(key)
                values.append(value)
        series = pd.Series(values, index=keys)
        series = series.T
        series_dict[user] = series
        # Delete userInfo stats if mem_opt is True
        if ml_mem_opt:
            for stat in _stats_whitelist:
                if stat in userInfo:
                    del userInfo[stat]
    courseInfo['stats_dframe'] = pd.DataFrame(series_dict).T


def executeUserClustering(courseInfo: dict):
    """This function executes the clustering algorithm on the course users

    Note:
        In order to allow this funtion to work, it has to be already populated with the stats_dframe (see migrateStatToDataFrate())

    Args:
        courseInfo (dict):  The dictionary that will be populated with the computed statistic;
    """

    if len(courseInfo['users']) < 2:
        return

    # Create pipeline for numerics values
    num_pipeline = Pipeline([
        ('selector', DataFrameSelector(_num_attribs)),  # Select numeric data
        ('imputer', SimpleImputer(strategy="median")),  # Fill missing data
        # Scale data (required by the clustering algorithms)
        ('std_scaler', StandardScaler())
    ])

    # Create pipeline for categorical attributes (not needed at the moment)
    cat_pipeline = Pipeline([
        ('selector', DataFrameSelector(_cat_attribs)),
        ('label_binarizer', LabelBinarizer()),
    ])

    # Create full pipeline
    full_pipeline = FeatureUnion(transformer_list=[
        ("num_pipeline", num_pipeline),
        ("cat_pipeline", cat_pipeline)
    ])

    # Get the data
    dataframe = courseInfo['stats_dframe']

    # Add noise for testing
    # noise = np.random.normal(100,10, dataframe.shape)
    # dataframe += noise

    # Run pipeline
    if _num_attribs != [] and _cat_attribs != []:
        X = full_pipeline.fit_transform(dataframe)
    elif _num_attribs != []:
        X = num_pipeline.fit_transform(dataframe)
    elif _cat_attribs != []:
        X = cat_pipeline.fit_transform(dataframe)

    # ============
    # Set up cluster parameters
    # ============
    params = {'quantile': .3,
              'eps': .3,  # This can be modified
              'damping': .9,
              'preference': -200,
              'n_neighbors': 1,
              'n_clusters': 3
              }

    # ============
    # Set up GridSearch parameters
    # ============

    param_grid = [{
        'n_neighbors': np.arange(2, 10),
        'n_clusters': np.arange(2, 5)
    }]

    # estimate bandwidth for mean shift
    #bandwidth = cluster.estimate_bandwidth(X, quantile=params['quantile'])
    # connectivity matrix for structured Ward
    connectivity = kneighbors_graph(
        X, n_neighbors=params['n_neighbors'], include_self=False)
    # make connectivity symmetric
    connectivity = 0.5 * (connectivity + connectivity.T)

    # ============
    # Create algorithms
    # ============
    #ms = cluster.MeanShift(bandwidth=bandwidth, bin_seeding=True)
    two_means = cluster.MiniBatchKMeans(n_clusters=params['n_clusters'])
    ward = cluster.AgglomerativeClustering(
        n_clusters=params['n_clusters'],
        linkage='ward', connectivity=connectivity)
    spectral = cluster.SpectralClustering(
        n_clusters=params['n_clusters'],
        eigen_solver='arpack',
        affinity="nearest_neighbors")
    dbscan = cluster.DBSCAN(eps=params['eps'])
    affinity_propagation = cluster.AffinityPropagation(
        damping=params['damping'], preference=params['preference'])
    average_linkage = cluster.AgglomerativeClustering(
        linkage="average", metric="cityblock",
        n_clusters=params['n_clusters'],
        connectivity=connectivity)
    birch = cluster.Birch(n_clusters=params['n_clusters'])
    gmm = mixture.GaussianMixture(
        n_components=params['n_clusters'], covariance_type='full')

    clustering_algorithms = (
        ('MiniBatchKMeans', two_means),
        ('AffinityPropagation', affinity_propagation),
        #('MeanShift', ms),
        #('SpectralClustering', spectral),
        ('Ward', ward),
        ('AgglomerativeClustering', average_linkage),
        ('DBSCAN', dbscan),
        ('Birch', birch),
        ('GaussianMixture', gmm)
    )

    # ============
    # Train and predict
    # ============

    algorithm_execution_time = {}
    clustering_results = {}

    for name, algorithm in clustering_algorithms:
        t0 = time.time()

        # catch warnings related to kneighbors_graph
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                message="the number of connected components of the " +
                "connectivity matrix is [0-9]{1,2}" +
                " > 1. Completing it to avoid stopping the tree early.",
                category=UserWarning)
            warnings.filterwarnings(
                "ignore",
                message="Graph is not fully connected, spectral embedding" +
                " may not work as expected.",
                category=UserWarning)
            algorithm.fit(X)

        # Get predictions (clusters)
        if hasattr(algorithm, 'labels_'):
            y_pred = algorithm.labels_.astype(int)
        else:
            y_pred = algorithm.predict(X)

        t1 = time.time()

        # Save clustering results
        clustering_results[name] = y_pred

        # Save execution time for debugging purposes
        algorithm_execution_time[name] = t1 - t0

    # ============
    # Save results
    # ============

    courseInfo['clusters'] = {
        'clustering_results': clustering_results,
        'execution_time': algorithm_execution_time
    }
