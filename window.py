import sys
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget,
                             QToolButton, QTableWidget, QVBoxLayout,
                             QTableWidgetItem, QFileDialog, QStyle,
                             QAction, QComboBox, QLabel)
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QSize, QTimer
from serial_com_reader import PortReader, ReadPortData
import threading
import queue
import time

class MyMainWindow(QMainWindow):
    """
    Main window, with a toolbar, the option to save the data to .csv, and
    pyqtgraph widget with the data.
    """
    def __init__(self):
        super().__init__()
        self.port = None
        self.baud = None
        self.read = None
        self.setWindowTitle('Arduino serial COM plotter')
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.dataAr = []
        self.x, self.y, self.z = None, None, None
        self.data_queue = queue.Queue()
        self.total_time = 0

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.layout.addWidget(self.plot_widget)
        self.setupGUI()

        self.time_counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateData)
        self.timer.start(100)
        self.thread = threading.Thread(target=self.readDataThread, daemon=True)
        self.thread.start()

    def plotData(self, time):
        if self.z is not None and len(time)==len(self.z):
            self.plot_widget.clear()
            self.plot_widget.plot(time, self.z, pen='k')
            styles = {"color": "#454545", "font-size": "20px"}
            self.plot_widget.setBackground('w')
            self.plot_widget.setLabel("left", "y axis", **styles)
            self.plot_widget.setLabel("bottom", "time, ms", **styles)
            self.plot_widget.setXRange(time[0], time[-1])

    def updatePlot(self):
        if not self.data_queue.empty():
            self.processData()
            self.time_counter += len(self.z)

    def readDataThread(self):
        while True:
            if self.port and self.baud:
                read = ReadPortData(self.port, self.baud)
                data = read.readDataLines()
                if data is not None and not isinstance(data, OSError):
                    for line in data:
                        self.data_queue.put(line)

    def processData(self):
        decodedData = []
        while not self.data_queue.empty():
            decodedData.append(self.data_queue.get().decode('utf-8').strip())
    
        if decodedData:
            decodedData = decodedData[1:]
            expected_length = len(decodedData[0].split(','))
            valid_lines = [line.split(',') for line in decodedData if len(line.split(',')) == expected_length]
            valid_lines_filtered = [[float(val) for val in line] for line in valid_lines if all(val.strip() for val in line)]
            axesArray = np.array(valid_lines_filtered, dtype=float)
            self.x = axesArray[:, 0]
            self.y = axesArray[:, 1]
            self.z = axesArray[:, 2]

            num_data_points = len(self.z)-1
            new_time = np.arange(self.total_time, self.total_time + num_data_points * 0.001, 0.001)
            self.total_time += num_data_points * 0.001
            self.plotData(new_time)

    def updateData(self):
        if self.port and self.baud:
            self.read = ReadPortData(self.port, self.baud)
            self.dataAr = self.read.readDataLines()
            if self.dataAr is not None:
                self.processData()

    def setupGUI(self):
        self.setGeometry(0, 0, 1000, 700)
        self.setContentsMargins(10, 10, 10, 10)
        self.createToolbar()
        self.csv_file = ""
        self.csv_file_name = ""

    def createToolbar(self):
        self.toolbar = self.addToolBar("File")
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)
        self.toolbar.setAllowedAreas(Qt.TopToolBarArea)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet("border: 2px; padding: 4px;")
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_FileDialogListView))

        save_icon = self.style().standardIcon(QStyle.SP_DialogSaveButton)
        save_btn = QToolButton(text = "Save", icon = save_icon)
        save_btn.setStyleSheet("QToolButton:hover {background: #D7DAE0;}")
        self.toolbar.addWidget(save_btn)

        self.statusbar = self.statusBar()
        self.statusbar.setStyleSheet("font-size: 12pt; color: #888a85")
        self.statusbar.showMessage("Ready")

        self.portComboBox = QComboBox()
        self.updatePorts()
        self.toolbar.addWidget(self.portComboBox)

        self.baudRateComboBox = QComboBox()
        bauds = ['300 baud', '1200 baud', '2400 baud', '4800 baud', '9600 baud', '19200 baud',
        '38400 baud', '57600 baud', '74880 baud', '115200 baud', '230400 baud', '250000 baud',
        '500000 baud', '1000000 baud', '2000000 baud']
        self.baudRateComboBox.addItems(bauds)
        self.toolbar.addWidget(self.baudRateComboBox)
        self.selectedBaudRate = QLabel(f"Selected baud rate: {self.baud}")
        self.layout.addWidget(self.selectedBaudRate)
        self.baudRateComboBox.currentIndexChanged.connect(self.onBaudSelected)

        refresh_action = QAction("Refresh ports", self)
        refresh_action.triggered.connect(self.updatePorts)
        self.toolbar.addAction(refresh_action)
        self.selectedPortLabel = QLabel(f"Selected Port: {self.port}")
        self.layout.addWidget(self.selectedPortLabel)
        self.portComboBox.currentIndexChanged.connect(self.onPortSelected)

    def onBaudSelected(self):
        if self.read:
            self.read.closePort()
            self.read = None
            self.baud = None
            selectedBaud = self.baudRateComboBox.currentText()
            self.selectedBaudRate.setText(f"Selected baud rate: {selectedBaud}")
        else:
            selectedBaud = self.baudRateComboBox.currentText()
            self.selectedBaudRate.setText(f"Selected baud rate: {selectedBaud}")
            self.baud = int(selectedBaud.split(" ")[0])
            if self.port and self.baud:
                self.updateData()

    def updatePorts(self):
        ports = PortReader.readAvailablePorts()
        self.portComboBox.clear()
        self.portComboBox.addItems(ports)

    def onPortSelected(self):
        if self.read:
            self.read.closePort()
            self.read = None
            self.port = None
            selectedPort = self.portComboBox.currentText()
            self.selectedPortLabel.setText(f"Selected Port: {selectedPort}")
        else:
            selectedPort = self.portComboBox.currentText()
            self.selectedPortLabel.setText(f"Selected Port: {selectedPort}")
            self.port = selectedPort.split(" ")[0][:-1]
            if self.port and self.baud:
                self.updateData()

def main():
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
