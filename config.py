import json


config_path = "config.json"


def get(option):
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
        return config[option]


def set(option, value):
    with open(config_path, "r") as config_file:
        config = json.load(config_file)

    try:
        if not isinstance(config[option], type(value)):
            raise ValueError

        config[option] = value

        with open(config_path, "w") as config_file:
            json.dump(config, config_file)

    # Returns an error if the value is of the wrong type
    except Exception as e:
        print(e)
