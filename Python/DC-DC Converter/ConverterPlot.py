import numpy
import matplotlib.pyplot as pyplot
import matplotlib.colors as colors


# Settings

input            = '../Data/DC-DC Converter/PWM.npz'
outputPin        = '../Data/DC-DC Converter/PWM_Power.png'
outputVout       = '../Data/DC-DC Converter/PWM_Voltage.png'
outputEfficiency = '../Data/DC-DC Converter/PWM_Efficiency.png'
title = 'PWM'

input            = '../Data/DC-DC Converter/PFM.npz'
outputPin        = '../Data/DC-DC Converter/PFM_Power.png'
outputVout       = '../Data/DC-DC Converter/PFM_Voltage.png'
outputEfficiency = '../Data/DC-DC Converter/PFM_Efficiency.png'
title = 'PFM'

input            = '../Data/DC-DC Converter/DCM.npz'
outputPin        = '../Data/DC-DC Converter/DCM_Power.png'
outputVout       = '../Data/DC-DC Converter/DCM_Voltage.png'
outputEfficiency = '../Data/DC-DC Converter/DCM_Efficiency.png'
title = 'DCM'

size   = (6, 4.5)


# Function

def plot(vTable, iTable, quantity, title, cmap, logBar, minBar, maxBar, barLabel, contourLevels, contourThreshold, width = size[0], height = size[1]):
    fig, ax = pyplot.subplots()
    pyplot.gcf().set_size_inches(width, height)

    if logBar:
        pyplot.pcolormesh(iTable, vTable, quantity, shading = 'auto', cmap = cmap, norm = colors.LogNorm(vmin = minBar, vmax = maxBar))
    else:
        pyplot.pcolormesh(iTable, vTable, quantity, shading = 'auto', cmap = cmap, vmin = minBar, vmax = maxBar)
        
    pyplot.xscale('log')

    pyplot.xticks([1e-4, 1e-3, 1e-2, 1e-1, 1], ['100$\mu$', '1m', '10m', '100m', '1'])

    pyplot.xlabel('$I_{out}$ (A)', fontsize = 15)
    pyplot.ylabel('$V_{in}$ (V)', fontsize = 15)

    cb = pyplot.colorbar(label = barLabel)
    cb.set_label(label = barLabel, size = 15)

    if len(contourLevels) != 0:
        cs = pyplot.contour(iTable, vTable, quantity, contourLevels, colors = ['w' if x <= contourThreshold else 'k' for x in levels])
        ax.clabel(cs, inline = True, inline_spacing = 5, fontsize = 10)

    pyplot.title(title, fontsize = 18)


# Code

file = numpy.load(input)

data   = file['data']
vTable = file['vTable']
iTable = file['iTable']

vIn  = data[:, :, 0]
iIn  = data[:, :, 1]
pIn  = vIn * iIn

vOut = data[:, :, 2]
iOut = data[:, :, 3]
pOut = vOut * iOut

vIn[vIn == 0] = numpy.NaN
iIn[iIn == 0] = numpy.NaN
pIn[pIn == 0] = numpy.NaN

vOut[vOut == 0] = numpy.NaN
iOut[iOut == 0] = numpy.NaN
pOut[pOut == 0] = numpy.NaN

efficiency = numpy.empty(data.shape[0 : 2])
efficiency[:] = numpy.NaN
efficiency[pIn != 0] = pOut[pIn != 0] / pIn[pIn != 0]

levels = numpy.array([0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95])
plot(vTable, iTable, efficiency, title, 'inferno', False, 0., 1., 'Efficiency', levels, 0.5)
pyplot.savefig(outputEfficiency, dpi = 300)
pyplot.clf()

levels = numpy.array([0.01, 0.1, 1.0, 10])
plot(vTable, iTable, pIn, title, 'inferno', True, 0.001, 15, 'Input power (W)', levels, 0.5)
pyplot.savefig(outputPin, dpi = 300)
pyplot.clf()

levels = numpy.array([5])
plot(vTable, iTable, vOut, title, 'seismic', False, 4.9, 5.1, 'Output voltage (V)', levels, 4)
pyplot.savefig(outputVout, dpi = 300)
pyplot.clf()


