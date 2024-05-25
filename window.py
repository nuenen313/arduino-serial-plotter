import sys
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget,
                             QToolButton, QTableWidget, QVBoxLayout,
                             QTableWidgetItem, QFileDialog, QStyle)
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QSize

class MyMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
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

        open_icon = self.style().standardIcon(QStyle.SP_DialogOpenButton)
        open_btn = QToolButton(text = "Open", icon = open_icon)
        open_btn.setStyleSheet("QToolButton:hover {background: #D7DAE0;}")
        self.toolbar.addWidget(open_btn)
        # open_btn.clicked.connect(self.open_file)

        save_icon = self.style().standardIcon(QStyle.SP_DialogSaveButton)
        save_btn = QToolButton(text = "Save", icon = save_icon)
        save_btn.setStyleSheet("QToolButton:hover {background: #D7DAE0;}")
        self.toolbar.addWidget(save_btn)
        save_btn.clicked.connect(self.save_file)

        self.statusbar = self.statusBar()
        self.statusbar.setStyleSheet("font-size: 12pt; color: #888a85")
        self.statusbar.showMessage("Ready")
    
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
