import numpy as np
import nibabel as nib
from nilearn import datasets
from nilearn import image
from nilearn import regions
import pandas as pd
from typing import Tuple, Dict, Optional
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.stats import zscore
import nbformat
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class GCNConnectivity(nn.Module):
    def __init__(self, num_regions, num_features, hidden_dim=64):
        super(GCNConnectivity, self).__init__()
        self.conv1 = GCNConv(num_features, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, hidden_dim)
        self.fc = nn.Linear(hidden_dim, num_regions)

    def forward(self, x, edge_index):
        x = torch.relu(self.conv1(x, edge_index))
        x = torch.relu(self.conv2(x, edge_index))
        x = self.fc(x)
        x = torch.tanh(x)  # Map to [-1, 1]
        x = (x + x.transpose(0, 1)) / 2  # Symmetrize
        return x

class FunctionalConnectivityProcessor:
    def __init__(self, model_path: str):
        """
        Initialize the processor with the path to the model notebook.
        
        Args:
            model_path: Path to the .ipynb model file
        """
        # Load Harvard-Oxford subcortical atlas
        self.atlas = datasets.fetch_atlas_harvard_oxford('sub-maxprob-thr25-2mm')
        self.atlas_filename = self.atlas.maps
        self.labels = self.atlas.labels
        
        # Load model from notebook
        self.model = self.load_model(model_path)
        
    def load_model(self, model_path: str):
        """Load model from Jupyter notebook."""
        try:
            with open(model_path, 'r', encoding='utf-8') as f:
                notebook = nbformat.read(f, as_version=4)

            # Initialize model with dummy dimensions (will be updated during processing)
            model = GCNConnectivity(num_regions=1, num_features=1)
            
            # Look for model weights in the notebook
            for cell in notebook.cells:
                if cell.cell_type == 'code':
                    try:
                        # Skip cells with errors or empty outputs
                        if not cell.outputs:
                            continue
                            
                        # Look for state dict in the outputs
                        for output in cell.outputs:
                            if output.output_type == 'execute_result':
                                if 'state_dict' in str(output.data):
                                    logger.info("Found model weights in notebook output")
                                    # Extract the state dict from the output
                                    state_dict = output.data.get('text/plain', '')
                                    if state_dict:
                                        # Convert string representation to actual state dict
                                        state_dict = eval(state_dict)
                                        model.load_state_dict(state_dict)
                                        break
                    except Exception as cell_error:
                        logger.warning(f"Error processing cell: {str(cell_error)}")
                        continue
            
            model.eval()
            return model
            
        except Exception as e:
            logger.error(f"Error loading model from notebook: {str(e)}")
            # Fallback to untrained model
            return GCNConnectivity(num_regions=1, num_features=1)
        
    def load_nifti(self, file_path: str) -> nib.Nifti1Image:
        """Load a NIfTI file."""
        return nib.load(file_path)
    
    def extract_time_series(self, nifti_img: nib.Nifti1Image) -> np.ndarray:
        """Extract time series from each ROI."""
        # Resample atlas to match the input image
        resampled_atlas = image.resample_to_img(
            self.atlas_filename,
            nifti_img,
            interpolation='nearest'
        )
        
        # Extract time series for each ROI
        time_series = regions.img_to_signals_labels(
            nifti_img,
            resampled_atlas,
            background_label=0
        )
        
        # Normalize time series
        time_series = zscore(time_series[0], axis=1, ddof=1)
        time_series = np.nan_to_num(time_series, nan=0.0)
        
        return time_series
    
    def compute_connectivity_matrix(self, time_series: np.ndarray) -> np.ndarray:
        """
        Use the GCN model to compute the connectivity matrix.
        
        Args:
            time_series: numpy array of shape (n_regions, n_timepoints)
            
        Returns:
            numpy array of shape (n_regions, n_regions) containing the connectivity matrix
        """
        # Convert to torch tensor
        features = torch.tensor(time_series, dtype=torch.float)
        
        # Compute correlation-based adjacency for initial graph
        corr_matrix = np.corrcoef(time_series)
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        edge_index = np.where(np.abs(corr_matrix) > 0.3)  # threshold of 0.3
        edge_index = torch.tensor(np.array(edge_index), dtype=torch.long)
        
        # Update model dimensions
        num_regions = time_series.shape[0]
        num_features = time_series.shape[1]
        self.model = GCNConnectivity(num_regions=num_regions, num_features=num_features)
        
        # Generate connectivity matrix
        with torch.no_grad():
            connectivity_matrix = self.model(features, edge_index)
            connectivity_matrix = connectivity_matrix.numpy()
        
        return connectivity_matrix
    
    def process_nifti(self, nifti_file_path: str) -> Tuple[np.ndarray, list, Dict]:
        """
        Process a NIfTI file and return connectivity information.
        
        Args:
            nifti_file_path: Path to the NIfTI file
            
        Returns:
            Tuple containing:
            - connectivity_matrix: numpy array of shape (n_regions, n_regions)
            - region_names: list of region names
            - additional_metrics: dictionary of additional metrics
        """
        # Load the NIfTI file
        nifti_img = self.load_nifti(nifti_file_path)
        
        # Extract time series
        time_series = self.extract_time_series(nifti_img)
        
        # Compute connectivity matrix using the GCN model
        connectivity_matrix = self.compute_connectivity_matrix(time_series)
        
        # Generate heatmap visualization
        plt.figure(figsize=(10, 10))
        plt.imshow(connectivity_matrix, cmap='coolwarm')
        plt.colorbar()
        plt.title('Brain Connectivity Matrix')
        
        # Save the heatmap
        heatmap_path = os.path.join('uploads', 'connectome.png')
        plt.savefig(heatmap_path)
        plt.close()
        
        # Prepare additional metrics
        additional_metrics = {
            'mean_connectivity': float(np.mean(connectivity_matrix)),
            'std_connectivity': float(np.std(connectivity_matrix)),
            'max_connectivity': float(np.max(connectivity_matrix)),
            'min_connectivity': float(np.min(connectivity_matrix))
        }
        
        return connectivity_matrix, self.labels, additional_metrics

# Example usage:
if __name__ == "__main__":
    processor = FunctionalConnectivityProcessor("models/FC_Other_Models.ipynb")
    # Test with a sample file
    # matrix, regions, metrics = processor.process_nifti("path_to_your_nifti_file.nii.gz") 