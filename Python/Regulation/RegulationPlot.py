import numpy
import matplotlib.pyplot as pyplot


# Settings

size = (12, 6)


# Functions

def load(filename):
    file = numpy.load(filename)

    vBuffer = file['vBuffer']
    iBuffer = file['iBuffer']

    tBuffer = numpy.arange(vBuffer.size) / (500_000 * 1.01348)

    return tBuffer, vBuffer, iBuffer


def plotVI(tBuffer, vBuffer, iBuffer, title):
    ax1 = pyplot.subplot(211)

    pyplot.plot(tBuffer, vBuffer)
    pyplot.ylabel('Voltage (v)')
    pyplot.setp(ax1.get_xticklabels(), visible=False)
 
    ax2 = pyplot.subplot(212, sharex = ax1)

    pyplot.plot(tBuffer, iBuffer)
    pyplot.xlabel('Time (s)')
    pyplot.ylabel('Current (A)')

    ax1.set_title(title)


def plotStackT(tBuffer, vBuffer, iBuffer, title, search, threshold, plot, start, end):
    if search == 'i':
        idxList = numpy.where(numpy.logical_and(numpy.abs(iBuffer[:-1]) < threshold, numpy.abs(iBuffer[1:]) >= threshold))[0]
    elif search == 'v':
        idxList = numpy.where(numpy.logical_and(numpy.abs(vBuffer[:-1]) < threshold, numpy.abs(vBuffer[1:]) >= threshold))[0]

    startDelta = int(numpy.argmax(tBuffer > numpy.abs(start) / 1000.) * numpy.sign(start))
    endDelta   = int(numpy.argmax(tBuffer > numpy.abs(end)   / 1000.) * numpy.sign(end))

    for idx in idxList:
        startIndex = idx + startDelta
        endIndex   = idx + endDelta

        if plot == 'v':
            pyplot.plot(tBuffer[: endIndex - startIndex] * 1000. + start, vBuffer[startIndex : endIndex])
            pyplot.ylabel('Voltage (V)')
        elif plot == 'i':
            pyplot.plot(tBuffer[: endIndex - startIndex] * 1000. + start, iBuffer[startIndex : endIndex])
            pyplot.ylabel('Current (A)')

    pyplot.xlabel('Time (ms)')

    pyplot.title(title)


def plotStackTV(tBuffer, vBuffer, iBuffer, title, search = 'i', threshold = 0.15, plot = 'v', start = -0.2, end = 1.2):
    if search == 'i':
        rise = numpy.where(numpy.logical_and(numpy.abs(iBuffer[:-1]) < threshold, numpy.abs(iBuffer[1:]) >= threshold))[0]
    elif search == 'v':
        rise = numpy.where(numpy.logical_and(numpy.abs(vBuffer[:-1]) < threshold, numpy.abs(vBuffer[1:]) >= threshold))[0]
        fall = numpy.where(numpy.logical_and(numpy.abs(vBuffer[:-1]) > threshold, numpy.abs(vBuffer[1:]) <= threshold))[0]
        
    startDelta = int(numpy.argmax(tBuffer > numpy.abs(start) / 1000.) * numpy.sign(start))
    endDelta   = int(numpy.argmax(tBuffer > numpy.abs(end)   / 1000.) * numpy.sign(end))

    for i in range(rise.size):
        startIndex = rise[i] + startDelta
        endIndex   = rise[i] + endDelta
        span = endIndex - startIndex

        if plot == 'v':
            if search == 'v':
                delta = vBuffer[startIndex + span // 3: endIndex - span // 3].mean()
            
            elif search == 'i':
                delta = vBuffer[startIndex - 200 : startIndex - 100].mean()
            
            pyplot.plot(tBuffer[: endIndex - startIndex] * 1000. + start, vBuffer[startIndex : endIndex] - delta)
            pyplot.ylabel('Voltage (V)')
        
        elif plot == 'i':
            delta = iBuffer[startIndex + span // 3: endIndex - span // 3].mean()
            
            pyplot.plot(tBuffer[: endIndex - startIndex] * 1000. + start, iBuffer[startIndex : endIndex] - delta)
            pyplot.ylabel('Current (A)')

    pyplot.xlabel('Time (ms)')

    pyplot.title(title)


# Code

fileList = \
[
    ['../Data/Regulation/i_0.npz',     'CPM: Sweep: -8 A to +8 A, Load: Short', -0.2, 1.2],
    ['../Data/Regulation/i_0_320.npz', 'CPM: Sweep: -8 A to +8 A, Load: 0.3 $\Omega$', -0.2, 1.2],
]

for file, title, start, end in fileList:
    tBuffer, vBuffer, iBuffer = load(file)

    plotVI(tBuffer, vBuffer, iBuffer, title)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_VI.png', dpi = 300)
    pyplot.clf()

    plotStackT(tBuffer, vBuffer, iBuffer, title, 'i', 0.25, 'i', -0.5, 10.5)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_T.png', dpi = 300)
    pyplot.clf()

    plotStackTV(tBuffer, vBuffer, iBuffer, title, 'i', 0.25, 'i', -0.5, 10.5)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_TV.png', dpi = 300)
    pyplot.clf()

fileList = \
[
    ['../Data/Regulation/v_s_nl.npz', 'VPM: Sweep: -20V to +20 V, Load: Open, FTR: Off',       -0.5, 10.5],
    ['../Data/Regulation/v_f_nl.npz', 'VPM: Sweep: -20V to +20 V, Load: Open, FTR: On',        -0.5, 10.5],
    ['../Data/Regulation/v_s_8.npz',  'VPM: Sweep: -20V to +20 V, Load: 8 $\Omega$, FTR: Off', -0.5, 10.5],
    ['../Data/Regulation/v_f_8.npz',  'VPM: Sweep: -20V to +20 V, Load: 8 $\Omega$, FTR: On',  -0.5, 10.5],
 ]

for file, title, start, end in fileList:
    tBuffer, vBuffer, iBuffer = load(file)

    plotVI(tBuffer, vBuffer, iBuffer, title)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_VI.png', dpi = 300)
    pyplot.clf()

    plotStackT(tBuffer, vBuffer, iBuffer, title, 'v', 0.1, 'v', -0.5, 10.5)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_T.png', dpi = 300)
    pyplot.clf()

    plotStackTV(tBuffer, vBuffer, iBuffer, title, 'v', 0.1, 'v', -0.5, 10.5)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_TV.png', dpi = 300)
    pyplot.clf()

fileList = \
[
    ['../Data/Regulation/regulation_load_5_580_slow_max3.npz', 'Regulation: Sweep: 0 V to +20 V, Max current: ~0.5 A, FTR: Off', -0.2, 1.2],
    ['../Data/Regulation/regulation_load_5_580_fast_max3.npz', 'Regulation: Sweep: 0 V to +20 V, Max current: ~0.5 A, FTR: On',  -0.2, 1.2],
    ['../Data/Regulation/regulation_load_6_250_slow_max3.npz', 'Regulation: Sweep: 0 V to +20 V, Max current: ~3 A, FTR: Off',   -0.2, 1.2],
    ['../Data/Regulation/regulation_load_6_250_fast_max3.npz', 'Regulation: Sweep: 0 V to +20 V, Max current: ~3 A, FTR: On',    -0.2, 1.2],
    ['../Data/Regulation/regulation_load_6_950_slow_max8.npz', 'Regulation: Sweep: 0 V to +6 V, Max current: ~8 A, FTR: Off',    -0.2, 1.2],
    ['../Data/Regulation/regulation_load_6_950_fast_max8.npz', 'Regulation: Sweep: 0 V to +6 V, Max current: ~8 A, FTR: On',     -0.2, 1.2],
]

for file, title, start, end in fileList:
    tBuffer, vBuffer, iBuffer = load(file)

    plotVI(tBuffer, vBuffer, iBuffer, title)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_VI.png', dpi = 300)
    pyplot.clf()

    plotStackT(tBuffer, vBuffer, iBuffer, title, 'i', 0.15, 'v', start, end)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_T.png', dpi = 300)
    pyplot.clf()

    plotStackTV(tBuffer, vBuffer, iBuffer, title, 'i', 0.15, 'v', start, end)
    pyplot.gcf().set_size_inches(size[0], size[1])
    pyplot.savefig(file[:-4] + '_TV.png', dpi = 300)
    pyplot.clf()
