from enum import Enum


class BackendOptions(Enum):
    DATA_SOURCE_DIR = 1
    OUTPUT_DIR = 2
    IMAGE_NAME = 3
    NVIDIA_RUNTIME = 4
    DEVELOPMENT = 5


backend_config = {
    BackendOptions.DATA_SOURCE_DIR: "/mnt/data",
    BackendOptions.OUTPUT_DIR: "~/output",
    BackendOptions.IMAGE_NAME: "dtasev/hebi",
    BackendOptions.NVIDIA_RUNTIME: {
        "value": "--runtime=nvidia",
        "active": True
    },
    # if True, will use the DevBackendOptions to mount Hebi and Savu sources
    BackendOptions.DEVELOPMENT: False,
}


class DevBackendOptions(Enum):
    HEBI_SOURCE_DIR = 1
    SAVU_SOURCE_DIR = 2
    DEVELOPMENT_LABEL = 3


dev_backend_config = {
    DevBackendOptions.HEBI_SOURCE_DIR: "~/dev/hebi/api",
    DevBackendOptions.SAVU_SOURCE_DIR: "~/dev/savu",
    # the label of the development image that should be used
    DevBackendOptions.DEVELOPMENT_LABEL: "dev"
}
