import pyvisa
import numpy
import time

import Temperature


# Settings

resource        = 'TCPIP::192.168.0.32::hislip0::INSTR'
temperaturePort = 'com5'

v    = 5           # Voltage
minI = -3          # Min current
maxI = +3          # Max current

stepNumber   = 21          # Number of steps
stepDuration = (180, 120)  # Time duration of the first and the remaining steps

period     = 0.01

filename = '../Data/Peltier/pwm.npz'


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

ngu401.write('FLOG:TARG SCPI')                               # FastLog
ngu401.write('FLOG:SRAT S500K')                              # 500 ks/s

dcBuffer = []
pBuffer  = []
tBuffer  = []
tmBuffer = []

dutyCycle  = numpy.linspace(-1.0, 1.0, stepNumber)       # Negative duty cycle indicates that the PWM voltage is negative

startTime = 0

for index in range(dutyCycle.size):
    # Clear events
    ngu401.query('STAT:OPER:INST:ISUM1:EVEN?')
    ngu401.query('STAT:OPER:INST:EVEN?')
    ngu401.query('STAT:OPER:EVEN?')

    ngu401.query('STAT:QUES:INST:ISUM1:EVEN?')
    ngu401.query('STAT:QUES:INST:EVEN?')
    ngu401.query('STAT:QUES:EVEN?')

    if dutyCycle[index] > 0:
        vOutput = v
    else:
        vOutput = -v

    onTime  = period * abs(dutyCycle[index])
    offTime = period * (1. - abs(dutyCycle[index]))

    arb = 'ARB:DATA '
    
    if onTime != 0:
        arb += '{:f},{:f},{:f},{:f},0'.format(vOutput, maxI, minI, onTime)
    
    if onTime != 0 and offTime != 0:
        arb += ','
    
    if offTime != 0:
        arb += '{:f},{:f},{:f},{:f},0'.format(0, maxI, minI, offTime)

    ngu401.write('ARB:REP 0')                                    # Repeat indefinitely
    ngu401.write('ARB:BEH:END OFF')                              # Disable output at end of ARB
    ngu401.write(arb)                                            # Linear sweep vMin->vMax->vMin
    ngu401.write('ARB:TRAN 1')                                   # Transfer the arbitrary table
    ngu401.write('ARB:STAT 1')

    ngu401.write('FLOG 1')
    ngu401.query('*OPC?')
    
    ngu401.write('OUTP 1')

    stepTime = time.time()

    while True:
        stb = ngu401.read_stb()

        if stb & 128:
            data = ngu401.query_binary_values('FLOG:DATA?', datatype = 'f', data_points = 50)
        
            # Clear event bits
            ngu401.query('STAT:OPER:EVEN?')
            ngu401.query('STAT:OPER:INST:EVEN?')
            ngu401.query('STAT:OPER:INST:ISUM1:EVEN?')

            currentTime = time.time()

            if startTime == 0:
                startTime = currentTime

            p = (numpy.array(data[0::2]) * numpy.array(data[1::2])).mean()
            t = numpy.array(temperature.read()).mean()

            pBuffer.append(p)
            tBuffer.append(t)
            dcBuffer.append(dutyCycle[index])
            tmBuffer.append(currentTime - startTime)
            
            print('[{:.1f} s] Duty Cycle: {:.3f}, Power: {:.3f} W, Temperature {:.3f} ºC'.format(currentTime - startTime, dutyCycle[index], p, t))

            if (index == 0 and currentTime - stepTime > stepDuration[0]) or (index != 0 and currentTime - stepTime > stepDuration[1]):
                break;

        if stb & 8:
            print('Lost data!')
            break;

    ngu401.write('FLOG 0')
    ngu401.query('*OPC?')

    ngu401.write('OUTP 0')

numpy.savez(filename, dcBuffer = dcBuffer, pBuffer = pBuffer, tBuffer = tBuffer, tmBuffer = tmBuffer)
