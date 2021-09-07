class CommandLinePath:
    _instance = None
    images_path = ""

    def __new__(cls, path: str = ""):
        """
        Creates a singleton for storing the result of the Cuda check.
        """
        if cls._instance is None:
            cls._instance = super(CommandLinePath, cls).__new__(cls)
            cls.images_path = path
        return cls._instance

    @classmethod
    def path(cls) -> str:
        """
        Returns the shared cuda check result.
        """
        return cls.images_path
