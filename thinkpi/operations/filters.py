import os
from time import sleep

from scipy import signal

from bokeh.io import output_file, show

from thinkpi.operations.plotting import Plotter 


class Filter:
    '''
    This class supports the following digital filters: Elliptic, Butterworth, Chebyshev type I, Chebyshev type II, and Bessel.
    Depending on the filter type the following parameters are required:

    filter_name = The name of the filter: 'elliptic', 'butterworth', 'chebyshev1', 'chebyshev2', 'bessel'

    order       = Order of the filter
                  --> Applies to all filters.

    cutoff_freq = Frequency at which the transition in the filter occurs specified in Hz.
                  For bandpass or bandstop filters provide two numbers in parentheses (low_freq, high_freq).
                  --> Applies to all filters.

    filter_type = The type of filter. Can only take these values: 'lowpass', 'highpass', 'bandpass', 'bandstop'.
                  --> Applies to all filters.

    ts          = Sampling time of the digital filter specified in seconds.
                  --> Applies to all filters.
    
    ripple      = The maximum ripple allowed below unity gain in the passband region, specified in dB.
                  --> Does not apply to Butterworth, hebyshev type II, and Bessel filters.

    att         = The minimum attenuation required in the stopband region, specified in dB.
                  --> Does not apply to Butterworth, Chebyshev type I, and Bessel filters.

                        order   |   cutoff freq. [Hz]   |   filter_type |   ts [sec]    |   ripple [dB]    |   att [dB]    
                    -------------------------------------------------------------------------------------------------------  
    elliptic              x                 x                   x               x                x                x
    butterworth           x                 x                   x               x                
    chebyshev1            x                 x                   x               x                x
    chebyshev2            x                 x                   x               x                                 x
    bessel                x                 x                   x               x   
    '''

    def __init__(self, filter_name, order, cutoff_freq, filter_type, ts,
                 ripple=None, att=None, keep_DC=False, analog=False, output='sos'):

        self.filter_types = {'elliptic': self.elliptic, 'butterworth': self.butterworth,
                             'chebyshev1': self.chebyshev1, 'chebyshev2': self.chebyshev2,
                             'bessel': self.bessel}
        self.filter_name = filter_name
        self.filter_func = self.filter_types[self.filter_name]
        self.order = order
        self.ripple = ripple
        self.att = att
        self.cutoff_freq = cutoff_freq
        self.filter_type = filter_type
        self.fs = 1/ts
        self.keep_DC = keep_DC
        self.analog = analog
        self.output = output
        self.plt = Plotter()
    
    def __repr__(self):

        return f'{self.filter_name}, order: {self.order}, cuttoff freq: {self.cutoff_freq} Hz, filter type: {self.filter_type}, sampling interval: {1/self.fs:.3} sec'

    def _freq_descr(self):

        if self.filter_type == 'lowpass' or self.filter_type == 'low':
                return f'LP_{round(self.cutoff_freq*1e-6, 2)}MHz'
        elif self.filter_type == 'highpass' or self.filter_type == 'high':
            return f'HP_{round(self.cutoff_freq*1e-6, 2)}MHz'
        elif self.filter_type == 'bandpass':
            return f'BP_{round(self.cutoff_freq[0]*1e-6, 2)}_{round(self.cutoff_freq[1]*1e-6, 2)}MHz'
        elif self.filter_type == 'bandstop':
            return f'BS_{round(self.cutoff_freq[0]*1e-6, 2)}_{round(self.cutoff_freq[1]*1e-6, 2)}MHz'

    def elliptic(self):

        return signal.ellip(N=self.order, rp=self.ripple, rs=self.att,
                            Wn=self.cutoff_freq, btype=self.filter_type,
                            analog=self.analog, output=self.output, fs=self.fs)

    def butterworth(self):

        return signal.butter(N=self.order, Wn=self.cutoff_freq, btype=self.filter_type,
                             analog=self.analog, output=self.output, fs=self.fs)

    def chebyshev1(self):

        return signal.cheby1(N=self.order, rp=self.ripple, Wn=self.cutoff_freq, btype=self.filter_type,
                             analog=self.analog, output=self.output, fs=self.fs)

    def chebyshev2(self):

        return signal.cheby2(N=self.order, rs=self.att, Wn=self.cutoff_freq, btype=self.filter_type,
                             analog=self.analog, output=self.output, fs=self.fs)

    def bessel(self):

        return signal.bessel(N=self.order, Wn=self.cutoff_freq, btype=self.filter_type,
                             analog=self.analog, output=self.output, norm='phase', fs=self.fs)

    def plot(self, xaxis_type='linear', yaxis_type='linear'):

        #cwd = os.getcwd()
        output_file('filter_responses.html')
        show(self.plt.plot_filter_response(self, xaxis_type=xaxis_type,
                                            yaxis_type=yaxis_type))



