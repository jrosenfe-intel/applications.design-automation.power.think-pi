*######################################################################
*Generic current pulse
*######################################################################
.subckt current_pulse n1 n2 
+ileak=0
+imin=0
+imax=1
+vid=1
+gpoly=1
+iprobe=0
+trise=1n
+ton=1u
+tperiod=2u
+tdelay=1u

V_test_I n1 mid 0

.if(iprobe==1)
	.probe I(V_test_I)
.endif


.if(gpoly==1)
	*If we want at GPOLY
	Vctrl_Idyn	controlnode_Idyn	0	PWL 
	+0 					'imin' 
	+1p 				'imin' 
	+'trise' 			'imax-ileak' 
	+'trise+ton' 		'imax-ileak'
	+'trise+ton+trise' 	'imin' 
	+'tperiod' 			'imin'
	+td=tdelay
	+r=0

	Vctrl_Ileak	controlnode_Ileak	0	PWL (0 ileak tperiod ileak )

	Gpolydyn mid n2 poly(2) controlnode_Idyn 0 n1 n2 0 0 0 0 '1/vid'
	Gpolyleak mid n2 poly(2) n1 n2 controlnode_Ileak 0 0 0 0 0 0 0 0 0 0 0 0 '1/(pow(vid,3))'
.else
*If we want a PWL hard current
	I_Icctdyn	mid	n2	PWL 
	+0 									'imin' 
	+1p 								'imin' 
	+'trise' 						    'imax-ileak' 
	+'trise+ton' 				        'imax-ileak'
	+'trise+ton+trise' 		            'imin' 
	+'tperiod' 						    'imin'
	+td=tdelay
	+r=0

	I_Ileak	mid	n2	PWL (0 ileak tperiod ileak )
.endif
.ends
