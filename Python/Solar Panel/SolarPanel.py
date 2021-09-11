import pyvisa
import time
import numpy


# Settings

resource = 'tcpip0::192.168.0.32::hislip0::instr'
step = 0.01


# Code

ngu = pyvisa.ResourceManager().open_resource(resource, timeout = 30_000)
ngu.clear()

ngu.write('*RST')                           # Reset instrument
ngu.write('SOUR:VOLT 0')                    # Set voltage to 0
ngu.write('SOUR:CURR:NEG -1')               # Set negative current limit to -1
ngu.write('SOUR:CURR MIN')                  # Set positive current to the minimum (0.001 mA)
ngu.write('SENS:VOLT:RANG:AUTO 1')          # Set voltage readback range to auto
ngu.write('SENS:CURR:RANG:AUTO 1')          # Set current readback range to auto
ngu.write('SENS:NPLC 1')                    # Set the number of power line cycles to 1
ngu.write('OUTP 1')                         # Turn on the output
ngu.query('*OPC?')                          # Wait for previous operations to complete

source = 0
data = []

while source <= 20:
    ngu.write('SOUR:VOLT {:f}'.format(source))    # Set voltage to the variable
    ngu.query('*OPC?')                            # Wait for previous operations to complete
    time.sleep(.2)

    currentTime = time.time()

    query = ngu.query('READ?')                    # Read the voltage and current

    v, i = [float(x) for x in query.split(',')]
    
    data.append([v, i])
    
    if i > 0:
        break

    source += step

ngu.write('OUTP 0')                         # Turn off the output

vi = numpy.array(data)
idx = numpy.argmax(-vi[:, 0] * vi[:, 1])

print('Voc  = {:.3f} V'.format(vi[-1, 0]))
print('Isc  = {:.3f} mA'.format(-vi[0, 1] * 1000.))
print('Vmax = {:.3f} V'.format(vi[idx, 0]))
print('Imax = {:.3f} mA'.format(-vi[idx, 1] * 1000.))
print('Pmax = {:.3f} mW'.format(-vi[idx, 0] * vi[idx, 1] * 1000.))
