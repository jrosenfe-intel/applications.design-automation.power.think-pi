function [x, TFini, TFtune, Zo, G, fit_z, f_z, Ns_z, freq_z, fit_g, f_g, Ns_g, freq_g] = tune_wo_ll(Zo_data, G_data, vin, vramp, rll, x0, f0, PHmarg, Nz, Ng, itr)
%UNTITLED2 Summary of this function goes here
%   Detailed explanation goes here
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%plant transfer funtion
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%VF
% This section takes 2 input matix that represent the Z_load and the Plant transfer fution
% and calculate the transfer funtion for the plant, compensator and the full system.
% This program call the funtion vectfit2.m, Written by: Bjorn Gustavsen   
%%%%%%%%%%%%%%%%%%%%%% Vector fitin fot the Zload %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
freq=Zo_data(:,1);
A1=Zo_data(:,2);
A2=Zo_data(:,3);
w=2*pi*freq;
s=i.*w; Ns=length(s);
for k=1:Ns
	f1=A1(k);
	f2=A2(k);
	f(k)=f1+i*f2;
end
%=====================================
% Rational function approximation of f(s):
%=====================================

N=Nz; %Order of approximation 

%Complex starting poles :
bet=linspace(w(1),w(Ns),N/2);
poles=[];
for n=1:length(bet)
  alf=-bet(n)*1e-2;
  poles=[poles (alf-i*bet(n)) (alf+i*bet(n)) ]; 
end

weight=ones(1,Ns); %No weighting
%weight=1./abs(f); %Weighting with inverse of magnitude function

VF.relax=1;      %Use vector fitting with relaxed non-triviality constraint
VF.kill=2;       %Enforce stable poles
VF.asymp=1;      %Include only D fitting    
VF.skip_pole=0;  %Do not skip pole identification
VF.skip_res=0;   %Do not skip identification of residues (C,D,E) 
VF.use_normal=0; %Use Normal Equations
VF.use_sparse=1; %Use sparse computations
VF.cmplx_ss=0;   %Create real-only state space model

VF.spy1=1;       %No plotting for first stage of vector fitting
VF.spy2=0;       %Create magnitude plot for fitting of f(s) 
VF.logx=1;       %Use linear abscissa axis
VF.logy=1;       %Use logarithmic ordinate axis 
VF.errplot=0;    %Include deviation in magnitude plot
VF.phaseplot=1;  %Include plot of phase angle
VF.legend=0;     %do NOT include legends in plots

disp('vector fitting...')
Niter=itr;
for iter=1:Niter
  if iter==Niter, VF.legend=1; end %Include legend in final plot
  disp(['   Iter ' num2str(iter)])
  [SER,poles,rmserr,fit_z,f_z,Ns_z,freq_z]=vectfit2_for_gui(f,s,poles,weight,VF,0); 
  rms(iter,1)=rmserr;
end
disp('Done.')
clear s
[Npole,temp]= size(SER.A);%vector size
%Npole=Nz;
s = tf('s');
I=eye(Npole);
Zo=SER.C*(1/(s*I-SER.A))*SER.B+SER.D; %%%%% This is the Zload
clear s;
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%plant transfer funtion
clear SER
freq=G_data(:,1);
A_p=G_data(:,2);
B_p=G_data(:,3);

w=2*pi*freq;
s=i.*w; Ns=length(s);
for k=1:Ns
	f1=A_p(k);
	f2=B_p(k);
	f(k)=f1+i*f2;
end
%=====================================
% Rational function approximation of f(s):
%=====================================

N=Ng; %Order of approximation 

%Complex starting poles :
bet=linspace(w(1),w(Ns),N/2);
poles=[];
for n=1:length(bet)
  alf=-bet(n)*1e-2;
  poles=[poles (alf-i*bet(n)) (alf+i*bet(n)) ]; 
end

weight=ones(1,Ns); %No weighting
%weight=1./abs(f); %Weighting with inverse of magnitude function

% VF.relax=1;      %Use vector fitting with relaxed non-triviality constraint
% VF.kill=2;       %Enforce stable poles
% VF.asymp=1;      %Include only D fitting    
% VF.skip_pole=0;  %Do not skip pole identification
% VF.skip_res=0;   %Do not skip identification of residues (C,D,E) 
% VF.use_normal=0; %Use Normal Equations
% VF.use_sparse=1; %Use sparse computations
% VF.cmplx_ss=0;   %Create real-only state space model
% 
% VF.spy1=0;       %No plotting for first stage of vector fitting
% VF.spy2=1;       %Create magnitude plot for fitting of f(s) 
% VF.logx=1;       %Use linear abscissa axis
% VF.logy=1;       %Use logarithmic ordinate axis 
% VF.errplot=1;    %Include deviation in magnitude plot
% VF.phaseplot=1;  %Include plot of phase angle
% VF.legend=0;     %do NOT include legends in plots

disp('vector fitting...')
Niter=itr;
for iter=1:Niter
  if iter==Niter, VF.legend=1; end %Include legend in final plot
  disp(['   Iter ' num2str(iter)])
  [SER,poles,rmserr,fit_g,f_g,Ns_g,freq_g]=vectfit2_for_gui(f,s,poles,weight,VF,2); 
  rms(iter,1)=rmserr;
end
disp('Done.')
clear s
[Npole,temp]= size(SER.A);%vector size
%Npole=Ng; % fix due to the order of the vector fitting order
s = tf('s');
I=eye(Npole);
G=SER.C*(1/(s*I-SER.A))*SER.B+SER.D; %%%%%% This is the plant transfer funtion
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

Ga= G*(vin/vramp); %open loop gain
w0 = 2*pi()*f0;
H = evalfr(Ga,1j*w0);
f = 20*log10(abs(H));
f = -1*f;
phi = angle(H)*180/pi;
if phi > 0
 phi= phi-360;
end

PH_boost = PHmarg-phi-90;
K= (tan(((PH_boost*pi/180)/4)+45*pi/180))^2;
R1 = 4000;  
R3 = (R1/(K-1)); 
C1 = (1/(w0*(10^(f/20)*R1)));
C2 = C1*(K-1);
C3 = (1/(w0*sqrt(K)*R3));
R2 = (sqrt(K)/(w0*(C2)));

x(1)=R1/1000;
x(2)=R2/1000;
x(3)=R3/1000;
x(4)=C1/50e-12;
x(5)=C2/1e-9;
x(6)=C3/1e-9;

TF2 = @(x)System2(x,vin,vramp,rll,Ga,Zo);

TFini = TF2(x0);
TFtune = TF2(x);
end

function TF2 = System2(x,vin,vramp,rll,G,Zo)


R1 = x(1)*1000;
R2 = x(2)*1000;
R3 = x(3)*1000;
C1 = x(4)*50e-12;
C2 = x(5)*1e-9;
C3 = x(6)*1e-9;

s = tf('s');
k0 = vin*rll/vramp;
z1 = (R1*(R3*C3*s+1))/(C3*s*(R3+R1)+1);
z2 = (R2*C2*s+1)/(s*(C1*C2*R2*s+(C1+C2)));
H1= z2/z1;

z3 = z2/R1;
H2 = 1/(1+k0*z3/Zo);

H = H1*H2;
%%%%%%% order reduction
%if (rll ~= 0) && (order(G) > 23)  %if rll = 0, no order reduction is needed
%[hsv,baldata] = hsvd(H);
%H = balred(H,20,baldata);
%[hsv,baldata] = hsvd(G);
%G = balred(G,20,baldata);
%end 
TF2 = G*H;


end





