import numpy as np
import nibabel as nib
from nilearn import datasets
from nilearn import image
from nilearn import regions
import pandas as pd
from typing import Tuple, Dict, Optional
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
from scipy.stats import zscore
import logging
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.funcational_connectivity_gcn import (
    preprocess_fmri,
    validate_connectivity_matrix,
    create_connection_table,
    predict_connectivity,
    get_region_coordinates
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class FunctionalConnectivityProcessor:
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the processor.
        
        Args:
            model_path: Path to the pre-trained model file (.pth) or notebook (.ipynb)
        """
        self.model_path = model_path
        # Load Harvard-Oxford subcortical atlas
        self.atlas = datasets.fetch_atlas_harvard_oxford('sub-maxprob-thr25-2mm')
        self.atlas_filename = self.atlas.maps
        self.labels = self.atlas.labels
        
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
        try:
            logger.info(f"Starting to process NIfTI file: {nifti_file_path}")
            
            # Process the NIfTI file using our GCN model
            logger.info("Processing fMRI data with GCN model...")
            result = predict_connectivity(nifti_file_path, ipynb_path=self.model_path)
            
            connectivity_matrix = np.array(result['connectivity_matrix'])
            region_labels = result.get('region_names', [f'Region_{i}' for i in range(connectivity_matrix.shape[0])])
            
            # Create connection table
            connection_table = create_connection_table(connectivity_matrix, region_labels)
            logger.info(f"Connectivity matrix shape: {connectivity_matrix.shape}")
            
            # Generate heatmap visualization
            logger.info("Generating heatmap visualization...")
            plt.figure(figsize=(12, 10))
            plt.imshow(connectivity_matrix, cmap='coolwarm', vmin=-1, vmax=1)
            plt.colorbar(label='Connection Strength')
            plt.title('Brain Connectivity Matrix')
            plt.xlabel('Brain Regions')
            plt.ylabel('Brain Regions')
            
            # Save the heatmap
            heatmap_path = os.path.join('uploads', 'connectivity_matrix.png')
            logger.info(f"Saving heatmap to: {heatmap_path}")
            plt.savefig(heatmap_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Generate connectome visualization
            logger.info("Generating connectome visualization...")
            features, edge_index, num_regions, _, atlas_img = preprocess_fmri(nifti_file_path)
            coords = get_region_coordinates(atlas_img, num_regions, region_labels)
            
            plt.figure(figsize=(12, 10))
            from nilearn import plotting
            plotting.plot_connectome(
                connectivity_matrix,
                coords,
                node_size=40,
                edge_threshold="80%",
                title="Brain Network Connectome",
                display_mode='ortho'
            )
            
            # Save the connectome
            connectome_path = os.path.join('uploads', 'connectome.png')
            logger.info(f"Saving connectome to: {connectome_path}")
            plt.savefig(connectome_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Save connection table
            connection_table_path = os.path.join('uploads', 'connection_strengths.csv')
            connection_table.to_csv(connection_table_path, index=False)
            logger.info(f"Saved connection table to: {connection_table_path}")
            
            # Prepare additional metrics
            logger.info("Calculating additional metrics...")
            additional_metrics = {
                'mean_connectivity': float(np.mean(connectivity_matrix)),
                'std_connectivity': float(np.std(connectivity_matrix)),
                'max_connectivity': float(np.max(connectivity_matrix)),
                'min_connectivity': float(np.min(connectivity_matrix)),
                'num_regions': connectivity_matrix.shape[0],
                'connection_table': connection_table.to_dict('records')
            }
            
            logger.info("Successfully completed processing NIfTI file")
            return connectivity_matrix, region_labels, additional_metrics
            
        except Exception as e:
            logger.error(f"Error processing NIfTI file: {str(e)}", exc_info=True)
            raise

# Example usage:
if __name__ == "__main__":
    processor = FunctionalConnectivityProcessor()
    # Test with a sample file
    # matrix, regions, metrics = processor.process_nifti("path_to_your_nifti_file.nii.gz") 