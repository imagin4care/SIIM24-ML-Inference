# ML Inference server

This is a simple server that can be used to serve monai models.

## Install

### Build the docker image
In `monai_ml` directory, run:

```bash
docker build -t monai_ml .
```

### Run the docker container
```bash
docker run -p 8000:8000 --gpus all monai_ml
```
*Option*: mount volumes to the container to access the models and data.
```bash

docker run -p 8000:8000 --gpus all -v /path/to/data:/app/dcm -v /path/to/output:/app/ monai_ml
```

## Usage
Look at the file `model_info.json` to see the available models.
Each model there can be used to make a prediction by sending a GET request to the server.

1. Download the model weights from the model zoo.
```bash
GET on localhost:8000/download/{model_name}
```

2. Put data in the dcm folder inside the container. There are two options.
    - Put the data in the dcm folder inside the container using docker cp command.
      ```bash
        docker cp /path/to/data/. container_id:/app/dcm/{model_name}
      ```
    - Mount a volume to the dcm folder and put data in dcm/model_name folder.
    ````bash
    docker run -p 8000:8000 --gpus all -v /path/to/data:/app/dcm -v /path/to/output:/app/ monai_ml
   ````

   
2. Inference on the model.
```bash
GET on localhost:8000/inference/{model_name}
```

The output is stored in output folder inside the container. You can mount a volume to the output folder to access the output.

#TODO

- [ ] Add support for multiple models (model tested are spleen segmentation and brats axial generation)
- [ ] Use POST request to send data to the server instead of GET
- [ ] Add support for multiple data formats (currently it is amde manually as spleen segmentation request nifti file)
- [ ] Add integration with Orthanc
- [ ] CLean code