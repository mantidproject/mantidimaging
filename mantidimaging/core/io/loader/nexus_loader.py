import h5py


def get_tomo_entry(nexus_file, entry_path: str):
    try:
        return nexus_file[entry_path]
    except Exception:
        return None


def execute(file_path: str):
    with h5py.File(file_path, 'r') as nexus_file:
        tomo_entry = get_tomo_entry(nexus_file, '/entry1/tomo_entry')
        if tomo_entry is not None:
            return
        data = get_tomo_entry(tomo_entry, 'data')
        image_key = get_tomo_entry(tomo_entry, 'image_key')
