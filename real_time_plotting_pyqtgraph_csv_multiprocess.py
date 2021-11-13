# Import libraries
from numpy import *
from multiprocessing import Process
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import pyqtgraph.exporters
import serial
import threading


filename = input('Enter filename to be saved along with extension: ')
item_code = input('Enter item code: ')

def arduino_setup():
    # Create object serial port
    portName = "COM5"                      # replace this port name by yours!
    baudrate = 9600
    ser = serial.Serial(portName,baudrate)
    try:
        val = ser.readline().decode('utf-8') # read line (single value) from the serial port
        val = val.rstrip().split(',')
        Xi = float(val[0])
        Yi = float(val[1])
        Zi = float(val[2])
    except Exception as e:
        print(e)
    return ser
    ### START QtApp #####

def plot_set():
    app = QtGui.QApplication([])            # you MUST do this once (initialize things)
    ####################

    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
    win = pg.GraphicsWindow(title="Bow testing Jig") # creates a window
    p = win.addPlot(title="Load vs Displacement ({})".format(item_code))  # creates empty space for the plot in the window
    p.showGrid(x=True, y=True)
    p.setLabel(axis='left', text='Load (lbs)')
    p.setLabel(axis='bottom', text='Displacement (inches)')
    curve1 = p.plot()                   # create an empty "plot" (a curve to plot)
    curve2 = p.plot()                   # create an empty "plot" (a curve to plot)
                                        # create an empty "plot" (a curve to plot)

    windowWidth = 500                       # width of the window displaying the curve
    Xm = linspace(0,0,windowWidth)          # create array that will contain the relevant time series     
    Ym = linspace(0,0,windowWidth)
    Zm = linspace(0,0,windowWidth)
    ptr = -windowWidth                      # set first x position
    t = ptr
# Realtime data plot. Each time this function is called, the data display is updated
def update(curve1, curve2, ptr, Xm, Ym, Zm, ser, Yi, Zi, p):
    # global curve1, curve2, ptr, Xm, Ym, Zm
    Xm[:-1] = Xm[1:]                      # shift data in the temporal mean 1 sample left
    Ym[:-1] = Ym[1:]
    Zm[:-1] = Zm[1:]
    value = ser.readline().decode('utf-8')# read line (single value) from the serial port
    value = value.rstrip().split(',')
    print(value)
    Xm[-1] = (float(value[0])+240-140)/25.4              # vector containing the instantaneous values
    Ym[-1] = float(value[1]) * 2.20462
    Zm[-1] = (float(value[2]) - 1.66) * 2.20462      
    print('disp = {}, Load1 = {}, Load2 = {}'.format(Xm[-1], Ym[-1], Zm[-1]))
    ptr += 1                                # update x position for displaying the curve             
    curve1.setData(y=Ym ,x=Xm, pen=None, symbol='o', symbolPen=None, symbolBrush=('r'), PointVisible=True, name='Axial Load (lbs)')                  # set the x acc curve with this data
    curve1.setPos(0,Yi)                # set x position in the graph to 0                    
    curve2.setData(y=Zm, x=Xm, pen=None, symbol='o', symbolPen=None, symbolBrush=('b'), PointVisible=True, name='Transverse Load (lbs)')                  # set the y acc curve with this data
    curve2.setPos(0,Zi)                # set x position in the graph to 0
    p.addLegend()
    p.setXRange(0, 30)
    p.setYRange(-20, 100)
                # set x position in the graph to 0
    # curve.setPos(ptr,0)                   
    QtGui.QApplication.processEvents()    # you MUST process the plot now
    csv = threading.Thread(target=to_csv, args=(filename, value[0], value[1], value[2]))
    csv.start()
    csv.join()

def to_csv(filename, x, y, z):
    data = x + ',' + y + ',' + z + '\n'
    with open('./Data/{}'.format(filename), 'a+') as f:
        f.write(data)
        f.close()
### MAIN PROGRAM #####    
# this is a brutal infinite loop calling your realtime data plot
plot_set()
while True:
    try:
        try:
            update()
        except Exception as e:
            print(e)
            if e is KeyboardInterrupt:
                break
            else:
                continue
    except KeyboardInterrupt as e:
        ser.close()
        exporter = pg.exporters.ImageExporter(p)
        exporter.export('./plots/{}.png'.format(item_code))
        print('File saved successfully')
        break

### END QtApp ####
pg.QtGui.QApplication.exec_() # you MUST put this at the end
##################