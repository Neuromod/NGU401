import pyvisa
import time
import numpy
import Metric


# Settings

k2450Resource  = 'TCPIP::192.168.0.31::inst0::INSTR'
ngu401Resource = 'TCPIP::192.168.0.32::hislip0::INSTR'

vRange = (6, 20)
iRange = (25E-6, 2.5)

vLimit = 4.95
iLimit = 1.0

vSteps = 50
iSteps = 50

measurementDelay = 2

filename = '../Data/DC-DC Converter/DCM2.npz'


# Code

resourceManager = pyvisa.ResourceManager()

k2450  = resourceManager.open_resource(k2450Resource, timeout = 30_000)
ngu401 = resourceManager.open_resource(ngu401Resource, timeout = 30_000)

k2450.clear()
ngu401.clear()

# Set the Source

k2450.write('reset()')
k2450.write('smu.measure.sense = smu.SENSE_4WIRE')
k2450.write('smu.source.highc = smu.ON')
k2450.write('smu.measure.filter.count = 10')
k2450.write('smu.measure.filter.enable = smu.ON')
k2450.write('smu.source.ilimit.level = 1.05')
k2450.write('smu.measure.autorangelow = 1E-4')
k2450.write('smu.source.level = 0')
k2450.write('smu.source.output = smu.ON')

# Set the load

ngu401.write('*RST')
ngu401.write('SOUR:PRI CURR')
ngu401.query('*OPC?')
ngu401.write('SOUR:VOLT:RANG 6')
ngu401.query('*OPC?')
ngu401.write('SOUR:VOLT:NEG 0')
ngu401.write('SOUR:VOLT 5.1')
ngu401.query('*OPC?')
ngu401.write('SOUR:CURR:RANG 0.001')
time.sleep(.1)
ngu401.write('SOUR:CURR -25E-6')
ngu401.write('SENS:CURR:RANG:AUTO 1')
ngu401.write('SENS:VOLT:RANG:AUTO 1')
ngu401.write('SENS:NPLC 10')
ngu401.query('*OPC?')
ngu401.write('OUTP:STAT 1')
ngu401.query('*OPC?')

# Initialize arrays

vTable = numpy.linspace(vRange[0], vRange[1], vSteps)
iTable = iRange[0] * numpy.power(numpy.power(iRange[1] / iRange[0], 1. / (iSteps - 1.)), numpy.arange(iSteps))

data = numpy.zeros((vTable.size, iTable.size, 4))


for iIdx in range(iTable.size):
    iOut = iTable[iIdx]

    # Set output current

    ngu401.write('SOUR:CURR:RANG {:f}'.format(iOut))
    time.sleep(.2)
    ngu401.write('SOUR:CURR {:f}'.format(-iOut))

    for vIdx in reversed(range(vTable.size)):
        vIn = vTable[vIdx]
 
        # Set input Voltage

        k2450.write('smu.source.level = {:f}'.format(vIn))
        
        time.sleep(measurementDelay)

        # Read input

        k2450.write('smu.measure.read()')

        vIn = float(k2450.query('print(defbuffer1.sourcevalues[defbuffer1.n])'))
        iIn = float(k2450.query('print(defbuffer1[defbuffer1.n])'))

        # Read Output

        query = ngu401.query('READ?')
        ngu401.query('*OPC?')
        
        vOut, iOut = [float(x) for x in query.split(',')]
        iOut = -iOut

        # Print
        
        vin  = Metric.metric(vIn, 3, 'V')
        inn  = Metric.metric(iIn, 3, 'A')
        pin  = Metric.metric(vIn * iIn, 3, 'W')
        vout = Metric.metric(vOut, 3, 'V')
        iout = Metric.metric(iOut, 3, 'A')
        pout = Metric.metric(vOut * iOut, 3, 'W')

        print('Input: {:s}, {:s}, {:s}, Output: {:s}, {:s}, {:s}, Effiency: {:.1f}%'.format(vin, inn, pin, vout, iout, pout, 100 * (vOut * iOut) / (vIn * iIn)))

        if vOut < vLimit or iIn > iLimit:
            break

        data[vIdx, iIdx, 0] = vIn
        data[vIdx, iIdx, 1] = iIn
        data[vIdx, iIdx, 2] = vOut
        data[vIdx, iIdx, 3] = iOut

ngu401.write('OUTP:STAT 0')
k2450.write('smu.source.output = smu.OFF')

numpy.savez(filename, data = data, vTable = vTable, iTable = iTable)