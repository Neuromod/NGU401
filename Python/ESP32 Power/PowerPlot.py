import numpy
import matplotlib.pyplot as pyplot
import scipy.signal as signal


# Settings

smuInput    = '../Data/ESP32 Power/power.npz'
scopeInput  = '../Data/ESP32 Power/scope.npz'
rawOutput   = '../Data/ESP32 Power/raw.png'
powerOutput = '../Data/ESP32 Power/power.png'

size = (12, 6)


# Precomputation

file = numpy.load(smuInput)

vBuffer  = file['vBuffer']
iBuffer  = file['iBuffer']

file = numpy.load(scopeInput)

ch1 = file['ch1'].astype(float)
ch2 = file['ch2'].astype(float)

ch1 -= ch1.min()
ch1 /= ch1.max()
ch1 = (ch1 > 0.5).astype(float)

ch2 -= ch2.min()
ch2 /= ch2.max()
ch2 = (ch2 > 0.5).astype(float)

edge = numpy.where(numpy.diff(ch1) != 0)[0]
duration = (edge[1] - edge[0]) / 100_000
tScope = (numpy.arange(ch1.size) - edge[0]) / 100_000

posEdge = tScope[numpy.where(numpy.diff(ch2) > 0)[0]]
negEdge = tScope[numpy.where(numpy.diff(ch2) < 0)[0]]

edge = numpy.where(numpy.diff(vBuffer > 2.5) != 0)[0]
rate = (edge[1] - edge[0]) / duration
tSmu = (numpy.arange(iBuffer.size) - edge[0]) / rate 

# Print measurements

phase = \
[
    'Idle',
    'Computation',
    'WiFi Connect',
    'WiFi Idle',
    'WiFi Download',
    'WiFi Upload',
    'WiFi Disconnect',
    'Light-sleep Overhead',
    'Light-sleep',
    'Deep-sleep Overhead',
    'Deep-sleep',
    'Reset',
]

for i in range(12):
    t0 = negEdge[i]
    t1 = posEdge[i + 1]

    idx0 = numpy.argmax(tSmu > t0)
    idx1 = numpy.argmax(tSmu > t1)

    if i == 8 or i == 10:
        mid = (idx0 + idx1) / 2
        
        idx0 = int(mid - rate * .5)
        idx1 = int(mid + rate * .5)

        t0 = tSmu[idx0]
        t1 = tSmu[idx1]

    current = iBuffer[idx0 : idx1].mean()
    charge  = current * (t1 - t0)
    power   = (iBuffer[idx0 : idx1] * vBuffer[idx0 : idx1]).mean()
    energy  = power * (t1 - t0)

    print('{:20s} : {:6.1f} ms, {:5.1f} mA, {:5.1f} mC, {:5.1f} mW, {:6.1f} mJ'.format(phase[i % 12], (t1 - t0) * 1000., current * 1000., charge * 1000., power * 1000., energy * 1000.))


# Plot synchronized graph

pyplot.plot(tSmu, vBuffer / vBuffer.max() * 0.9 + 0)
pyplot.plot(tSmu, iBuffer / iBuffer.max() * 0.9 + 1)
pyplot.plot(tScope, ch1 * 0.4 + 2)
pyplot.plot(tScope, ch2 * 0.4 + 2.5)

pyplot.ylim(0, 3.3)
pyplot.xlim(-5, 60)

pyplot.yticks([])
pyplot.xlabel('Time (s)')

pyplot.legend(['SMU voltage', 'SMU current', 'Oscilloscope voltage', 'Oscilloscope GPIO'], frameon = False, loc = 1, ncol = 4)

pyplot.title('Recorded Waveforms')

pyplot.gcf().set_size_inches(size[0], size[1])
pyplot.savefig(rawOutput, dpi = 300)
pyplot.clf()


# Plot single iteration power

idx0 = numpy.argmax(tSmu > negEdge[0])
idx1 = numpy.argmax(tSmu > posEdge[12])

pyplot.plot(tSmu[idx0 : idx1], iBuffer[idx0 : idx1] * vBuffer[idx0 : idx1])

top = iBuffer[idx0 : idx1].max()

for i in range(13):
    t = (posEdge[i] + negEdge[i]) / 2
    
    pyplot.plot([t, t], [0, 0.05], 'k')

pyplot.xlabel('Time (s)')
pyplot.ylabel('Power (W)')

pyplot.title('Power Consumption')

pyplot.gcf().set_size_inches(size[0], size[1])
pyplot.savefig(powerOutput, dpi = 300)
pyplot.clf()