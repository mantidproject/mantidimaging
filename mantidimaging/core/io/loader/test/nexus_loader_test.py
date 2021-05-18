from mantidimaging.core.io.loader.nexus_loader import _missing_field_message


def test_missing_field_message():
    assert _missing_field_message(
        "missing_field") == "The NeXus file does not contain the required missing_field field."
