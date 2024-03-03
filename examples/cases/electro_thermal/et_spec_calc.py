import matplotlib.pyplot as plt
from scipy import interpolate
import numpy as np
import thinkpi.config.thinkpi_conf as cfg

# x axis values 
temp = list(cfg.ETPS_TEMP_SCALE.keys()) 
# corresponding y axis values 
current = list(cfg.ETPS_TEMP_SCALE.values())

# Interpolation
func_temp = interpolate.interp1d(list(cfg.ETPS_TEMP_SCALE.keys()),
                                                list(cfg.ETPS_TEMP_SCALE.values())
                                            )

# plotting the points  
plt.plot(temp, current, ".--")
temp2 = np.linspace(temp[0], temp[-1], 50)
plt.plot(temp2, func_temp(temp2), 'orange')
plt.plot(temp2, 2520.4*np.exp(-0.065*temp2), 'green')
  
# naming the x axis
plt.xlabel('Temperature [C]') 
# naming the y axis 
plt.ylabel('Current [A]') 
plt.grid()
plt.legend(['eTPS data', 'ThinkPI', 'Manual POR'])

plt.show()