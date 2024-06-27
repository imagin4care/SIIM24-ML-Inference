import os
import subprocess

import pydicom
import numpy as np
import nibabel as nib
from nibabel import Nifti1Header, Nifti1Image


class ImageManagement:
    def __init__(self, task_handler=None):
        self.task_handler = task_handler
        self.input_folder = os.environ.get("RAW_INPUT_FOLDER")

    def dicom_series_to_nifti(self,series_uuid, output_folder):
        try:
            subprocess.run(['dcm2niix', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except FileNotFoundError:
            raise RuntimeError("dcm2niix not found. Please install dcm2niix and make sure it is in your PATH.")
        task_h = self.task_handler.add_records({
            "task_name": "dicom_series_to_nifti",
            "series_uuid": series_uuid,
            "status": "open",
            "progress": 0
        })
        dicom_dir = os.path.join(self.input_folder, series_uuid)

        # Create a temporary output directory for dcm2niix
        temp_output_dir = os.path.join(dicom_dir, 'temp_nifti')
        os.makedirs(temp_output_dir, exist_ok=True)

        # Run dcm2niix command to convert DICOM to NIfTI
        cmd = ['dcm2niix','-z','y','-f', series_uuid,'-o', temp_output_dir, dicom_dir]
        subprocess.run(cmd, check=True)

        # Find the generated NIfTI file
        nifti_file = None
        for file in os.listdir(temp_output_dir):
            if file.endswith('.nii') or file.endswith('.nii.gz'):
                nifti_file = os.path.join(temp_output_dir, file)
                break

        if nifti_file is None:
            raise FileNotFoundError("No NIfTI file generated by dcm2niix.")

        print(nifti_file)
            # Move the NIfTI file to the desired output path
        nifti_output_path = os.path.join(output_folder, series_uuid + ".nii.gz")
        os.rename(nifti_file, nifti_output_path)

        # Clean up temporary directory
        os.rmdir(temp_output_dir)



