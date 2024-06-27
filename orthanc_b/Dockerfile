# Use the official Orthanc image as a base
FROM orthancteam/orthanc

RUN python3 -m pip install --break-system-packages requests

COPY orthanc-auto-download.py /python/