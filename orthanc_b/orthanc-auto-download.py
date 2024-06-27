import os
import json
import requests
import orthanc


# Function to read the Orthanc configuration
def read_orthanc_config():
    config = json.loads(orthanc.GetConfiguration())
    return config


# Register the plugin to be called when a new instance is stored
def download_series(seriesId, output_folder):
    orthanc_url = "http://localhost:8042"

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Get the series metadata
    response = requests.get(f"{orthanc_url}/series/{seriesId}")
    series_metadata = response.json()

    # Create a folder for the series
    series_folder = os.path.join(output_folder, seriesId)
    os.makedirs(series_folder, exist_ok=True)

    # Download each instance in the series
    for instanceId in series_metadata["Instances"]:
        instance_response = requests.get(f"{orthanc_url}/instances/{instanceId}/file")
        dicom_path = os.path.join(series_folder, f"{instanceId}.dcm")

        with open(dicom_path, 'wb') as f:
            f.write(instance_response.content)

        print(f"Downloaded DICOM file: {dicom_path}")


# Register the plugin to be called when a new series is stored
def OnChange(changeType, level, resourceId):
    if changeType == orthanc.ChangeType.STABLE_SERIES:
        config = read_orthanc_config()
        output_folder = config.get("StorageML", None)
        # Download the series
        download_series(resourceId, output_folder)


def OnStartup():
    print("Python plugin for downloading DICOM series is active")


orthanc.RegisterOnChangeCallback(OnChange)
