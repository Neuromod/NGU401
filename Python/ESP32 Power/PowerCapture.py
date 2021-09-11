import pyvisa
import numpy
import scipy.interpolate as interpolate
import time


# Settings

resource = 'TCPIP::192.168.0.32::hislip0::INSTR'

filename = '../Data/ESP32 Power/power.npz'

t0 = .5       # Time to wait before sourcing voltage
t1 = 57.0     # Voltage sourced duration
t2 = .5       # Time after voltage source has been cut

v = 5          # Min voltage 
minI = -3      # Negative current
maxI = +3      # Positive current


# Code

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
arb += '{:f},{:f},{:f},{:f},0,'.format(0, maxI, minI, t0)
arb += '{:f},{:f},{:f},{:f},0,'.format(v, maxI, minI, t1)
arb += '{:f},{:f},{:f},{:f},0'.format(0, maxI, minI, t2)

ngu401.write('ARB:REP 1')                                            # 1 Repetition
ngu401.write('ARB:BEH:END OFF')                                      # Disable output at end of ARB
ngu401.write(arb)                                                    # Linear sweep vMin->vMax->vMin
ngu401.write('ARB:TRAN 1')                                           # Transfer the arbitrary table
ngu401.write('ARB:STAT 1')

duration = t0 + t1 + t2

vBuffer = numpy.zeros(int(510_000 * (duration + 1)), dtype = float)
iBuffer = numpy.zeros(int(510_000 * (duration + 1)), dtype = float)

idx = 0

ngu401.write('FLOG 1')
ngu401.query('*OPC?')
    
ngu401.write('OUTP 1')

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

numpy.savez(filename, vBuffer = vBuffer, iBuffer = iBuffer)
