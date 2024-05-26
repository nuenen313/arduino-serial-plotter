import sys
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget,
                             QToolButton, QTableWidget, QVBoxLayout,
                             QTableWidgetItem, QFileDialog, QStyle,
                             QAction, QComboBox, QLabel)
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QSize
from serial_com_reader import PortReader, ReadPortData

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.port = None
        self.baud = None
        self.setWindowTitle('Arduino serial COM plotter')
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.plot_widget = pg.PlotWidget()
        self.layout.addWidget(self.plot_widget)
        self.plotData()
        
        self.setupGUI()
    
    def plotData(self):
        time = np.linspace(0,10, dtype=int)
        temp = np.linspace(25.0, 37.0, dtype=float)
        self.plot_widget.plot(time, temp, pen='w')
        styles = {"color": "#fff", "font-size": "20px"}
        self.plot_widget.setLabel("left", "y axis", **styles)
        self.plot_widget.setLabel("bottom", "time, ms", **styles)
  
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
        save_btn.clicked.connect(self.save_file)

        self.statusbar = self.statusBar()
        self.statusbar.setStyleSheet("font-size: 12pt; color: #888a85")
        self.statusbar.showMessage("Ready")

        self.portComboBox = QComboBox()
        self.updatePorts()
        self.toolbar.addWidget(self.portComboBox)

        self.baudRateComboBox = QComboBox()
        bauds = ['300 baud', '1200 baud', '2400 baud', '4800 baud', '9600 baud', '19200 baud', '38400 baud', 
        '57600 baud', '74880 baud', '115200 baud', '230400 baud', '250000 baud', '500000 baud', '1000000 baud', 
        '2000000 baud']
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
    
    def onBaudSelected(self, baudIndex):
        selectedBaud = self.baudRateComboBox.currentText()
        self.selectedBaudRate.setText(f"Selected baud rate: {selectedBaud}")
        self.baud = selectedBaud.split(" ")[0]

    def updatePorts(self):
        ports = PortReader.readAvailablePorts()
        print(type(ports))
        self.portComboBox.clear()
        self.portComboBox.addItems(ports)
        
    def onPortSelected(self, index):
        selectedPort = self.portComboBox.currentText()
        self.selectedPortLabel.setText(f"Selected Port: {selectedPort}")
        self.port = selectedPort.split(" ")[0][:-1]
        if self.port and self.baud:
            read = ReadPortData(self.port, 2000000)
            dataAr = read.readDataLines()
            print(dataAr)
    
    def save_file(self):
       fname,_ = QFileDialog.getSaveFileName(self, 'Save file', file_name,
                                    "CSV Files (*.csv *.tsv *.txt);;All Files (*.*)") 


def main():
    app = QApplication(sys.argv)
    window = MyMainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__=='__main__':
    main()
