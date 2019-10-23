from enum import Enum


class BackendOptions(Enum):
    DATA_SOURCE_DIR = 1
    OUTPUT_DIR = 2
    IMAGE_NAME = 3


backend_config = {
    BackendOptions.DATA_SOURCE_DIR: {
        "value": "/mnt/data"
    },
    BackendOptions.OUTPUT_DIR: {
        "value": "~/output"
    },
    BackendOptions.IMAGE_NAME: {
        "value": "dtasev/hebi:dev"
    }
}


class OptionalBackendOptions(Enum):
    NVIDIA_RUNTIME = 1
    HEBI_SOURCE_DIR = 2
    SAVU_SOURCE_DIR = 3


optional_backend_config = {
    OptionalBackendOptions.NVIDIA_RUNTIME: {
        "value": "--runtime=nvidia",
        "active": True
    },
    OptionalBackendOptions.HEBI_SOURCE_DIR: {
        "value": "~/dev/hebi/api",
        "active": True
    },
    OptionalBackendOptions.SAVU_SOURCE_DIR: {
        "value": "~/dev/savu",
        "active": True
    },
}
