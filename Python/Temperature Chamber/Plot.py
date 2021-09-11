import re
import numpy
import matplotlib.pyplot as pyplot


with open('../Data/Temperature Chamber/chamber.log') as file:
    lines = file.readlines()

t = []
T = []
sp = []

for line in lines:
    if line[0] == 't':
        m = re.search('t: ([^ ]*), T: ([^ ]*), SP: ([^ ]*),', line)
        
        t.append(float(m.group(1)))
        T.append(float(m.group(2)))
        sp.append(float(m.group(3)))

t = numpy.array(t) / 3600.
T = numpy.array(T)
sp = numpy.array(sp)

pyplot.plot(t, sp)
pyplot.plot(t, T)

pyplot.yticks([30, 25, 20, 15])

pyplot.xlabel('Time (h)')
pyplot.ylabel('Temperature (°C)')

pyplot.legend(['Setpoint', 'Temperature'], frameon = False)

pyplot.gcf().set_size_inches(12, 6)
pyplot.savefig('../Data/Temperature Chamber/chamber.png', dpi = 300)
pyplot.clf()
