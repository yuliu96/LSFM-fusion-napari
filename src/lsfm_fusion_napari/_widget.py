import logging
import warnings

from qtpy.QtWidgets import (
    QPushButton,
    QWidget,
    QLabel,
    QComboBox,
    QCheckBox,
    QLineEdit,
    QGroupBox,
    QGridLayout,
    QSizePolicy,
    QVBoxLayout,
    QScrollArea,
    QDialog,
)
from qtpy.QtCore import Qt

import napari

from ._writer import save_dialog, write_tiff


class FusionWidget(QWidget):
    """Main widget for the plugin."""

    def __init__(self, viewer: napari.viewer.Viewer):
        super().__init__()
        self.viewer = viewer
        self.logger: logging.Logger
        self._initialize_logger()

        self.logger.debug("Initializing FusionWidget")

        self._initialize_ui()

        def wrapper(self, func, event):
            self.logger.debug("Exiting")
            return func(event)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            func = self.viewer.window._qt_window.closeEvent
            self.viewer.window._qt_window.closeEvent = lambda event: wrapper(self, func, event)

        self.viewer.layers.events.inserted.connect(self._update_layer_comboboxes)
        self.viewer.layers.events.inserted.connect(self._connect_rename)
        self.viewer.layers.events.removed.connect(self._update_layer_comboboxes)
        self.viewer.layers.events.reordered.connect(self._update_layer_comboboxes)
        for layer in self.viewer.layers:
            layer.events.name.connect(self._update_layer_comboboxes)
        self._update_layer_comboboxes()

        self.logger.debug("FusionWidget initialized")
        self.logger.info("Ready to use")

    def _initialize_logger(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        for handler in self.logger.handlers:
            self.logger.removeHandler(handler)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        self.logger.addHandler(handler)

    def _initialize_ui(self):
        self.logger.debug("Initializing UI")

        ### QObjects
        # objects that can be updated are attributes of the class
        # for ease of access

        # QLabels
        title = QLabel("<h1>LSFM Fusion</h1>")
        title.setAlignment(Qt.AlignCenter)
        title.setMaximumHeight(100)
        label_illustration1 = QLabel("Illustration 1:")
        label_illustration2 = QLabel("Illustration 2:")
        label_illustration3 = QLabel("Illustration 3:")
        label_illustration4 = QLabel("Illustration 4:")
        label_direction1 = QLabel("Direction:")
        label_direction2 = QLabel("Direction:")
        label_direction3 = QLabel("Direction:")
        label_direction4 = QLabel("Direction:")
        self.label_selected_direction2 = QLabel()
        self.label_selected_direction4 = QLabel()
        label_resample_ratio = QLabel("Resample ratio:")
        label_window_size = QLabel("Window size:")
        label_gf_kernel_size = QLabel("GF kernel size:")
        label_req_segmentation = QLabel("Require segmentation:")
        label_req_registration = QLabel("Require registration:")
        label_req_flip_illu = QLabel("Require flipping along illustration:")
        label_req_flip_dir = QLabel("Require flipping along direction:")

        # QPushButtons
        btn_process = QPushButton("Process")
        btn_save = QPushButton("Save")

        btn_process.clicked.connect(self._process_on_click)
        btn_save.clicked.connect(self._save_on_click)

        # QComboBoxes
        self.combobox_layer1 = QComboBox()
        self.combobox_layer2 = QComboBox()
        self.combobox_layer3 = QComboBox()
        self.combobox_layer4 = QComboBox()
        self.combobox_direction1 = QComboBox()
        self.combobox_direction3 = QComboBox()

        self.layer_comboboxes = [
            self.combobox_layer1,
            self.combobox_layer2,
            self.combobox_layer3,
            self.combobox_layer4,
        ]

        self.combobox_layer1.currentIndexChanged.connect(self._update_layer_comboboxes1)
        self.combobox_layer2.currentIndexChanged.connect(self._update_layer_comboboxes2)
        self.combobox_layer3.currentIndexChanged.connect(self._update_layer_comboboxes3)
        self.combobox_direction1.currentIndexChanged.connect(self._update_direction2)
        self.combobox_direction1.currentIndexChanged.connect(self._update_direction3)
        self.combobox_direction3.currentIndexChanged.connect(self._update_direction4)

        self.combobox_direction1.addItems(["Top", "Bottom", "Left", "Right"])

        # QCheckBoxes
        self.checkbox_req_segmentation = QCheckBox()
        self.checkbox_req_registration = QCheckBox()
        self.checkbox_req_flip_illu = QCheckBox()
        self.checkbox_req_flip_dir = QCheckBox()

        # QLineEdits
        self.lineedit_resample_ratio = QLineEdit()
        self.lineedit_window_size_Y = QLineEdit()
        self.lineedit_window_size_X = QLineEdit()
        self.lineedit_gf_kernel_size = QLineEdit()

        self.lineedit_resample_ratio.setText("2")
        self.lineedit_window_size_Y.setText("59")
        self.lineedit_window_size_X.setText("5")
        self.lineedit_gf_kernel_size.setText("49")

        # QWidgets
        line1 = QWidget()
        line1.setFixedHeight(4)
        line1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        line1.setStyleSheet("background-color: #c0c0c0")

        # QGroupBoxes
        input = QGroupBox("Input")
        input_layout = QGridLayout()
        input_layout.addWidget(label_illustration1, 0, 0)
        input_layout.addWidget(self.combobox_layer1, 0, 1)
        input_layout.addWidget(label_direction1, 1, 0)
        input_layout.addWidget(self.combobox_direction1, 1, 1)
        input_layout.addWidget(label_illustration2, 2, 0)
        input_layout.addWidget(self.combobox_layer2, 2, 1)
        input_layout.addWidget(label_direction2, 3, 0)
        input_layout.addWidget(self.label_selected_direction2, 3, 1)
        input_layout.addWidget(line1, 4, 0, 1, 2)
        input_layout.addWidget(label_illustration3, 5, 0)
        input_layout.addWidget(self.combobox_layer3, 5, 1)
        input_layout.addWidget(label_direction3, 6, 0)
        input_layout.addWidget(self.combobox_direction3, 6, 1)
        input_layout.addWidget(label_illustration4, 7, 0)
        input_layout.addWidget(self.combobox_layer4, 7, 1)
        input_layout.addWidget(label_direction4, 8, 0)
        input_layout.addWidget(self.label_selected_direction4, 8, 1)
        input.setLayout(input_layout)

        parameters = QGroupBox("Parameters")
        parameters_layout = QGridLayout()
        parameters_layout.addWidget(label_resample_ratio, 0, 0, 1, 2)
        parameters_layout.addWidget(self.lineedit_resample_ratio, 0, 2)
        parameters_layout.addWidget(label_window_size, 1, 0)
        parameters_layout.addWidget(self.lineedit_window_size_Y, 1, 1)
        parameters_layout.addWidget(self.lineedit_window_size_X, 1, 2)
        parameters_layout.addWidget(label_gf_kernel_size, 2, 0, 1, 2)
        parameters_layout.addWidget(self.lineedit_gf_kernel_size, 2, 2)
        parameters_layout.addWidget(label_req_segmentation, 3, 0, 1, 2)
        parameters_layout.addWidget(self.checkbox_req_segmentation, 3, 2)
        parameters_layout.addWidget(label_req_registration, 4, 0, 1, 2)
        parameters_layout.addWidget(self.checkbox_req_registration, 4, 2)
        parameters_layout.addWidget(label_req_flip_illu, 5, 0, 1, 2)
        parameters_layout.addWidget(self.checkbox_req_flip_illu, 5, 2)
        parameters_layout.addWidget(label_req_flip_dir, 6, 0, 1, 2)
        parameters_layout.addWidget(self.checkbox_req_flip_dir, 6, 2)
        parameters.setLayout(parameters_layout)

        ### Layout
        layout = QGridLayout()
        layout.addWidget(title, 0, 0, 1, -1)
        layout.addWidget(input, 1, 0, 1, -1)
        layout.addWidget(parameters, 2, 0, 1, -1)
        layout.addWidget(btn_process, 3, 0)
        layout.addWidget(btn_save, 3, 1)

        widget = QWidget()
        widget.setLayout(layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(scroll_area)
        self.setMinimumWidth(330)

    def _update_layer_comboboxes(self):
        self.logger.debug("Updating layer comboboxes")
        layernames = [
            layer.name
            for layer in self.viewer.layers
            if type(layer) == napari.layers.Image
        ]
        layernames.reverse()

        self.combobox_layer1.clear()
        self.combobox_layer1.addItems(layernames)
        last_index = self.combobox_layer1.count() - 1
        self.combobox_layer1.setCurrentIndex(last_index)
        # for combobox in self.layer_comboboxes:
        #     combobox.clear()
        #     # combobox.addItems(layernames)

        # self.combobox_layer4.insertItem(0, "")
        # self.combobox_layer4.addItems(layernames)
        # self.combobox_layer3.insertItem(0, "")
        # self.combobox_layer3.addItems(layernames)
        # self.combobox_layer2.addItems(layernames)
        # self.combobox_layer1.addItems(layernames)
        
    def _update_layer_comboboxes1(self, _):
        layernames = [
            layer.name
            for layer in self.viewer.layers
            if type(layer) == napari.layers.Image
            and layer.name != self.combobox_layer1.currentText()
        ]
        layernames.reverse()

        self.combobox_layer2.clear()
        self.combobox_layer2.addItems(layernames)
        last_index = self.combobox_layer2.count() - 1
        self.combobox_layer2.setCurrentIndex(last_index)
    
    def _update_layer_comboboxes2(self, _):
        layernames = [
            layer.name
            for layer in self.viewer.layers
            if type(layer) == napari.layers.Image
            and layer.name != self.combobox_layer1.currentText()
            and layer.name != self.combobox_layer2.currentText()
        ]
        layernames.append("")
        layernames.reverse()

        self.combobox_layer3.clear()
        self.combobox_layer3.addItems(layernames)
        last_index = self.combobox_layer3.count() - 1
        self.combobox_layer3.setCurrentIndex(last_index)

    def _update_layer_comboboxes3(self, _):
        layernames = [
            layer.name
            for layer in self.viewer.layers
            if type(layer) == napari.layers.Image
            and layer.name != self.combobox_layer1.currentText()
            and layer.name != self.combobox_layer2.currentText()
            and layer.name != self.combobox_layer3.currentText()
        ]
        layernames.append("")
        layernames.reverse()

        self.combobox_layer4.clear()
        self.combobox_layer4.addItems(layernames)
        last_index = self.combobox_layer4.count() - 1
        self.combobox_layer4.setCurrentIndex(last_index)

    def _connect_rename(self, event):
        event.value.events.name.connect(self._update_layer_comboboxes)

    def _update_direction2(self):
        self.logger.debug("Updating direction 2")
        direction1 = self.combobox_direction1.currentText()
        if direction1 == "Top":
            direction2 = "Bottom"
        elif direction1 == "Bottom":
            direction2 = "Top"
        elif direction1 == "Left":
            direction2 = "Right"
        elif direction1 == "Right":
            direction2 = "Left"
        self.label_selected_direction2.setText(direction2)

    def _update_direction3(self):
        self.logger.debug("Updating direction 3")
        direction1 = self.combobox_direction1.currentText()
        if direction1 in ["Top", "Bottom"]:
            directions = ["Left", "Right"]
        elif direction1 in ["Left", "Right"]:
            directions = ["Top", "Bottom"]
        self.combobox_direction3.clear()
        self.combobox_direction3.addItems(directions)

    def _update_direction4(self):
        self.logger.debug("Updating direction 4")
        direction3 = self.combobox_direction3.currentText()
        if direction3 == "Top":
            direction4 = "Bottom"
        elif direction3 == "Bottom":
            direction4 = "Top"
        elif direction3 == "Left":
            direction4 = "Right"
        elif direction3 == "Right":
            direction4 = "Left"
        else:
            direction4 = ""
        self.label_selected_direction4.setText(direction4)

    def _save_on_click(self):
        self.logger.debug("Save button clicked")
        layernames = [
            layer.name
            for layer in self.viewer.layers
            if type(layer) == napari.layers.Image
        ]
        layernames.reverse()
        if not layernames:
            self.logger.info("No layers available")
            return
        if len(layernames) == 1:
            self.logger.info("Only one layer available")
            layername = layernames[0]
        else:
            self.logger.info("Multiple layers available")
            dialog = LayerSelection(layernames)
            index = dialog.exec_()
            if index == -1:
                self.logger.info("No layer selected")
                return
            layername = layernames[index]
        self.logger.debug(f"Selected layer: {layername}")
        data = self.viewer.layers[self.viewer.layers.index(layername)].data
        self.logger.debug(f"Data shape: {data.shape}")
        self.logger.debug(f"Data dtype: {data.dtype}")
        filepath = save_dialog(self)
        if filepath == ".tiff" or filepath == ".tif":
            self.logger.info("No file selected")
            return
        self.logger.debug(f"Filepath: {filepath}")
        write_tiff(filepath, data)
        self.logger.info("Data saved")

    def _process_on_click(self):
        params = self._get_parameters()
        if params is None:
            return
        output_image = None # TODO: call fusion processing
        # self.viewer.add_image(output_image)
        # self.logger.debug(params)

    def _get_parameters(self):
        self.logger.debug("Compiling parameters")
        image1_name = self.combobox_layer1.currentText()
        image2_name = self.combobox_layer2.currentText()
        if image1_name not in self.viewer.layers:
            self.logger.error(f"Layer {image1_name} not found")
            return None
        if image2_name not in self.viewer.layers:
            self.logger.error(f"Layer {image2_name} not found")
            return None
        params = {}
        params["image1"] = self.viewer.layers[image1_name].data
        params["image2"] = self.viewer.layers[image2_name].data
        params["direction1"] = self.combobox_direction1.currentText()
        params["direction2"] = self.label_selected_direction2.text()
        image3_name = self.combobox_layer3.currentText()
        image4_name = self.combobox_layer4.currentText()
        if image3_name in self.viewer.layers and image4_name in self.viewer.layers:
            self.logger.info("Using 4 images")
            params["image3"] = self.viewer.layers[image3_name].data
            params["image4"] = self.viewer.layers[image4_name].data
            params["direction3"] = self.combobox_direction3.currentText()
            params["direction4"] = self.label_selected_direction4.text()
        try:
            params["resample_ratio"] = int(self.lineedit_resample_ratio.text())
        except ValueError:
            self.logger.error("Invalid resample ratio")
            return
        if not (1 <= params["resample_ratio"] <= 5):
            self.logger.error("Resample ratio must be between 1 and 5")
            return
        self.logger.debug(f"Resample ratio: {params['resample_ratio']}")
        try:
            params["window_size"] = (int(self.lineedit_window_size_Y.text()), int(self.lineedit_window_size_X.text()))
        except ValueError:
            self.logger.error("Invalid window size")
            return
        if not (9 <= params["window_size"][0] <= 89 and 3 <= params["window_size"][1] <= 29):
            self.logger.error("Window size must be between 3x29 and 9x89")
            return
        self.logger.debug(f"Window size: {params['window_size']}")
        try:
            params["GF_kernel_size"] = int(self.lineedit_gf_kernel_size.text())
        except ValueError:
            self.logger.error("Invalid GF kernel size")
            return
        if not (29 <= params["GF_kernel_size"] <= 89):
            self.logger.error("GF kernel size must be between 29 and 89")
            return
        self.logger.debug(f"GF kernel size: {params['GF_kernel_size']}")
        params["require_segmentation"] = self.checkbox_req_segmentation.isChecked()
        self.logger.debug(f"Require segmentation: {params['require_segmentation']}")
        params["require_registration"] = self.checkbox_req_registration.isChecked()
        self.logger.debug(f"Require registration: {params['require_registration']}")
        params["require_flip_illu"] = self.checkbox_req_flip_illu.isChecked()
        self.logger.debug(f"Require flipping along illustration: {params['require_flip_illu']}")
        params["require_flip_dir"] = self.checkbox_req_flip_dir.isChecked()
        self.logger.debug(f"Require flipping along direction: {params['require_flip_dir']}")
        return params
            

class LayerSelection(QDialog):
    def __init__(self, layernames: list[str]):
        super().__init__()
        self.setWindowTitle("Select Layer to save as TIFF")
        self.combobox = QComboBox()
        self.combobox.addItems(layernames)
        btn_select = QPushButton("Select")
        btn_select.clicked.connect(self.accept)
        layout = QVBoxLayout()
        layout.addWidget(self.combobox)
        layout.addWidget(btn_select)
        self.setLayout(layout)
        self.setMinimumSize(250, 100)

    def accept(self):
        self.done(self.combobox.currentIndex())

    def reject(self):
        self.done(-1)
