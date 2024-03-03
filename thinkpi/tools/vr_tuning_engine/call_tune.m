%matlab -batch "Untitled(2)
pha=2  %count
rll=0.5 %mOhms
vin=12 %V
vramp=1.5 %V
f0=100e3 %Hz
PHmarg=60 %deg
lout=100 %nH
rout=0.29 %mO
VID=1 %V
touchstoune_file='plant.s2p'
includePath=''
tune_vr(pha,rll,vin,vramp,f0,PHmarg,lout,rout,VID,touchstoune_file,includePath)
