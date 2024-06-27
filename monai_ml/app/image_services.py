import glob
import os
import subprocess
import shutil
import dicom2nifti
import pydicom
import numpy as np
import nibabel as nib
from nibabel import Nifti1Header, Nifti1Image


class ImageManagement:
    def __init__(self, task_handler=None):
        self.task_handler = task_handler
        self.input_folder = os.environ.get("RAW_INPUT_FOLDER")

    def dicom_series_to_nifti_niix(self, series_uuid, output_folder):
        dicom_dir = os.path.join(self.input_folder, series_uuid)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        cmd = ['dcm2niix','-z','y','-f', series_uuid,'-o', output_folder, dicom_dir]
        subprocess.run(cmd, check=True)

    def dicom_series_to_nifti(self,series_uuid, output_folder):

        task_h = self.task_handler.add_records({
            "task_name": "dicom_series_to_nifti",
            "series_uuid": series_uuid,
            "status": "open",
            "progress": 0
        })
        dicom_dir = os.path.join(self.input_folder, series_uuid)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        nifti_output_path = os.path.join(output_folder, series_uuid + ".nii.gz")
        # Run dcm2niix command to convert DICOM to NIfTI
        dicom2nifti.convert_directory(dicom_dir, output_folder)
        #cmd = ['dcm2niix','-z','y','-f', series_uuid,'-o', temp_output_dir, dicom_dir]
        #subprocess.run(cmd, check=True)

    def nifti_to_dicom_series(self, series_uuid, output_folder):
        dicom_dir = os.path.join(self.input_folder, series_uuid)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)


