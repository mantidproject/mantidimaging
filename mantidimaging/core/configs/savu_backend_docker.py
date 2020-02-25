import os

# Name of the environment variable expected to contain
# the name of the output directory. This is needed to
# load the images back after processing remotely
MANTIDIMAGING_OUTPUT_DIR_NAME = "MANTIDIMAGING_OUTPUT_DIR"


def env(name, default):
    return os.path.abspath(os.path.expanduser(os.environ.get(name, default)))


class RemoteConfig:
    LOCAL_OUTPUT_DIR = env(MANTIDIMAGING_OUTPUT_DIR_NAME, "~/output")


class RemoteConstants:
    """
    These are constants that are set in the Hebi application.
    They are paths on the remote server/docker container/host.
    Changing them without adjustment is guaranteed
    to be a breaking change.
    """
    # dir on which the outside of the container is mounted
    OUTSIDE_MOUNT_DIR = "/outside"
    # dir where the output will be stored
    OUTPUT_DIR = "/output"
