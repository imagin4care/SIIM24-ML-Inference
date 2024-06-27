import json
import logging
import os
import uuid

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class Task:
    """Base class for tasks."""

    def __init__(self, records_file, ):
        self.records_file = records_file
        if os.path.exists(records_file):
            with open(records_file, "r") as f:
                self.records = json.load(f)
        else:
            self.records = []
            self.update_records()

    def find_task_with_id(self, task_name, series_uuid):
        for task in self.records:
            if task.get('task_name') == task_name and task.get('series_uuid') == series_uuid:
                return task
        return None

    def add_records(self, new_records):
        existing_records = self.find_task_with_id(new_records['task_name'], new_records['series_uuid'])
        if existing_records is not None:
            logging.info(
                f"Task {new_records['task_name']} for series {new_records['series_uuid']} already exists and is {existing_records['status']}")
            return existing_records
        else:
            new_records['task_id'] = str(uuid.uuid4())
            new_records['status'] = 'open'
            new_records['progress'] = 0
            self.records.append(new_records)
            self.update_records()
        return new_records

    def delete_task(self, task_id):
        for task in self.records:
            if task.get('task_id') == task_id:
                self.records.remove(task)
                self.update_records()
                return
        logging.info(f"Task with id {task_id} not found.")
    def update_records(self):
        with open(self.records_file, "w") as f:
            json.dump(self.records, f)

    def update_progress(self, task_id, progress):
        for task in self.records:
            if task.get('task_id') == task_id:
                task['progress'] = progress
                self.update_records()
                return
        logging.info(f"Task with id {task_id} not found.")

    def update_status(self, task_id, status):
        for task in self.records:
            if task.get('task_id') == task_id:
                task['status'] = status
                self.update_records()
                return
        logging.info(f"Task with id {task_id} not found.")

    def get_task(self, task_id):
        for task in self.records:
            if task.get('task_id') == task_id:
                return task
        return None

    def __str__(self):
        return str(self.records)

