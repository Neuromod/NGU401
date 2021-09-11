import time
import numpy
import pyvisa
import scipy.interpolate as interpolate
import matplotlib.pyplot as pyplot


# Settings

resource = 'TCPIP::192.168.0.32::hislip0::INSTR'
filename = '../Data/Regulation/i_0.npz'

i0              = -8       # Starting current
i1              = +8       # Ending current
minV            = -6       # Minimum voltage
maxV            = +6       # Maximum voltage
pulseNumber     = 33       # Number of pulses
pulseDuration   = 0.01     # duration of each pulse
pulseSeparation = 0.01     # separation between pulses


# Code

ngu401 = pyvisa.ResourceManager().open_resource(resource, timeout = 30_000)
ngu401.clear()

ngu401.write('*RST')
ngu401.query('*OPC?')

ngu401.write('SOUR:PRI CURR')

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

arb += '{:f},{:f},{:f},{:f},0,'.format(maxV, minV, 0.0001, pulseSeparation)

for i in numpy.linspace(i0, i1, pulseNumber):
    if i == 0:
        i = 0.0001
    arb += '{:f},{:f},{:f},{:f},0,'.format(maxV, minV, i,      pulseDuration)
    arb += '{:f},{:f},{:f},{:f},0,'.format(maxV, minV, 0.0001, pulseSeparation)

arb += '{:f},{:f},{:f},{:f},0'.format(maxV, minV, 0.001, pulseSeparation)

ngu401.write('ARB:CLE')                                      # Clear
ngu401.write('ARB:PRI:MODE CPM')                             # CPM mode
ngu401.write('ARB:REP 1')                                    # 1 Repetition
ngu401.write('ARB:BEH:END OFF')                              # Disable output at end of ARB
ngu401.write(arb)                                            # Linear sweep vMin->vMax->vMin
ngu401.write('ARB:TRAN 1')                                   # Transfer the arbitrary table
ngu401.write('ARB:STAT 1')

# Setup buffers
totalDuration = (pulseSeparation + (pulseDuration + pulseSeparation) * pulseNumber)

vBuffer = numpy.zeros(int(510_000 * (totalDuration + 3)), dtype = float)
iBuffer = numpy.zeros(int(510_000 * (totalDuration + 3)), dtype = float)

idx = 0

ngu401.write('FLOG 1')
ngu401.query('*OPC?')
    
ngu401.write('OUTP 1')

lastChunk = 3
startTime = 0

while True:
    stb = ngu401.read_stb()

    currentTime = time.time()

    if startTime != 0 and currentTime - startTime > totalDuration + .5:
        break

    if stb & 128:
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
        
        idx += len(v)

        if idx + len(data) > len(vBuffer) or lastChunk == 0:
            break

        if int(ngu401.query('OUTP?')) == 0:     # If output is off, get one last chunk of data before leaving loop
            lastChunk -= 1

        print('Remaining: {:.1f} s'.format(totalDuration - (currentTime - startTime)))

    if stb & 8:
        print('Lost data!')
        break;


vBuffer = vBuffer[:idx]
iBuffer = iBuffer[:idx]


idx = numpy.where(numpy.abs(iBuffer) > min(abs(i0), abs(i1)) / 2.)[0]
print(idx[0], idx[-1])

start = min(idx[0]  - 1_000, iBuffer.size)
end   = max(idx[-1] + 1_000, 0)

vBuffer = vBuffer[start : end]
iBuffer = iBuffer[start : end]

numpy.savez(filename, vBuffer = vBuffer, iBuffer = iBuffer)

pyplot.plot(vBuffer)
pyplot.plot(iBuffer)
pyplot.show()