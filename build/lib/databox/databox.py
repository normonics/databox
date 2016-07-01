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

def mongo_to_df(collection, query={}, fields=None):
    """return a mongo query as a DataFrame
    """

    records = collection.find(query, projection=fields)
    
    return pd.DataFrame(list(records))

#------------------------------------------------------------------------    

def pca(df):
    """Perform a principal components analysis on data in a DataFrame
    """
    
    # normalize the data
    df_normalized = (df - df.mean()) / df.std()
    corr_matrix = np.corrcoef(df_normalized, rowvar=0)
    eig_values, eig_vectors = np.linalg.eig(corr_matrix)
    
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

def plot_pca(projected_points, eig_values, eig_vectors, labels=None):
    """Function to plot the first two dimensions of a PCA analysis 
    along with its principal components and (normed) eigenvalues 
    """

    if not labels:
        labels = range(len(eig_values))

    fig, ax = plt.subplots(2,2, figsize=(10,10))

    ax[0,1].scatter(projected_points[:,0], projected_points[:,1])
    ax[0,1].set_xlabel('PC1')
    ax[0,1].set_ylabel('PC2')
    ax[0,1].set_title('PCA scatter')

    ax[1,1].bar(
        np.arange(eig_vectors.shape[0]) + 0.1, 
        eig_vectors[:,0] * np.sqrt(eig_values[0]))
    ax[1,1].xaxis.set_ticks(np.arange(len(labels)) + 0.5)
    ax[1,1].xaxis.set_ticklabels(labels)
    ax[1,1].set_title('PC1 loadings')

    ax[0,0].bar(
        np.arange(eig_vectors.shape[0]) + 0.1, 
        eig_vectors[:,1] * np.sqrt(eig_values[1]))
    ax[0,0].xaxis.set_ticks(np.arange(len(labels)) + 0.5)
    ax[0,0].xaxis.set_ticklabels(labels)
    ax[0,0].set_title('PC2 loadings')

    ax[1,0].plot(eig_values / eig_values.sum(), lw=2)
    ax[1,0].set_title('Eigenvalues (normalized)')

    plt.show()

#------------------------------------------------------------------------       

def mc_pca(df, N=99):
    """Take a dataframe and establish the significance of the largest eigenvalue 
    via a monte carlo approach
    """

    _, observed_eig_values, _ = pca(df) 

    mc_eig_values = np.zeros((N, df.shape[1]))
    for n in xrange(N):
        df_shuffled = shuffle_df(df)
        _, eig_values, _ = pca(df_shuffled)
        mc_eig_values[n,:] = eig_values

    #convert eigenvalus array to dataframe for useful functions 
    mc_eig_values = pd.DataFrame(data=mc_eig_values)

    # build summary dataframe
    df_summary = pd.DataFrame()
    df_summary['Observed Eigenvalue'] = observed_eig_values
    df_summary['Mean'] = mc_eig_values.mean()
    df_summary['Std'] = mc_eig_values.std()
    df_summary['Median'] = mc_eig_values.median()
    df_summary['Quantile 0.75'] = mc_eig_values.quantile(0.75)
    df_summary['Quantile 0.90'] = mc_eig_values.quantile(0.90)
    df_summary['Quantile 0.95'] = mc_eig_values.quantile(0.95)
    df_summary['Quantile 0.99'] = mc_eig_values.quantile(0.99)
    df_summary['P-value'] = (
        ((mc_eig_values>=observed_eig_values).sum().values.astype('float') + 1)
        / (N+1))
        
    return df_summary

#------------------------------------------------------------------------    

def cross_scatter(df_1, df_2, lin_regress=True):
    """Takes two DataFrames and builds the scatter plots of all their combinations
    """

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
            if j != df_2.shape[1]-1:
                ax[j,i].set_xticklabels([])
            if i == 0:
                ax[j,i].set_ylabel(label_2)
            if j == df_2.shape[1]-1:
                ax[j,i].set_xlabel(label_1)
                for ticklabel in ax[j,i].get_xticklabels():
                    ticklabel.set_rotation('vertical')

    return fig, ax

#------------------------------------------------------------------------    

def shuffle_df(df):
    """Shuffles the values in each column of a DataFrame and returns the 
    shuffled frame. Useful for e.g. monte carlo analysis
    """

    df = df.copy()
    df.apply(np.random.shuffle, axis=0)

    return df 

#------------------------------------------------------------------------   

def color_scatter_by_df(x, y, df):
    """Produce a scatter plot colored by the values in each column 
    of a DataFrame
    """

    for column in df.columns:
        plt.figure()
        plt.scatter(x, y, c=df[column].values)
        plt.colorbar()
        plt.title(column)
        plt.show()
