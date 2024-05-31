import sys
import numpy as np
from scipy import signal
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget,
                             QToolButton, QRadioButton, QVBoxLayout,
                             QMessageBox, QFileDialog, QStyle,
                             QAction, QComboBox, QLabel, QPushButton)
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QSize, QTimer
from serial_com_helper import PortReader, ReadPortData, DataSaving
import threading
import queue
from save_temp_to_file import main_temp
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
        self.selectedAxis = "y"
        self.setWindowTitle('Arduino serial COM plotter')
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.dataAr = []
        self.x, self.y, self.z = None, None, None
        self.data_queue = queue.Queue()
        self.save_data_queue = queue.Queue()
        self.total_time = 0
        self.rms = None
        self.recording = False
        self.save_directory = None

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.layout.addWidget(self.plot_widget)
        self.setupGUI()

        self.time_counter = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateData)
        self.timer.start(1)
        self.thread = threading.Thread(target=self.readDataThread, daemon=True)
        self.thread.start()
        self.thread2 = threading.Thread(target=self.processData, daemon=True)
        self.thread2.start()

        self.second_plot_visible = False
        self.third_plot_visible = False

    def plotData(self, time): #TODO: move data helper methods to another class?
        if self.selectedAxis == "x":
            axis = self.x
        elif self.selectedAxis == "y":
            axis = self.y
        elif self.selectedAxis == "z":
            axis = self.z
        if self.z is not None and len(time)==len(self.z):
            self.plot_widget.clear()
            self.plot_widget.plot(time, axis, pen={'color': 'k', 'width':1})
            styles = {"color": "#454545", "font-size": "12px"}
            self.plot_widget.setBackground('w')
            self.plot_widget.setLabel("left", "Acceleration, g", **styles)
            self.plot_widget.setLabel("bottom", "Time, ms", **styles)
            self.plot_widget.setXRange(time[0], time[-1])

            self.rms = np.sqrt(np.mean(axis**2))*9.81
            self.calculatedRMS.setText(f"RMS: {self.rms} m/s**2")
            fft_z = np.fft.fft(axis)
            freq = np.fft.fftfreq(len(axis), d=(1/4000)) #d=1/odr #TODO: fs as user input
            (f_c, S) = signal.welch(axis, 4000, nperseg=len(axis))
            if self.second_plot_visible == True:
                self.plotFFT(fft_z, freq)
            if self.third_plot_visible == True:
                self.plotPeriodogram(f_c, S)

    def plotFFT(self, fft_z, freq):
        n = len(self.z)
        half_n = n//2
        self.second_plot_widget.clear()
        self.second_plot_widget.plot(freq[:half_n], np.abs(fft_z)[:half_n], pen={'color': 'r', 'width':1})
        styles = {"color": "#454545", "font-size": "12px"}
        self.second_plot_widget.setLabel("left", "Amplitude", **styles)
        self.second_plot_widget.setLabel("bottom", 'Frequency, Hz', **styles)

    def plotPeriodogram(self, f_c, S):
        self.third_plot_widget.clear()
        self.third_plot_widget.setLogMode(False, True)
        self.third_plot_widget.plot(f_c, S, pen={'color': 'r', 'width':1})
        styles = {"color": "#454545", "font-size": "12px"}
        self.third_plot_widget.setLabel("left", "PSD [V**2/Hz]", **styles)
        self.third_plot_widget.setLabel("bottom", 'Frequency, Hz', **styles)

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

    def saveDataThread(self):
        while self.recording:
            if not self.save_data_queue.empty():
                data_to_save = []
                while not self.save_data_queue.empty():
                    data_to_save.append(self.save_data_queue.get())
                saveData = DataSaving(data_to_save, self.save_directory)
                saveData.save()
                saveData.combineFiles()
            time.sleep(1)

    def processData(self):
        decodedData = []
        while not self.data_queue.empty():
            decodedData.append(self.data_queue.get().decode('utf-8').strip())
    
        if decodedData:
            decodedData = decodedData[1:]
            expected_length = len(decodedData[0].split(','))
            valid_lines = [line.split(',') for line in decodedData if len(line.split(',')) == expected_length]
            valid_lines_filtered = [[float(val) for val in line] for line in valid_lines if all(val.strip() for val in line)]
            axesArray = np.array(valid_lines_filtered, dtype=float) #TODO: no of axes as user input
            self.x = axesArray[:, 0]
            self.y = axesArray[:, 1]
            self.z = axesArray[:, 2]

            num_data_points = len(self.z)
            new_time = np.arange(self.total_time, self.total_time + num_data_points * 0.25, 0.25)
            self.total_time += num_data_points * 0.25 #1/odr, ms
            self.plotData(new_time)
            self.save_data_queue.put(decodedData)

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
        self.toolbar = self.addToolBar("")
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setMovable(False)
        self.toolbar.setAllowedAreas(Qt.TopToolBarArea)
        self.toolbar.setIconSize(QSize(24, 24))
        self.toolbar.setStyleSheet("border: 2px; padding: 4px;")
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_FileDialogListView))

        record_icon = self.style().standardIcon(QStyle.SP_DialogSaveButton)
        record_btn = QToolButton(text = "Record measurement", icon = record_icon)
        record_btn.setStyleSheet("QToolButton:hover {background: #D7DAE0;}")
        record_btn.clicked.connect(self.selectSaveDirectory)
        self.toolbar.addWidget(record_btn)

        stop_icon = self.style().standardIcon(QStyle.SP_BrowserStop)
        self.stop_btn = QToolButton(text="Stop recording", icon=stop_icon)
        self.stop_btn.setStyleSheet("QToolButton:hover {background: #D7DAE0;}")
        self.stop_btn.clicked.connect(self.stopRecording)
        self.stop_btn.setEnabled(False)
        self.toolbar.addWidget(self.stop_btn)

        self.statusbar = self.statusBar()
        self.statusbar.setStyleSheet("font-size: 12pt; color: #888a85")
        self.statusbar.showMessage("Select COM & baud rate")

        self.portComboBox = QComboBox()
        self.updatePorts()
        self.toolbar.addWidget(self.portComboBox)

        refresh_action = QAction("Refresh ports", self)
        refresh_action.triggered.connect(self.updatePorts)
        self.toolbar.addAction(refresh_action)

        self.baudRateComboBox = QComboBox()
        self.baudRateComboBox.setFixedWidth(150)
        bauds = ['300 baud', '1200 baud', '2400 baud', '4800 baud', '9600 baud', '19200 baud',
        '38400 baud', '57600 baud', '74880 baud', '115200 baud', '230400 baud', '250000 baud',
        '500000 baud', '1000000 baud', '2000000 baud']
        self.baudRateComboBox.addItems(bauds)
        self.toolbar.addWidget(self.baudRateComboBox)

        self.calculatedRMS = QLabel()
        self.layout.addWidget(self.calculatedRMS)

        self.radio_button_x = QRadioButton("X")
        self.radio_button_y = QRadioButton("Y")
        self.radio_button_z = QRadioButton("Z")
        self.layout.addWidget(self.radio_button_x)
        self.layout.addWidget(self.radio_button_y)
        self.layout.addWidget(self.radio_button_z)
        self.radio_button_x.toggled.connect(self.on_radio_button_toggled)
        self.radio_button_y.toggled.connect(self.on_radio_button_toggled)
        self.radio_button_z.toggled.connect(self.on_radio_button_toggled)
        self.radio_button_y.setChecked(True)

        self.selectedPortLabel = QLabel(f"Selected Port: {self.port}")
        self.layout.addWidget(self.selectedPortLabel)
        self.portComboBox.currentIndexChanged.connect(self.onPortSelected)

        self.selectedBaudRate = QLabel(f"Selected baud rate: {self.baud}")
        self.layout.addWidget(self.selectedBaudRate)
        self.baudRateComboBox.currentIndexChanged.connect(self.onBaudSelected)

        self.toggle_fft_button = QPushButton('FFT')
        self.toggle_fft_button.clicked.connect(self.toggleFFT)
        self.toggle_fft_button.setFixedWidth(150)
        self.layout.addWidget(self.toggle_fft_button)
        self.second_plot_widget = pg.PlotWidget()
        self.second_plot_widget.setBackground('w')
        self.second_plot_widget.setFixedHeight(280)
        self.second_plot_widget.hide()
        self.layout.addWidget(self.second_plot_widget)

        self.toggle_power_spectrum_button = QPushButton('Power spectrum')
        self.toggle_power_spectrum_button.clicked.connect(self.togglePeriodogram)
        self.toggle_power_spectrum_button.setFixedWidth(150)
        self.layout.addWidget(self.toggle_power_spectrum_button)
        self.third_plot_widget = pg.PlotWidget()
        self.third_plot_widget.setBackground('w')
        self.third_plot_widget.setFixedHeight(280)
        self.third_plot_widget.hide()
        self.layout.addWidget(self.third_plot_widget)

    def on_radio_button_toggled(self):
        if self.radio_button_x.isChecked():
            self.selectedAxis = "x"
        elif self.radio_button_y.isChecked():
            self.selectedAxis = "y"
        elif self.radio_button_z.isChecked():
            self.selectedAxis = "z"

    def selectSaveDirectory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Select Directory", options=options)
        if directory:
            self.save_directory = directory
            reply = QMessageBox.question(self, 'Start saving data',
                                         "The current option will start continuously saving data to the chosen dircetory. Proceed?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.startRecording()
                self.stop_btn.setEnabled(True)

    def startRecording(self):
        self.stop_btn.setEnabled(True)
        self.recording = True
        threading.Thread(target=self.saveDataThread, daemon=True).start()

    def stopRecording(self):
        reply = QMessageBox.question(self, 'Stop Saving', 'Are you sure you want to stop saving?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.recording = False

    def toggleFFT(self):
        if self.second_plot_visible:
            self.second_plot_widget.hide()
            self.second_plot_visible = False
        else:
            if self.third_plot_visible:
                self.third_plot_widget.hide()
                self.third_plot_visible = False
            self.second_plot_widget.show()
            self.second_plot_visible = True

    def togglePeriodogram(self):
        if self.third_plot_visible:
            self.third_plot_widget.hide()
            self.third_plot_visible = False
        else:
            if self.second_plot_visible:
                self.second_plot_widget.hide()
                self.second_plot_visible = False
            self.third_plot_widget.show()
            self.third_plot_visible = True

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
                self.statusbar.showMessage("Ready")
                self.updateData()

    def updatePorts(self):
        ports = PortReader.readAvailablePorts()
        self.portComboBox.clear()
        self.portComboBox.addItems(ports)
        if self.read:
            self.read.closePort()
            self.read = None
        self.port = None
        self.statusbar.showMessage("Select COM and baud rate")

    def onPortSelected(self):
        if self.read:
            self.read.closePort()
            self.read = None
            self.port = None
            selectedPort = self.portComboBox.currentText()
            self.selectedPortLabel.setText(f"Selected Port: {self.port}")
        else:
            selectedPort = self.portComboBox.currentText()
            self.port = selectedPort.split(" ")[0][:-1]
            self.selectedPortLabel.setText(f"Selected Port: {self.port}")
            if self.port and self.baud:
                self.statusbar.showMessage("Ready")
                self.updateData()

def main():
    pg.setConfigOptions(antialias=True)
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
