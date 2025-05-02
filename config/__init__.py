import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "settings.yaml")

with open(CONFIG_PATH, "r") as f:
    settings = yaml.safe_load(f)
