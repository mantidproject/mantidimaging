from PyQt5 import Qt


class MetadataDialog(Qt.QDialog):
    """
    Dialog used to show a pretty formatted version of the image metadata.
    """

    def __init__(self, parent, image):
        super(MetadataDialog, self).__init__(parent)

        self.setWindowTitle('Image Metadata')
        self.setSizeGripEnabled(True)
        self.resize(600, 300)

        metadataText = Qt.QTextEdit()
        metadataText.setReadOnly(True)
        metadataText.setText(image.properties_pretty)

        buttons = Qt.QDialogButtonBox(Qt.QDialogButtonBox.Close)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = Qt.QVBoxLayout()
        layout.addWidget(metadataText)
        layout.addWidget(buttons)
        self.setLayout(layout)
