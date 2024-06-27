import logging

import yaml
from fastapi import FastAPI
from fastapi_socketio import SocketManager
from starlette.responses import JSONResponse
import os
from monai_services import MonaiZooModel
from image_services import ImageManagement
from utils import get_current_folder
from tasks_services import Task

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = FastAPI()
sio = SocketManager(app=app)


def load_config_as_env_vars(config_path: str):
    # Read the YAML file
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    # Recursively set environment variables
    def set_env_vars(prefix, config_dict):
        for key, value in config_dict.items():
            if isinstance(value, dict):
                # If value is a dictionary, recurse
                set_env_vars(f"{prefix}{key}_", value)
            else:
                # Set the environment variable
                env_var = f"{prefix}{key}".upper()
                os.environ[env_var] = str(value)

    set_env_vars('', config)


load_config_as_env_vars(os.path.join(get_current_folder(), 'config.yaml'))

# 2. Setup folder structure
if not os.path.exists(os.environ.get("HOLOSCAN_MODEL_PATH")):
    os.makedirs(os.environ.get("HOLOSCAN_MODEL_PATH"))
if not os.path.exists(os.environ.get("HOLOSCAN_OUTPUT_PATH")):
    os.makedirs(os.environ.get("HOLOSCAN_OUTPUT_PATH"))
if not os.path.exists(os.environ.get("HOLOSCAN_INPUT_PATH")):
    os.makedirs(os.environ.get("HOLOSCAN_INPUT_PATH"))
if not os.path.exists(os.environ.get("TASK_RECORDS_PATH")):
    os.makedirs(os.environ.get("TASK_RECORDS_PATH"))

MONAI_ZOO_URL = "https://github.com/Project-MONAI/model-zoo/releases/download/hosting_storage_v1"

tasks = Task(os.path.join(os.getenv("TASK_RECORDS_PATH"), "tasks.json"))
image_management = ImageManagement(task_handler=tasks)
monai_zoo_model = MonaiZooModel(task_handler=tasks, image_management=image_management)
logging.info(monai_zoo_model)


@app.get('/{model_name}/download')
async def download(model_name: str):
    logging.info(f"Downloading model {model_name}")
    try:
        monai_zoo_model.download_model(model_name, sio=sio)
        # monai_zoo_model.download_with_fire(model_name)
        return JSONResponse(status_code=202, content={"message": "Download started"})
    except ValueError as e:
        return JSONResponse(status_code=400, content={"message": str(e)})


@app.get('/{model_name}/predict/{series_uuid}')
def inference(model_name: str, series_uuid: str):
    logging.info(f"Running inference with model {model_name}")
    monai_zoo_model.inference(model_name, series_uuid=series_uuid)
    return {"message": "Inference started"}


@app.get('/tasks/{task_id}')
def get_task(task_id: str):
    return monai_zoo_model.get_task(task_id)

@app.delete('/tasks/{task_id}')
def get_task(task_id: str):
    tasks.delete_task(task_id)


@app.get('/tasks')
def add_task():
    return tasks.records


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='localhost', port=8000, reload=True, log_level="debug")
