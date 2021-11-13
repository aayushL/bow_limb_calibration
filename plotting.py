from numpy import *
from multiprocessing import Process
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.exporters
import serial
import serial.tools.list_ports
import threading

class plot:
    def __init__(self, filename, BaudRate):
        # self.filename = input("Enter file name: ")
        self.Filename = filename
        print(self.Filename)
        self.itemcode = filename
        self.portName = ''                   # replace this port name by yours!
        self.baudrate = BaudRate
        self.windowWidth = 500                       # width of the window displaying the curve
        self.Xm = linspace(0,0,self.windowWidth)          # create array that will contain the relevant time series     
        self.Ym = linspace(0,0,self.windowWidth)
        self.Zm = linspace(0,0,self.windowWidth)
        self.ptr = -self.windowWidth
        self.app = QtGui.QApplication([])
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.win = pg.GraphicsWindow(title="Bow testing Jig")
        self.p = self.win.addPlot(title="Load vs Displacement ({})".format(self.itemcode))

    def check_data(self):
        try:
            print('Reading for proper values from sensor...')
            self.ser = serial.Serial(self.portName,self.baudrate)
            val = self.ser.readline().decode('utf-8') # read line (single value) from the serial port
            val = val.rstrip().split(',')
            self.Xi = float(val[0])
            self.Yi = float(val[1])
            self.Zi = float(val[2])
            print(self.Xi, self.Yi, self.Zi)
            filename = self.Filename
            csv = threading.Thread(target=self.to_csv, args=(val[0], val[1], val[2]))
            csv.start()
            csv.join()
        except Exception as e:
            print(e)
    
    def get_data(self):
        self.Xm[:-1] = self.Xm[1:]                      # shift data in the temporal mean 1 sample left
        self.Ym[:-1] = self.Ym[1:]
        self.Zm[:-1] = self.Zm[1:]
        value = self.ser.readline().decode('utf-8')     # read line (single value) from the serial port
        value = value.rstrip().split(',')
        # app = QtGui.QApplication([])   

        # pg.setConfigOption('background', 'w')
        # pg.setConfigOption('foreground', 'k')
        
        # win = pg.GraphicsWindow(title="Bow testing Jig") # creates a window
        # p = win.addPlot(title="Load vs Displacement ({})".format(self.itemcode))  # creates empty space for the plot in the window
        self.p.showGrid(x=True, y=True)
        self.p.setLabel(axis='left', text='Load (lbs)')
        self.p.setLabel(axis='bottom', text='Displacement (inches)')
        # self.graph = object.addPlot(title="Load vs Displacement ({})".format(self.itemcode))
        self.p.showGrid(x=True, y=True)
        # self.graph.setLabel(axis='left', text='Load (lbs)')
        # self.graph.setLabel(axis='bottom', text='Displacement (inches)')

        self.curve1 = self.p.plot()
        self.curve2 = self.p.plot()

        self.windowWidth = 500                       # width of the window displaying the curve
        self.Xm = linspace(0,0,self.windowWidth)          # create array that will contain the relevant time series     
        self.Ym = linspace(0,0,self.windowWidth)
        self.Zm = linspace(0,0,self.windowWidth)
        self.ptr = -self.windowWidth
        return self.Xm, self.Ym, self.Zm, self.p

    def update(self):
        # global curve1, curve2, ptr, Xm, Ym, Zm    
        self.Xm[:-1] = self.Xm[1:]                      # shift data in the temporal mean 1 sample left
        self.Ym[:-1] = self.Ym[1:]
        self.Zm[:-1] = self.Zm[1:]
        value = self.ser.readline().decode('utf-8')# read line (single value) from the serial port
        value = value.rstrip().split(',')
        print(value)
        self.Xm[-1] = (float(value[0])+240-140)/25.4              # vector containing the instantaneous values
        self.Ym[-1] = float(value[1]) * 2.20462
        self.Zm[-1] = (float(value[2]) - 1.66) * 2.20462      
        print('disp = {}, Load1 = {}, Load2 = {}'.format(self.Ym[-1], self.Ym[-1], self.Zm[-1]))
        self.ptr += 1                                # update x position for displaying the curve             
        self.curve1.setData(y=self.Ym ,x=self.Xm, pen=None, symbol='o', symbolPen=None, symbolBrush=('r'), PointVisible=True, name='Axial Load (lbs)')                  # set the x acc curve with this data
        self.curve1.setPos(0,self.Yi)                # set x position in the graph to 0                    
        self.curve2.setData(y=self.Zm, x=self.Xm, pen=None, symbol='o', symbolPen=None, symbolBrush=('b'), PointVisible=True, name='Tension (lbs)')                  # set the y acc curve with this data
        self.curve2.setPos(0,self.Zi)                # set x position in the graph to 0
        self.p.addLegend()
        self.p.setXRange(0, 30)
        self.p.setYRange(-20, 100)
                    # set x position in the graph to 0
        # curve.setPos(ptr,0)                   
        QtGui.QApplication.processEvents()    # you MUST process the plot now
        filename = self.Filename
        csv = threading.Thread(target=self.to_csv, args=(value[0], value[1], value[2]))
        csv.start()
        csv.join()

    def to_csv(self, x, y, z):
        data = x + ',' + y + ',' + z + '\n'
        with open('./Data/{}.csv'.format(self.Filename), 'a+') as f:
            f.write(data)
            f.close()

    def close_gateway(self):
        self.ser.close()
    
    def find_port(self):
        print('Searching for Port.......')
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            port = p.device
        print('Port found: ', port)
        return port

def execute(Filename):
    filename = Filename
    plt = plot(BaudRate=9600, filename=filename)
    port = plt.find_port()
    plt.portName = port
    plt.check_data()
    _,_,_,p = plt.get_data()
    while True:
        try:
            try:
                plt.update()
            except Exception as e:
                print(e)
                if e is KeyboardInterrupt:
                    break
                else:
                    continue
        except KeyboardInterrupt as e:
            plt.close_gateway()
            exporter = pg.exporters.ImageExporter(p)
            exporter.export('./plots/{}.png'.format(plt.itemcode))
            print('File saved successfully')
            break

