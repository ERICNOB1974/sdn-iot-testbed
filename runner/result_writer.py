import json
from pathlib import Path

import yaml


class ResultWriter:
    def __init__(self, results_dir):

        self.results_dir = Path(results_dir)

        self.results_dir.mkdir(parents=True, exist_ok=True)

    def write_text(self, filename, content):

        path = self.results_dir / filename

        with path.open("w", encoding="utf-8") as file:
            file.write(content)

        return path

    def write_json(self, filename, data):

        path = self.results_dir / filename

        with path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

        return path

    def write_yaml(self, filename, data):

        path = self.results_dir / filename

        with path.open("w", encoding="utf-8") as file:
            yaml.safe_dump(data, file, sort_keys=False, allow_unicode=True)

        return path
