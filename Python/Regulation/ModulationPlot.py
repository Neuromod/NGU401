import numpy
import matplotlib.pyplot as pyplot


def plot(v, title):
    t = numpy.arange(v.size) / (500_000 * 1.01348)

    pyplot.plot(t * 1000, v)

    pyplot.ylabel('Voltage (V)')
    pyplot.xlabel('Time (ms)')

    pyplot.title(title)


f1hz   = numpy.load('../Data/Regulation/modulation_1Hz.npy')
f10hz  = numpy.load('../Data/Regulation/modulation_10Hz.npy')
f100hz = numpy.load('../Data/Regulation/modulation_100Hz.npy')

plot(f1hz, '1 Hz Sine Wave')
pyplot.gcf().set_size_inches(12, 6)
pyplot.savefig('../Data/Regulation/modulation_1Hz.png', dpi = 300)
pyplot.clf()

plot(f10hz, '10 Hz Sine Wave')
pyplot.gcf().set_size_inches(12, 6)
pyplot.savefig('../Data/Regulation/modulation_10Hz.png', dpi = 300)
pyplot.clf()

plot(f100hz, '100 Hz Sine Wave')
pyplot.gcf().set_size_inches(12, 6)
pyplot.savefig('../Data/Regulation/modulation_100Hz.png', dpi = 300)
pyplot.clf()
