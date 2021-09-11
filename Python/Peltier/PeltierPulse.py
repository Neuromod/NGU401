import pyvisa
import numpy
import scipy.interpolate as interpolate
import time

import Temperature


# Settings

resource        = 'TCPIP::192.168.0.32::hislip0::INSTR'
temperaturePort = 'com5'

minV = -5          # Min voltage 
maxV = +5          # Max voltage
minI = -3          # Min current
maxI = +3          # Max current

stepNumber   = 21          # Number of steps
stepDuration = (0.001, 1)  # duration of the pulse and the time between pulses


filename = '../Data/Peltier/pulse.npz'


# Code

temperature = Temperature.Temperature(temperaturePort)

ngu401 = pyvisa.ResourceManager().open_resource(resource, timeout = 30_000)
ngu401.clear()

ngu401.write('*RST')
ngu401.query('*OPC?')

ngu401.write('STAT:OPER:NTR 0')
ngu401.write('STAT:OPER:PTR 8192')
ngu401.write('STAT:OPER:ENABLE 8192')                        # instrument operation summary
ngu401.write('STAT:OPER:INST:NTR 0')
ngu401.write('STAT:OPER:INST:PTR 2')
ngu401.write('STAT:OPER:INST:ENABLE 2')                      # Channel 1
ngu401.write('STAT:OPER:INST:ISUM1:NTR 0')
ngu401.write('STAT:OPER:INST:ISUM1:PTR 4096') 
ngu401.write('STAT:OPER:INST:ISUM1:ENABLE 4096')             # Fastlog data available

ngu401.write('STAT:QUES:NTR 0')
ngu401.write('STAT:QUES:PTR 8192')
ngu401.write('STAT:QUES:ENABLE 8192')                        # Instrument questionable summary
ngu401.write('STAT:QUES:INST:NTR 0')
ngu401.write('STAT:QUES:INST:PTR 2')
ngu401.write('STAT:QUES:INST:ENABLE 2')                      # Channel 1
ngu401.write('STAT:QUES:INST:ISUM1:NTR 0')
ngu401.write('STAT:QUES:INST:ISUM1:PTR 2048')
ngu401.write('STAT:QUES:INST:ISUM1:ENABLE 2048')             # Fastlog data skipped

# Clear events
ngu401.query('STAT:OPER:INST:ISUM1:EVEN?')
ngu401.query('STAT:OPER:INST:EVEN?')
ngu401.query('STAT:OPER:EVEN?')

ngu401.query('STAT:QUES:INST:ISUM1:EVEN?')
ngu401.query('STAT:QUES:INST:EVEN?')
ngu401.query('STAT:QUES:EVEN?')

ngu401.write('FLOG:TARG SCPI')                               # FastLog
ngu401.write('FLOG:SRAT S500K')                              # 500 ks/s

arb = 'ARB:DATA '
arb += '{:f},{:f},{:f},{:f},0,'.format(0, maxI, minI, stepDuration[1])

for i, v in enumerate(numpy.linspace(minV, maxV, stepNumber)):
    arb += '{:f},{:f},{:f},{:f},0,'.format(v, maxI, minI, stepDuration[0])
    arb += '{:f},{:f},{:f},{:f},0'.format(0, maxI, minI, stepDuration[1])

    if i + 1 < stepNumber:
        arb += ','

ngu401.write('ARB:REP 1')                                            # 1 Repetition
ngu401.write('ARB:BEH:END OFF')                                      # Disable output at end of ARB
ngu401.write(arb)                                                    # Linear sweep vMin->vMax->vMin
ngu401.write('ARB:TRAN 1')                                           # Transfer the arbitrary table
ngu401.write('ARB:STAT 1')

# Setup buffers
duration = stepDuration[1] + (stepDuration[0] + stepDuration[1]) * stepNumber

vBuffer = numpy.zeros(int(510_000 * (duration + 1)), dtype = float)
iBuffer = numpy.zeros(int(510_000 * (duration + 1)), dtype = float)
tBuffer = []

idx = 0

ngu401.write('FLOG 1')
ngu401.query('*OPC?')
    
ngu401.write('OUTP 1')

temperature.read() # Discard all

lastChunk = False
startTime = 0

while True:
    stb = ngu401.read_stb()

    if stb & 128:
        currentTime = time.time()
        
        if  startTime == 0:
            startTime = currentTime

        data = ngu401.query_binary_values('FLOG:DATA?', datatype = 'f', data_points = 50)
        
        # Clear event bits
        ngu401.query('STAT:OPER:EVEN?')
        ngu401.query('STAT:OPER:INST:EVEN?')
        ngu401.query('STAT:OPER:INST:ISUM1:EVEN?')

        v = data[0::2]
        i = data[1::2]
        
        vBuffer[idx : idx + len(v)] = v
        iBuffer[idx : idx + len(i)] = i
        tBuffer.extend(temperature.read())
        
        idx += len(v)

        if idx + len(data) > len(vBuffer) or lastChunk:
            break

        if int(ngu401.query('OUTP?')) == 0:     # If output is off, get one last chunk of data before leaving loop
            lastChunk = True

        print('Remaining: {:.1f} s'.format(duration - (currentTime - startTime)))

    if stb & 8:
        print('Lost data!')
        break;

rate = (idx - len(v)) / (currentTime - startTime)

vBuffer = vBuffer[:idx]
iBuffer = iBuffer[:idx]
tmBuffer = numpy.arange(vBuffer.size) / rate

f = interpolate.interp1d(numpy.linspace(0, tmBuffer[-1], len(tBuffer)), tBuffer, kind = 'linear')
tBuffer = f(tmBuffer)

numpy.savez(filename, vBuffer = vBuffer, iBuffer = iBuffer, tBuffer = tBuffer, tmBuffer = tmBuffer)
