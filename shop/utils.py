import yaml
from django.conf import settings

def load_yaml_data():
    yaml_file_path = settings.YAML_FILE_PATH

    # Open and load the YAML file
    try:
        with open(yaml_file_path, 'r') as file:
            data = yaml.safe_load(file)
            return data
    except FileNotFoundError:
        print(f"YAML file not found at: {yaml_file_path}")
        return None
    except yaml.YAMLError as exc:
        print(f"Error while parsing YAML: {exc}")
        return None
