from PyQt5 import QtWidgets, uic, QtCore, QtGui
from pyqtgraph.functions import colorStr
import pyqtgraph.exporters
from new_video_window import Ui_BowAnalyzer
from startup_window import Ui_StartupWindow
from plot_window import Ui_PlotWindow
# from plotting import plot
import cv2
from numpy import *
from datetime import date as dt
import time
import serial
import serial.tools.list_ports
import threading
import sys

class startup(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.startup_ui = Ui_StartupWindow()
        self.startup_ui.setupUi(self)

        self.startup_ui.submit_btn.clicked.connect(self.exp_name)
        self.startup_ui.submit_btn.clicked.connect(self.open_camerascreen)

    def exp_name(self):
        item_code = str(self.startup_ui.item_code.text())
        part = str(self.startup_ui.cam_no.text())
        return item_code, part

    def open_camerascreen(self):
        global itemcode, part, filename
        itemcode, part = self.exp_name()
        filename = str(dt.today()) + '_' + itemcode + '-' + part
        self.camscreen = CameraScreen()
        self.camscreen.show()
        self.close()

class CameraScreen(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cam_ui = Ui_BowAnalyzer()
        self.cam_ui.setupUi(self)

        self.worker1 = worker1()
        self.worker1.start()
        self.worker1.imageupdate.connect(self.ImageUpdateSlot)

        self.worker2 = worker2()
        self.worker2.start()
        self.worker2.imageupdate_2.connect(self.ImageUpdateSlot_2)

        self.cam_ui.start_plot.clicked.connect(self.open_plot)

        self.cam_ui.stop_btn.clicked.connect(self.stop_feed)
        self.cam_ui.stop_btn.clicked.connect(self.stop_feed_2)

    def ImageUpdateSlot(self, Image):
        self.cam_ui.cam1_lbl.setPixmap(QtGui.QPixmap.fromImage(Image))

    def ImageUpdateSlot_2(self, Image):
        self.cam_ui.cam2_lbl.setPixmap(QtGui.QPixmap.fromImage(Image))
    
    def stop_feed(self):
        self.worker1.stop()
        self.cam_ui.cam1_lbl.setStyleSheet('background-color: black')

    def stop_feed_2(self):
        self.worker2.stop()
        self.cam_ui.cam2_lbl.setStyleSheet('background-color: black')

    def open_plot(self):
        self.plotscreen = plot_window()
        self.plotscreen.show()
        # self.work3 = worker3()
        # self.work3.start()
        # self.work3.data_signal.connect(self.update)
        # self.plotscreen.execute()

class arduino_data():
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print
        self.port = self.find_port()
        self.BaudRate = 9600
        self.ser = serial.Serial(self.port,self.BaudRate)
    def checkData(self):
        try:
            print('Reading for proper values from sensors...............')
            val = self.ser.readline().decode('utf-8') # read line (single value) from the serial port
            val = val.rstrip().split(',')
            Xi = float(val[0])
            Yi = float(val[1])
            Zi = float(val[2])
            return Xi, Yi, Zi
            # print('CHECKDATA.................',self.Xi, self.Yi, self.Zi)
        except Exception as e:
            print(e)

    def get_data(self):
        print('Creating plot instance..........')
        value = self.ser.readline().decode('utf-8')     # read line (single value) from the serial port
        value = value.rstrip().split(',')
        self.windowWidth = 500                       # width of the window displaying the curve
        Xm = linspace(0,0,self.windowWidth)          # create array that will contain the relevant time series     
        Ym = linspace(0,0,self.windowWidth)
        Zm = linspace(0,0,self.windowWidth)
        self.ptr = -self.windowWidth
        # print('GETDATA........LINSPACE.......',Xm, self.Ym, Zm)
        return Xm, Ym, Zm
    def stream_data(self, Xm, Ym, Zm):
        Xm[:-1] = Xm[1:]                      # shift data in the temporal mean 1 sample left
        Ym[:-1] = Ym[1:]
        Zm[:-1] = Zm[1:]
        self.value = self.ser.readline().decode('utf-8')# read line (single value) from the serial port
        self.value = self.value.rstrip().split(',')
        print('Update self.value',self.value)
        Xm[-1] = (float(self.value[0])+240-140)/25.4              # vector containing the instantaneous self.values
        Ym[-1] = float(self.value[1]) * 2.20462
        Zm[-1] = (float(self.value[2]) - 1.66) * 2.20462 
        # self.data_signal.emit(self.Ym[-1], self.Ym[-1], Zm[-1])
        print('disp = {}, Load1 = {}, Load2 = {}'.format(Xm[-1], Ym[-1], Zm[-1]))
        self.ptr += 1
        return Xm, Ym, Zm

    def to_csv(self, x, y, z):
        data = str(x) + ',' + str(y) + ',' + str(z) + '\n'
        with open('./Data/{}.csv'.format(filename), 'a+') as f:
            f.write(data)
            f.close()

    def close_gateway(self):
        print('CLOSING GATEWAY..........')
        self.ser.close()
    
    def find_port(self):
        print('Searching for Port.......')
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            port = p.device
        print('Port found: ', port)
        return port

class plot_window(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plot_ui = Ui_PlotWindow()
        self.plot_ui.setupUi(self)

        self.plot_ui.savebtn.clicked.connect(self.save_btn)
        self.plot_ui.btn_strt.clicked.connect(self.stop_btn)

        self.plot_check = True

        self.ard_Data = arduino_data()
        styles_lbl = {'color':'k', 'font-size': '16px'}
        styles_title = {'color':'k', 'size': '20px'}
        font = QtGui.QFont()
        font.setPixelSize(14)
        self.plot_ui.plot_view.setBackground(background= (255,255,255))
        self.plt_item = self.plot_ui.plot_view.getPlotItem()
        self.plt_item.showGrid(x=True, y=True)
        self.plt_item.setTitle(title='Load vs Displacement curve for {}'.format(filename), **styles_title)
        self.plt_item.addLegend()
        self.plot_ui.plot_view.getAxis('left').setStyle(tickFont = font)
        self.plot_ui.plot_view.getAxis('bottom').setStyle(tickFont = font)
        self.plot_ui.plot_view.getAxis('left').setTextPen('k')
        self.plot_ui.plot_view.getAxis('bottom').setTextPen('k')
        self.plot_ui.plot_view.setLabel('left', 'Load (lbs)', **styles_lbl)
        self.plot_ui.plot_view.setLabel('bottom', 'Displacement (Inches)', **styles_lbl)

    def update(self, Xm, Ym, Zm, Yi, Zi):       
        self.curve1 = self.plt_item.plot()
        self.curve2 = self.plt_item.plot()      
        self.curve1.setData(y=Ym ,x=Xm, pen=None, symbol='o', symbolPen=None, symbolBrush=('r'), PointVisible=True, name='Axial Load (lbs)')                  # set the x acc curve with this data
        self.curve1.setPos(0,Yi)                # set x position in the graph to 0                    
        self.curve2.setData(y=Zm, x=Xm, pen=None, symbol='o', symbolPen=None, symbolBrush=('b'), PointVisible=True, name='Tension (lbs)')                  # set the y acc curve with this data
        self.curve2.setPos(0,Zi)                # set x position in the graph to 0
        self.plt_item.setXRange(0,40)
        self.plt_item.setYRange(-30, 150)
        self.plt_item.addLegend()
        self.plot_ui.plot_view.setXRange(0,30)
        self.plot_ui.plot_view.setYRange(-20, 100)
                    # set x position in the graph to 0
        # curve.setPos(ptr,0)                   
        QtGui.QApplication.processEvents()    # you MUST process the plot now
        # csv = threading.Thread(target=self.to_csv, args=(Xm, Ym, Zm))
        # csv.start()
        # csv.join()
 
    '''def execute(self):
        # self.port = self.ard_Data.find_port()
        try:
            _, Yi, Zi = self.ard_Data.checkData()
        except Exception as e:
            print(e)
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Critical)
            msg.setText("Error!!")
            msg.setInformativeText('More information: {}'.format(e))
            msg.setWindowTitle("Error")
            msg.exec_()
            pass
        A,B,C = self.ard_Data.get_data()
        print('Please wait while your data is getting fetched..........')
        time.sleep(5)
        while True:
            try:
                Xm, Ym, Zm = self.ard_Data.stream_data(A,B,C)
                self.update(Xm=Xm, Ym=Ym, Yi=Yi, Zm=Zm, Zi=Zi)
                csv = threading.Thread(target=self.ard_Data.to_csv, args=(Xm, Ym, Zm))
                csv.start()
                csv.join()
            except Exception as e:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Error!!")
                msg.setInformativeText('More information: {}'.format(e))
                msg.setWindowTitle("Error")
                msg.exec_()
                break'''
            
    def stop_btn(self):
        if self.plot_check:
            self.plot_check = False
            self.plot_ui.btn_strt.setText('Stop')
        else:
            self.plot_ui.btn_strt.setText('Start')
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Information)
            msg.setText("Closing Arduino Serial port!!")
            self.ard_Data.close_gateway()
            msg.setWindowTitle("Port Closed!!")
            msg.exec_()

    def save_btn(self):
        exporter = pyqtgraph.exporters.ImageExporter(self.plt_item)
        exporter.export('./plots/{}.png'.format(filename))
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)
        msg.setText("Files saved successfully!!")
        msg.setWindowTitle("Success!!")
        msg.exec_()


class worker1(QtCore.QThread):
    imageupdate = QtCore.pyqtSignal(QtGui.QImage)
    def run(self):
        self.threadactive = True
        capture = cv2.VideoCapture(1)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        save_cam1 = cv2.VideoWriter('.\Recordings\{}.avi'.format('REC-CAM-1'+filename),fourcc,20.0,(640,480))
        while self.threadactive:
            ret, frame = capture.read()
            if ret:
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                flipped_image = cv2.flip(image, 1)
                qt_image = QtGui.QImage(flipped_image.data, flipped_image.shape[1], flipped_image.shape[0], QtGui.QImage.Format_RGB888)
                pic = qt_image.scaled(640, 480, QtCore.Qt.KeepAspectRatio)
                self.imageupdate.emit(pic)
                save_cam1.write(flipped_image)

    def stop(self):
        self.threadactive = False
        self.quit()

class worker2(QtCore.QThread):
    imageupdate_2 = QtCore.pyqtSignal(QtGui.QImage)
    def run(self):
        self.threadactive_2 = True
        capture_2 = cv2.VideoCapture(2)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        save_cam2 = cv2.VideoWriter('.\Recordings\{}.avi'.format('REC-CAM-2'+filename),fourcc,20.0,(640,480))
        while self.threadactive_2:
            ret_2, frame_2 = capture_2.read()
            if ret_2:
                image_2 = cv2.cvtColor(frame_2, cv2.COLOR_BGR2RGB)
                flipped_image_2 = cv2.flip(image_2, 1)
                qt_image_2 = QtGui.QImage(flipped_image_2.data, flipped_image_2.shape[1], flipped_image_2.shape[0], QtGui.QImage.Format_RGB888)
                pic_2 = qt_image_2.scaled(640, 480, QtCore.Qt.KeepAspectRatio)
                self.imageupdate_2.emit(pic_2)
                save_cam2.write(flipped_image_2)
    
    def stop(self):
        self.threadactive_2 = False
        self.quit()

class worker3(QtCore.QThread):
    data_signal = QtCore.pyqtSignal(float,float,float, float, float)
    print('Signal Created: ', data_signal)
    def send_signal(self):
        self.thread_active = True
        self.data = arduino_data()
        self.plt = plot_window()
        print('Thread active...., Checking for data')
        # self.data.port = self.data.find_port()
        _,yi,zi = self.data.checkData()
        x,y,z = self.data.get_data()
        while self.thread_active:
            X, Y, Z = self.data.stream_data(Xm=x, Ym=y, Zm=z)
            self.plt.update(Xm=X, Ym=Y, Zm=Z, Yi=yi, Zi=zi)
            self.data_signal.emit(X,Y,Z,yi,zi)


if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    details_ui = startup()
    details_ui.show()
    sys.exit(app.exec_())