"""the databox module is a collection of (hopefully) useful data-related 
functions, including handling, analysis, and visualization
"""

import matplotlib.pyplot as plt 
import numpy as np 
import pandas as pd 

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

def plot_pca(projected_points, eig_values, eig_vectors, labels):
    """Function to plot the first two dimensions of a PCA analysis along with its principal components and (normed) eigenvalues """
    fig, ax = plt.subplots(2,2, figsize=(10,10))

    ax[0,1].scatter(projected_points[:,0], projected_points[:,1])
    ax[0,1].set_xlabel('PC1')
    ax[0,1].set_ylabel('PC2')
    ax[0,1].set_title('PCA of individuals based on their std')

    ax[1,1].bar(range(eig_vectors.shape[0]), eig_vectors[:,0])
    ax[1,1].xaxis.set_ticklabels(labels)

    ax[0,0].bar(range(eig_vectors.shape[0]), eig_vectors[:,1])
    ax[0,0].xaxis.set_ticklabels(labels)

    ax[1,0].plot(eig_values / eig_values.sum())

plt.show()