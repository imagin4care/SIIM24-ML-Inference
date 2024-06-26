import logging

from fastapi import FastAPI
from fastapi_socketio import SocketManager
from starlette.responses import JSONResponse

from monai_services import MonaiZooModel

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
app = FastAPI()
sio = SocketManager(app=app)

MONAI_ZOO_URL = "https://github.com/Project-MONAI/model-zoo/releases/download/hosting_storage_v1"

monai_zoo_model = MonaiZooModel()
logging.info(monai_zoo_model)


@app.get('/download/{model_name}')
async def download(model_name: str):
    logging.info(f"Downloading model {model_name}")
    try:
        monai_zoo_model.download_model(model_name, sio=sio)
        # monai_zoo_model.download_with_fire(model_name)
        return JSONResponse(status_code=202, content={"message": "Download started"})
    except ValueError as e:
        return JSONResponse(status_code=400, content={"message": str(e)})


@app.get('/inference/{model_name}')
def inference(model_name: str):
    logging.info(f"Running inference with model {model_name}")
    monai_zoo_model.inference(model_name)
    return {"message": "Inference started"}



if __name__ == '__main__':
    import uvicorn

    uvicorn.run(app, host='localhost', port=8000, reload=True, log_level="debug")