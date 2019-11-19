class BackendConfig:
    DATA_SOURCE_DIR = "/mnt/data"
    OUTPUT_DIR = "~/output"
    IMAGE_NAME = "dtasev/hebi"
    NVIDIA_RUNTIME = {
        "value": "--runtime=nvidia",
        "active": True
    }
    DEVELOPMENT = False


class DevelopmentBackendConfig:
    HEBI_SOURCE_DIR = "~/dev/hebi/api"
    SAVU_SOURCE_DIR = "~/dev/savu"
    # the label of the development image that should be used
    DEVELOPMENT_LABEL = "dev"
