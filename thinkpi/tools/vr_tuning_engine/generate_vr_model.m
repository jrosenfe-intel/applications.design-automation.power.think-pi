%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%FILE NAME: generate_vr_model.m
%VERSION: 0.1 Initial Release
%DATE: Feb 28th, 2012
%
%DESCRIPTION: This script generates the E.J. VR model
%        
%   generate_vr_model(pha,tuning,compensator_val,avp,lout,rout)
%
% pha: Number of VR phases
% tuning: 1 -> If you want to generate a VR model for tuning (this model
%              includes ac source perturbation of 1mA)
%         0 -> If you want to generate VR model for AC and TRAN analysis 
% compensator_val: Vector with values for elements in compensation network
%                 [  r1   r2    r3  c1 c2 c3], values must be in: 
%                  omhs komhs kohms pF nF nF  
% avp: Adaptive Voltage Positioning(Load Line value), it must be in mohms
% lout: The per phase inductor value in nHenries
% rout: Resistance of output inductor per phase value in mohms
%
%   Miryam Lomeli 
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
function flag = generate_vr_model(filePath,pha,tuning,compensator_val,avp,lout,rout,VID)

    if tuning==0   
        vr_file_name = sprintf('%svrstavggen_%d_ph.inc',filePath,pha);
    else
        vr_file_name = sprintf('%svrstavggen_%d_ph_BODE.inc',filePath,pha);
    end

    vr_file = fopen (vr_file_name,'w');

   if vr_file==-1
       flag = -1;
       return;
   else
       flag = 1;
   end
   fprintf(vr_file,'******************************************************************\n');
   fprintf(vr_file,'*Generalized VR State Average Model %d phases\n',pha);
   fprintf(vr_file,'*Created by E. J. Pole II\n');
   fprintf(vr_file,'*Updated to handle single or dual-ended modeling - 08/22/2008\n');
   fprintf(vr_file,'******************************************************************\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'* Compensation components for numbering reference\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'* +---------+   +----+   +--+   +--+   +--+   +--+\n');
   fprintf(vr_file,'* | vsensep |---|+   |-+-|r3|---|c3|-+-|r2|---|c2|-+\n');
   fprintf(vr_file,'* +---------+   |    | | +--+   +--+ | +--+   +--+ |\n');
   fprintf(vr_file,'*               |diff| |diff         |             |\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'* +---------+   |    | |    +--+     |    +--+     |\n');
   fprintf(vr_file,'* | vsensen |---|-   | +----|r1|-----+----|c1|-----+\n');
   fprintf(vr_file,'* +---------+   +----+      +--+     |    +--+     |\n');
   fprintf(vr_file,'*                                    |fb           |\n');
   fprintf(vr_file,'*                                    | +-------+   |\n');
   fprintf(vr_file,'*                                    +-| error |---+comp\n');
   fprintf(vr_file,'*                                      +-------+\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'* Set parhier option to \"local\"\n');
   fprintf(vr_file,'* localizing all parameters in subcircuit\n');
   fprintf(vr_file,'* preventing interference between parameters in other files\n');
   fprintf(vr_file,'* allowing override of values on subcircuit calls\n');
   fprintf(vr_file,'* and use of \".alter\" to run multiple cases at a time\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'.option parhier=local\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'*****************************************************\n');
   fprintf(vr_file,'* State Average Model  \n');
   fprintf(vr_file,'*****************************************************\n');
   fprintf(vr_file,'.option acout=1 \n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'.subckt vrstavggen sensep sensen g0 ');
   for i=1:pha
      fprintf(vr_file,'p%d ',i);
   end
   fprintf(vr_file,'\n');
   fprintf(vr_file,'*Connect \"sensep\" to positive differential feedback sense point\n');
   fprintf(vr_file,'*Connect \"sensen\" to negative differential feedback sense point\n');
   fprintf(vr_file,'*Connect \"g0\" to \"0\" for single-ended model or a reasonable VR ground connection node for a dual-ended model. This should be at or near the ground node equivalent to the phase node(s)\n');
   fprintf(vr_file,'*Connect \"px\" to the phase inductor(s) output nodes\n');
   fprintf(vr_file,'* Parameters used in the model\n');
   fprintf(vr_file,'.param\n');
   fprintf(vr_file,'+ r1 = ''%fk''\n',compensator_val(1));
   fprintf(vr_file,'+ r2 = ''%fk''\n',compensator_val(2));
   fprintf(vr_file,'+ r3 = ''%fk''\n',compensator_val(3));
   fprintf(vr_file,'+ c1 = ''%fp''\n',compensator_val(4));
   fprintf(vr_file,'+ c2 = ''%fn''\n',compensator_val(5));
   fprintf(vr_file,'+ c3 = ''%fn''\n',compensator_val(6));
   fprintf(vr_file,'+ duty = ''75'' * Maximum duty cycle in percentage\n');
   fprintf(vr_file,'+ egain = ''4000'' * Gain of error amp\n');
   fprintf(vr_file,'+ lout = ''%.6fn'' * The per phase inductor value in Henries\n',lout);
   fprintf(vr_file,'+ avp = ''%.6f'' * Adaptive Voltage Positioning setting in ohms\n',avp);
   fprintf(vr_file,'+ rout = ''%.6fm'' * dcr resistance of output inductor per phase value in ohms\n',rout);
   fprintf(vr_file,'+ vid = ''%g'' * Output setpoint in volts\n',VID);
   fprintf(vr_file,'+ vin = ''12'' * Input voltage. Usually 12V\n');
   fprintf(vr_file,'+ vramp = ''1.5'' * peak ramp voltage in volts\n');
   fprintf(vr_file,'+ np = %d * number of phases. Can be 1, 2, 3, 4, 5, 6, 7 ,8 ,9 or 10.\n',pha);
   fprintf(vr_file,'* Parameters NOT used in the model\n');
   fprintf(vr_file,'+ fs = 300000 * per phase switching frequency\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'* Compensation network\n\n');
   if (tuning == 1)
      fprintf(vr_file,'r1 compin fb ''r1''\n');
      fprintf(vr_file,'r2 fb r2c2 ''r2''\n');
      fprintf(vr_file,'r3 compin r3c3 ''r3''\n');
      fprintf(vr_file,'c1 fb comp ''c1''\n');
      fprintf(vr_file,'c2 r2c2 comp ''c2''\n');
      fprintf(vr_file,'c3 r3c3 fb ''c3''\n');
      fprintf(vr_file,'\nVfdbk compin diff dc 0 ac 1m\n\n');
      fprintf(vr_file,'.probe ac\n');
      fprintf(vr_file,'+ vdb(diff,compin),vp(diff,compin)  ** closed loop\n');
      fprintf(vr_file,'+ vdb(diff,comp),vp(diff,comp)      **plant\n');
      fprintf(vr_file,'+ vdb(comp,compin),vp(comp,compin)\n'); 
   else 
      fprintf(vr_file,'r1 diff fb ''r1''\n');
      fprintf(vr_file,'r2 fb r2c2 ''r2''\n');
      fprintf(vr_file,'r3 diff r3c3 ''r3''\n');
      fprintf(vr_file,'c1 fb comp ''c1''\n');
      fprintf(vr_file,'c2 r2c2 comp ''c2''\n');
      fprintf(vr_file,'c3 r3c3 fb ''c3''\n');
   end
   fprintf(vr_file,'\n');
   fprintf(vr_file,'* Error \"amp\"\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'vvid vid g0 ''vid''\n');
   fprintf(vr_file,'ecomp comp g0 vcvs vid fb ''egain'' max=''vramp''\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'* Differential sense input calculation\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'ediff diff g0 vol=''v(sensep,g0)-v(sensen,g0)''\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'.if (avp!=0)\n');
   fprintf(vr_file,'   gdroop fb g0 vol=''i(eout)*avp/r1''\n');
   fprintf(vr_file,'.endif\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'* Output\n');
   fprintf(vr_file,'\n');
   fprintf(vr_file,'eout swn g0 vol=''vin*v(comp,g0)/vramp'' max=''vin*duty/100''\n\n');
   fprintf(vr_file,'lp1 swn lp1rp1 ''lout''\n');
   fprintf(vr_file,'rp1 lp1rp1 p1 ''rout''\n');
   fprintf(vr_file,'.probe ac v(p1)* dummy probe remove after model is complete\n');
   fprintf(vr_file,'\n');
   if (pha > 1)
      for i=2:1:pha
         fprintf(vr_file,'lp%d swn lp%drp%d ',i,i,i);
	 fprintf(vr_file,' ''lout''\n');
         fprintf(vr_file,'rp%d lp%drp%d p%d ',i,i,i,i);
         fprintf(vr_file,' ''rout''\n\n');
      end	     
   end	
  fprintf(vr_file,'\n.ends\n');
  fclose(vr_file); 


end


