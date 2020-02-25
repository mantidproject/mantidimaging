import os


class RemoteConfig:
    LOCAL_OUTPUT_DIR = os.path.expanduser("/babylon/Public/Dimitar Tasev/output")


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
