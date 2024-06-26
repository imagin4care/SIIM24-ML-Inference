import asyncio
import logging
import subprocess
import threading
import zipfile
import requests
import os
import shutil
import yaml
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
progress = {}


def get_current_folder():
    return os.path.dirname(os.path.abspath(__file__))


# 1. Load configuration and store as environment variables
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


class MonaiZooModel:
    base_url = "https://github.com/Project-MONAI/model-zoo/releases/download/hosting_storage_v1"
    _model_info = None

    def __str__(self):
        title_art = r"""
          __  __  ____  _   _          _____       ____  _____ _______ _    _          _   _  _____ 
         |  \/  |/ __ \| \ | |   /\   |_   _|     / __ \|  __ \__   __| |  | |   /\   | \ | |/ ____|
         | \  / | |  | |  \| |  /  \    | |______| |  | | |__) | | |  | |__| |  /  \  |  \| | |     
         | |\/| | |  | | . ` | / /\ \   | |______| |  | |  _  /  | |  |  __  | / /\ \ | . ` | |     
         | |  | | |__| | |\  |/ ____ \ _| |_     | |__| | | \ \  | |  | |  | |/ ____ \| |\  | |____ 
         |_|  |_|\____/|_| \_/_/    \_\_____|     \____/|_|  \_\ |_|  |_|  |_/_/    \_\_| \_|\_____
        """

        header = "\033[1;34m" + "=" * 60 + "\033[0m"
        title = "\033[1;32m" + title_art + "\033[0m"
        models = "\n".join([f"\033[1;33m- {m}\033[0m" for m in self.list_available_models()])
        # return f"{header}\n{title}\nAvailable models are:\n{models}\n{header}"
        return title

    @property
    def model_info(self):
        # if self._model_info is None:
        #     with open("monai_zoo_info.yaml", "r") as file:
        #         self._model_info = yaml.safe_load(file)
        # return self._model_info
        if self._model_info is None:
            with open(os.path.join(get_current_folder(), "model_info.json"), "r") as file:
                self._model_info = json.load(file)
        return self._model_info

    def download_with_fire(self, model_name):
        command = [
            'python',
            '-m',
            'monai.bundle',
            'download',
            model_name,
            '--bundle_dir',
            os.environ.get('HOLOSCAN_MODEL_PATH')
        ]
        result = subprocess.run(command, capture_output=True, text=True)
        # Print the output
        if result.stdout:
            print("Standard Output:")
            print(result.stdout)

        if result.stderr:
            print("Standard Error:")
            print(result.stderr)

        # Check for errors
        if result.returncode != 0:
            print(f"Command failed with return code {result.returncode}")
        else:
            print("Command executed successfully")

    def download_model(self, model_name: str, sio):
        if model_name not in self.list_available_models():
            raise ValueError(
                f"Model {model_name} not found in model zoo. Available models: {list(self.model_info.keys())}")
        if model_name in self.list_downloaded_models():
            logging.info(f"N Model {model_name} already exists")
            return 200, {"message": "Model already exists"}
        progress[model_name] = 0
        threading.Thread(target=self._sync_do_download_model, args=(model_name, sio)).start()

    def _sync_do_download_model(self, model_name: str, sio):
        asyncio.run(self._do_download_model(model_name, sio))

    async def _do_download_model(self, model_name: str, sio):
        model = self.model_info.get(model_name)
        if model is None:
            raise ValueError(
                f"Model {model_name} not found in model zoo. Available models: {list(self.model_info.keys())}")
        file_name = model_name + ".zip"
        url = self.model_info[model_name].get("source")

        output_folder = os.path.join(os.environ.get("HOLOSCAN_MODEL_PATH"), model_name)
        output_file = os.path.join(os.environ.get("HOLOSCAN_MODEL_PATH"), file_name)

        if os.path.exists(output_folder):
            logging.info(f"Model {model_name} already exists at {output_folder}")
            return output_folder

        logging.info(f"Downloading model {model_name} from {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        with open(output_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
                    downloaded_size += len(chunk)
                    progress = int((downloaded_size / total_size) * 100)
                    sio.emit('download_progress', {'model_name': model_name, 'progress': progress})
        logging.info(f"Downloaded model {model_name} to {output_file}")
        with zipfile.ZipFile(output_file, 'r') as zip_ref:
            for member in zip_ref.namelist():
                # Extract each file to the specified directory
                zip_ref.extract(member, output_folder)
        logging.info(f"Extracted model {model_name} to {output_folder}")
        os.remove(output_file)
        logging.info(f"Deleted model zip {output_file}")
        return output_folder

    def delete_model(self, model_name):
        model = self.model_info.get(model_name)
        if model is None:
            raise ValueError(
                f"Model {model_name} not found in model zoo. Available models: {list(self.model_info.keys())}")
        file_name = model.get("file") + ".zip"

        output_path = os.path.join(os.environ.get("HOLOSCAN_MODEL_PATH"), model_name)
        if os.path.exists(output_path):
            logging.info(f"Deleting model {model_name} from {output_path}")
            shutil.rmtree(output_path)
            return True

    def list_available_models(self):
        return list(self.model_info.keys())

    def list_downloaded_models(self):
        return os.listdir(os.environ.get("HOLOSCAN_MODEL_PATH"))

    def get_bundle_root(self, name1):
        base_path = os.path.join(os.environ.get("HOLOSCAN_MODEL_PATH"), name1)

        # List directories under the base path
        try:
            subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]

            # Ensure there is exactly one subdirectory
            if len(subdirs) == 1:
                name2 = subdirs[0]
                bundle_root = os.path.join(base_path, name2)

                return bundle_root
            else:
                return f"Error: Expected exactly one subdirectory under {base_path}, found {len(subdirs)}."
        except Exception as e:
            return f"Error: {str(e)}"

    def inference(self, model_name):
        bundle_root = self.get_bundle_root(model_name)
        config_path = os.path.join(bundle_root, "configs", "inference.json")
        command = ["python",
                   "-m", "monai.bundle",
                   "run",
                   "--config_file", config_path,
                   "--bundle_root", bundle_root]
        if "segmentation" in model_name or "classification" in model_name:  # we need inputs image
            command.extend(["--dataset_dir",
                            os.path.join(os.environ.get("HOLOSCAN_INPUT_PATH"), model_name)])
        command.extend(["--output_dir",
                        os.path.join(os.environ.get("HOLOSCAN_OUTPUT_PATH"), model_name)])
        print(command)
        subprocess.run(command, check=True)
