import os
import nibabel as nib
import numpy as np
from nilearn import datasets, plotting
from nilearn.connectome import ConnectivityMeasure
import matplotlib.pyplot as plt

def process_brain_data(filepath):
    """
    Process brain imaging data and return connectivity matrix and connectome visualization
    """
    # Load the NIfTI file
    img = nib.load(filepath)
    data = img.get_fdata()
    
    # Extract time series from regions of interest
    # For this example, we'll use a simple approach
    # In practice, you should use your trained model here
    n_regions = 100  # Example number of regions
    n_timepoints = data.shape[-1]
    
    # Reshape data to get time series for each voxel
    reshaped_data = data.reshape(-1, n_timepoints)
    
    # Select random regions (in practice, use your model's regions)
    selected_regions = np.random.choice(reshaped_data.shape[0], n_regions, replace=False)
    time_series = reshaped_data[selected_regions]
    
    # Compute correlation matrix
    correlation_measure = ConnectivityMeasure(kind='correlation')
    connectivity_matrix = correlation_measure.fit_transform([time_series])[0]
    
    # Generate connectome visualization
    output_dir = 'static'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create a simple connectome plot
    plt.figure(figsize=(10, 10))
    plt.imshow(connectivity_matrix, cmap='coolwarm')
    plt.colorbar()
    plt.title('Brain Connectivity Matrix')
    
    # Save the plot
    connectome_path = os.path.join(output_dir, 'connectome.png')
    plt.savefig(connectome_path)
    plt.close()
    
    return connectivity_matrix, connectome_path 