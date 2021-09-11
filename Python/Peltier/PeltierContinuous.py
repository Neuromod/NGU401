import pyvisa
import numpy
import time
import matplotlib.pyplot as pyplot

import Temperature


# Settings

resource        = 'TCPIP::192.168.0.32::hislip0::INSTR'
temperaturePort = 'com5'

v0   = -5                  # Initial sweep voltage
v1   = +5                  # Final swepp voltage

stepNumber   = 21          # Number of steps
stepDuration = (180, 120)  # Time duration of the first and the remaining steps

filename = '../Data/peltier/Continuous.npz'


# Code
temperature = Temperature.Temperature(temperaturePort)

ngu401 = pyvisa.ResourceManager().open_resource(resource, timeout = 30_000)
ngu401.clear()

ngu401.write('*RST')
ngu401.query('*OPC?')
ngu401.write('SOUR:VOLT 0')
ngu401.write('SOUR:CURR:NEG MIN')
ngu401.write('SOUR:CURR MAX')
ngu401.write('SENS:VOLT:RANG:AUTO 1')
ngu401.write('SENS:CURR:RANG:AUTO 1')
ngu401.write('SENS:NPLC 1')
ngu401.write('OUTP 1')
ngu401.query('*OPC?')

vBuffer = []
iBuffer = []
tBuffer = []
tmBuffer = []

voltage = numpy.linspace(v0, v1, stepNumber)

startTime = 0

for index in range(voltage.size):
    ngu401.write('SOUR:VOLT {:f}'.format(voltage[index]))
    ngu401.query('*OPC?')
    time.sleep(1)

    stepTime = time.time()

    while True:
        query = ngu401.query('READ?')
        ngu401.query('*OPC?')

        v, i = [float(x) for x in query.split(',')]
        
        t = numpy.array(temperature.read()).mean()
        
        currentTime = time.time()

        if startTime == 0:
            startTime = currentTime

        print('[{:.1f} s] Voltage: {:.3f}, Current {:.3f}, Power: {:.3f} W, Temperature {:.3f} ºC'.format(currentTime - startTime, v, i, v * i, t))

        vBuffer.append(v)
        iBuffer.append(i)
        tBuffer.append(t)
        tmBuffer.append(currentTime - startTime)

        if (index == 0 and currentTime - stepTime > stepDuration[0]) or (index != 0 and currentTime - stepTime > stepDuration[1]):
            break;

        time.sleep(0.25)

ngu401.write('OUTP 0')

numpy.savez(filename, vBuffer = vBuffer, iBuffer = iBuffer, tBuffer = tBuffer, tmBuffer = tmBuffer)
