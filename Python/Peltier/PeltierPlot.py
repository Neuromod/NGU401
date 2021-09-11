import numpy
import scipy.signal as signal
import matplotlib.pyplot as pyplot


# Settings

inputStep        = '../Data/Peltier/continuous.npz'
inputPulse       = '../Data/Peltier/pulse.npz'
inputPwm         = '../Data/Peltier/PWM.npz' 

outputStepTime   = '../Data/Peltier/continuous_time.png' 
outputPulseTime  = '../Data/Peltier/pulse_time.png' 
outputPwmTime    = '../Data/Peltier/pwm_time.png' 

outputIv         = '../Data/Peltier/IV.png'
outputR          = '../Data/Peltier/R.png'
outputEfficiency = '../Data/Peltier/Efficiency.png'

stepWindow  = 2       # Step average window size in seconds
pulseWindow = 0.0005  # Pulse average window size in seconds
pwmWindow   = 2       # PWM average window size in seconds

size = (12, 6)


# Load files

file = numpy.load(inputStep)

stepI  = file['iBuffer']
stepV  = file['vBuffer']
stepT  = file['tBuffer']
stepTm = file['tmBuffer']

file = numpy.load(inputPulse)

pulseV  = file['vBuffer']
pulseI  = file['iBuffer']
pulseT  = file['tBuffer']
pulseTm = file['tmBuffer']

file = numpy.load(inputPwm)

pwmDc = file['dcBuffer']
pwmP  = file['pBuffer']
pwmT  = file['tBuffer']
pwmTm = file['tmBuffer']


# Step preprocessing

diff = numpy.append(numpy.diff(stepV), 0)
where = numpy.append(numpy.where(diff > numpy.median(numpy.abs(diff)) * 1000)[0], stepV.size - 1)

segStepV = numpy.zeros(where.size)
segStepI = numpy.zeros(where.size)
segStepT = numpy.zeros(where.size)

for i in range(where.size):    
    slice = numpy.logical_and(stepTm + stepWindow >= stepTm[where[i]], stepTm <= stepTm[where[i]])

    segStepV[i] = stepV[slice].mean()
    segStepI[i] = stepI[slice].mean()
    segStepT[i] = stepT[slice].mean()


# Pulse preprocessing

diff  = numpy.diff((numpy.abs(pulseV) > numpy.mean(numpy.abs(pulseV)) * 100).astype(float))

where = numpy.where(diff != 0)[0]
where = (where[diff[where] > 0] + where[diff[where] < 0]) // 2

half = where.size // 2
where = numpy.concatenate((where[:half], [(where[half - 1] + where[half]) // 2], where[half:]))

segPulseV = numpy.zeros(where.size)
segPulseI = numpy.zeros(where.size)
segPulseT = numpy.zeros(where.size)

for i in range(where.size):
    slice = numpy.logical_and(pulseTm >= pulseTm[where[i]] - pulseWindow / 2, pulseTm <= pulseTm[where[i]] + pulseWindow / 2)

    segPulseV[i] = pulseV[slice].mean()
    segPulseI[i] = pulseI[slice].mean()
    segPulseT[i] = pulseT[slice].mean()


# PWM preprocessing

diff = numpy.append(numpy.diff(pwmDc), 0)
where = numpy.append(numpy.where(numpy.diff(pwmDc) != 0)[0], pwmDc.size - 1)

segPwmDc = numpy.zeros(where.size)
segPwmP  = numpy.zeros(where.size)
segPwmT  = numpy.zeros(where.size)

for i in range(where.size):    
    slice = numpy.logical_and(pwmTm + pwmWindow >= pwmTm[where[i]], pwmTm <= pwmTm[where[i]])

    segPwmDc[i] = pwmDc[where[i]]
    segPwmP[i]  = pwmP[slice].mean()
    segPwmT[i]  = pwmT[slice].mean()


# Step-Time

fig = pyplot.gcf()
ax1 = pyplot.gca()
ax2 = pyplot.gca().twinx()

p1 = ax1.plot(stepTm, stepV, 'C0')
p2 = ax1.plot(stepTm, stepI, 'C1')
p3 = ax2.plot(stepTm, stepT, 'C2')

ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Voltage (v) / Current (A)')
ax2.set_ylabel('Temperature (ºC)')

ax2.set_ylim(-15, 75)

ax1.set_title('Continuous Voltage Characterization')

ax1.legend(p1 + p2 + p3, ['Voltage', 'Current', 'Temperature'], loc = 2, frameon = False)

fig.set_size_inches(size[0], size[1])
fig.savefig(outputStepTime, dpi = 300)
pyplot.clf()


# Pulse-Time

fig = pyplot.gcf()
ax1 = pyplot.gca()
ax2 = pyplot.gca().twinx()

p1 = ax1.plot(pulseTm, pulseV, 'C0')
p2 = ax1.plot(pulseTm, pulseI, 'C1')
p3 = ax2.plot(pulseTm, pulseT, 'C2')

ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Voltage (v) / Current (A)')
ax2.set_ylabel('Temperature (ºC)')

ax2.set_ylim(numpy.floor(pulseT.mean()) - 0.75, numpy.ceil(pulseT.mean()) + 0.75)

ax1.set_title('Pulsed Characterization')

ax1.legend(p1 + p2 + p3, ['Voltage', 'Current', 'Temperature'], loc = 2, frameon = False)

fig.set_size_inches(size[0], size[1])
fig.savefig(outputPulseTime, dpi = 300)
pyplot.clf()


# PWM-Time

fig = pyplot.gcf()
ax1 = pyplot.gca()
ax2 = pyplot.gca().twinx()

p1 = ax1.plot(pwmTm, pwmP, 'C0')
p2 = ax2.plot(pwmTm, abs(pwmDc) * 100, 'C1')
p3 = ax2.plot(pwmTm, pwmT, 'C2')

ax1.set_xlabel('Time (s)')
ax1.set_ylabel('Power (W)')
ax2.set_ylabel('Duty Cycle (%) / Temperature (ºC)')

ax1.set_ylim(-1, 13)
ax2.set_ylim(-15, 125)

ax1.set_title('PWM Voltage Characterization')

ax1.legend(p1 + p2 + p3, ['Power', 'Duty cycle (%)', 'Temperature'], loc = 2, frameon = False)

fig.set_size_inches(size[0], size[1])
fig.savefig(outputPwmTime, dpi = 300)
pyplot.clf()


# I/V plot

pyplot.plot(segStepV,  segStepI, '.-')
pyplot.plot(segPulseV, segPulseI, '.-')

pyplot.xlabel('Voltage (V)')
pyplot.ylabel('Current (A)')

pyplot.legend(['Continuous', 'Pulsed'], loc = 2, frameon = False)

pyplot.title('Voltage/Current Curves')

fig.set_size_inches(size[0], size[1])
fig.savefig(outputIv, dpi = 300)
pyplot.clf()


# R plot

mid = segStepV.size >> 1

v = numpy.append(segStepV[:mid], segStepV[mid + 1:])
i = numpy.append(segStepI[:mid], segStepI[mid + 1:])
r = v / i

pyplot.plot(v,  r, '.-')

mid = segPulseV.size >> 1

v = numpy.append(segPulseV[:mid], segPulseV[mid + 1:])
i = numpy.append(segPulseI[:mid], segPulseI[mid + 1:])
r = v / i

pyplot.plot(v, r, '.-')

pyplot.xlabel('Voltage (V)')
pyplot.ylabel('Resistance ($\\Omega$)')

pyplot.legend(['Continuous', 'Pulsed'], loc = 2, frameon = False)

pyplot.ylim(0, 5)

pyplot.title('Resistance Curves')

fig.set_size_inches(size[0], size[1])
fig.savefig(outputR, dpi = 300)
pyplot.clf()


# Efficiency plot

pyplot.plot(segStepV * segStepI, segStepT, '.-')
pyplot.plot(segPwmP, segPwmT, '.-')

pyplot.xlabel('Power (W)')
pyplot.ylabel('Temperature (C)')

pyplot.legend(['Continuous', 'PWM'], loc = 2, frameon = False)

pyplot.title('Efficiency')

fig.set_size_inches(size[0], size[1])
fig.savefig(outputEfficiency, dpi = 300)
pyplot.clf()
