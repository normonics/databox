"""
The databox module is a collection of (hopefully) useful data-related 
functions, including handling, analysis, and visualization
"""

import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd 
import scipy.stats as stats
# from pymongo import MongoClient()

#------------------------------------------------------------------------    

def pca(df):
    """Perform a principal components analysis on data in a DataFrame"""
    
    # normalize the data
    df_normalized = (df - df.mean()) / df.std()
    cov_matrix = np.cov(df_normalized, rowvar=0)
    eig_values, eig_vectors = np.linalg.eig(cov_matrix)
    
    # sort eig values and eigvectors
    eig_vectors = np.array(
                    [v[1] for v in sorted(
                        zip(eig_values, eig_vectors.transpose()), reverse=True
                            )]).transpose()
    eig_values = np.array(sorted(eig_values, reverse=True))

    # make eigenvectors primarily positive for easier interpretation
    for col in range(eig_vectors.shape[1]):
        if eig_vectors[:,col].sum() < 0:
            eig_vectors[:,col] = -eig_vectors[:,col]
    
    # project normalized points to prinipal components
    projected_points = np.dot(df_normalized.values, eig_vectors)
    
    return projected_points, eig_values, eig_vectors
  
#------------------------------------------------------------------------    

def plot_pca(projected_points, eig_values, eig_vectors, labels):
    """Function to plot the first two dimensions of a PCA analysis 
    along with its principal components and (normed) eigenvalues """

    fig, ax = plt.subplots(2,2, figsize=(10,10))

    ax[0,1].scatter(projected_points[:,0], projected_points[:,1])
    ax[0,1].set_xlabel('PC1')
    ax[0,1].set_ylabel('PC2')
    ax[0,1].set_title('PCA scatter')

    ax[1,1].bar(np.arange(eig_vectors.shape[0]) + 0.1, eig_vectors[:,0])
    ax[1,1].xaxis.set_ticklabels(labels)
    ax[1,1].set_title('PC1')

    ax[0,0].bar(np.arange(eig_vectors.shape[0]) + 0.1, eig_vectors[:,1])
    ax[0,0].xaxis.set_ticklabels(labels)
    ax[0,0].set_title('PC2')

    ax[1,0].plot(eig_values / eig_values.sum(), lw=2)
    ax[1,0].set_title('Eigenvalues (normalized)')

    plt.show()

#------------------------------------------------------------------------    

def mongo_to_df(collection, query={}, fields=None):
    """return a mongo query as a DataFrame"""
    records = collection.find(query, projection=fields)
    
    return pd.DataFrame(list(records))

#------------------------------------------------------------------------    

def cross_scatter(df_1, df_2):
    "Takes two DataFrames and builds the scatter plots of all their combinations"

    labels_1 = df_1.columns
    labels_2 = df_2.columns

    fig, ax = plt.subplots(len(labels_2), len(labels_1), figsize=(14,14))
    fig.subplots_adjust(wspace = 0.15, hspace=0.1)

    for i, label_1 in enumerate(labels_1):
        for j, label_2 in enumerate(labels_2):
            # scatter plot
            ax[j,i].scatter(df_1[label_1], df_2[label_2])
            
            # linear regression and plot
            slope, intercept, r_value, p_value, std_err = stats.linregress(
                df_1[label_1], df_2[label_2]
            )
            
            x = np.linspace(df_1[label_1].min(), df_1[label_1].max())
            ax[j,i].plot(x, slope*x+intercept, 'r', lw=3)
            
            
            if i != 0:
                ax[j,i].set_yticklabels([])
            if j != df_2.shape[0]-1:
                ax[j,i].set_xticklabels([])
            if i == 0:
                ax[j,i].set_ylabel(label_2)
            if j == df_2.shape[0]-1:
                ax[j,i].set_xlabel(label_1)
                for ticklabel in ax[j,i].get_xticklabels():
                    ticklabel.set_rotation('vertical')
