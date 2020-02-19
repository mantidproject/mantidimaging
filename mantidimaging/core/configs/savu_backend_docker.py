import os


class RemoteConfig:
    LOCAL_DATA_DIR = "/mnt/e"
    LOCAL_OUTPUT_DIR = os.path.expanduser("~/output")
    IMAGE_NAME = "dtasev/hebi"
    NVIDIA_RUNTIME = {"value": "--runtime=nvidia", "active": False}
    DEVELOPMENT = False


class DevelopmentRemoteConfig:
    HEBI_SOURCE_DIR = os.path.expanduser("~/dev/hebi/api")
    SAVU_SOURCE_DIR = os.path.expanduser("~/dev/savu")
    # the label of the development image that should be used
    DEVELOPMENT_LABEL = "dev"


class RemoteConstants:
    """
    These are constants that are set in the Hebi application.
    They are paths on the remote server/docker container/host.
    Changing them without adjustment is guaranteed
    to be a breaking change.
    """
    DATA_DIR = "/data"
    OUTPUT_DIR = "/output"
    HEBI_SOURCE_DIR = "/webservice"
    SAVU_SOURCE_DIR = "/savu_custom"
