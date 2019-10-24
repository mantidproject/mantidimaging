from PyQt5 import Qt
from PyQt5.QtWidgets import QWidget

from mantidimaging.core.data import Images


class MetadataDialog(Qt.QDialog):
    """
    Dialog used to show a pretty formatted version of the image metadata.
    """

    def __init__(self, parent: QWidget, image: Images):
        super(MetadataDialog, self).__init__(parent)

        self.setWindowTitle('Image Metadata')
        self.setSizeGripEnabled(True)
        self.resize(600, 300)

        metadataText = Qt.QTextEdit()
        metadataText.setReadOnly(True)
        metadataText.setText(image.properties_pretty)

        buttons = Qt.QDialogButtonBox(Qt.QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)

        layout = Qt.QVBoxLayout()
        layout.addWidget(metadataText)
        layout.addWidget(buttons)
        self.setLayout(layout)
