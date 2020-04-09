def gpu_available():
    try:
        import cupy
        return cupy
    except ImportError:
        return False


