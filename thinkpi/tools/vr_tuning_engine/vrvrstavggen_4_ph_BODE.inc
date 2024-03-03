******************************************************************
*Generalized VR State Average Model 4 phases
*Created by E. J. Pole II
*Updated to handle single or dual-ended modeling - 08/22/2008
******************************************************************

* Compensation components for numbering reference

* +---------+   +----+   +--+   +--+   +--+   +--+
* | vsensep |---|+   |-+-|r3|---|c3|-+-|r2|---|c2|-+
* +---------+   |    | | +--+   +--+ | +--+   +--+ |
*               |diff| |diff         |             |

* +---------+   |    | |    +--+     |    +--+     |
* | vsensen |---|-   | +----|r1|-----+----|c1|-----+
* +---------+   +----+      +--+     |    +--+     |
*                                    |fb           |
*                                    | +-------+   |
*                                    +-| error |---+comp
*                                      +-------+

* Set parhier option to "local"
* localizing all parameters in subcircuit
* preventing interference between parameters in other files
* allowing override of values on subcircuit calls
* and use of ".alter" to run multiple cases at a time

.option parhier=local

*****************************************************
* State Average Model  
*****************************************************
.option acout=1 

.subckt vrstavggen sensep sensen g0 p1 p2 p3 p4 
*Connect "sensep" to positive differential feedback sense point
*Connect "sensen" to negative differential feedback sense point
*Connect "g0" to "0" for single-ended model or a reasonable VR ground connection node for a dual-ended model. This should be at or near the ground node equivalent to the phase node(s)
*Connect "px" to the phase inductor(s) output nodes
* Parameters used in the model
.param
+ r1 = '4.000000k'
+ r2 = '3.097629k'
+ r3 = '0.040651k'
+ c1 = '37.184908p'
+ c2 = '3.658897n'
+ c3 = '2.804969n'
+ duty = '75' * Maximum duty cycle in percentage
+ egain = '4000' * Gain of error amp
+ lout = '100.000000n' * The per phase inductor value in Henries
+ avp = '0.000560' * Adaptive Voltage Positioning setting in ohms
+ rout = '0.290000m' * dcr resistance of output inductor per phase value in ohms
+ vid = '1.1' * Output setpoint in volts
+ vin = '12' * Input voltage. Usually 12V
+ vramp = '1.5' * peak ramp voltage in volts
+ np = 4 * number of phases. Can be 1, 2, 3, 4, 5, 6, 7 ,8 ,9 or 10.
* Parameters NOT used in the model
+ fs = 300000 * per phase switching frequency

* Compensation network

r1 compin fb 'r1'
r2 fb r2c2 'r2'
r3 compin r3c3 'r3'
c1 fb comp 'c1'
c2 r2c2 comp 'c2'
c3 r3c3 fb 'c3'

Vfdbk compin diff dc 0 ac 1m

.probe ac
+ vdb(diff,compin),vp(diff,compin)  ** closed loop
+ vdb(diff,comp),vp(diff,comp)      **plant
+ vdb(comp,compin),vp(comp,compin)

* Error "amp"

vvid vid g0 'vid'
ecomp comp g0 vcvs vid fb 'egain' max='vramp'

* Differential sense input calculation

ediff diff g0 vol='v(sensep,g0)-v(sensen,g0)'

.if (avp!=0)
   gdroop fb g0 vol='i(eout)*avp/r1'
.endif

* Output

eout swn g0 vol='vin*v(comp,g0)/vramp' max='vin*duty/100'

lp1 swn lp1rp1 'lout'
rp1 lp1rp1 p1 'rout'
.probe ac v(p1)* dummy probe remove after model is complete

lp2 swn lp2rp2  'lout'
rp2 lp2rp2 p2  'rout'

lp3 swn lp3rp3  'lout'
rp3 lp3rp3 p3  'rout'

lp4 swn lp4rp4  'lout'
rp4 lp4rp4 p4  'rout'


.ends
