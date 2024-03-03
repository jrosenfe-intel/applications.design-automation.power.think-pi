function result=tune_vr(pha,rll,vin,vramp,f0,PHmarg,lout,rout,VID,touchstoune_file,includePath,comp_file)                     
%pha=2  %count
%rll=0.5 %mOhms
%vin=12 %V
%vramp=1.5 %V
%f0=100e3 %Hz
%PHmarg=60 %deg
%lout=100 %nH
%rout=0.29 %mO
%VID=1 %V
%--- Vector Fitting VARIABLES ---
    tol = 1;  % ph margin tolerance in degrees
    Nz = 20;  % 6 a 20
    Ng = 15;
    itr = 6; % iteraciones maximas del curve fit 5 a 10.
 %--- Optimizer VARIABLES ---
    Rmin =0.001;        Rmax = 50;   %kOhm
    Cmin = 0.01;       Cmax = 40;   %nF
    x0 = [4;Rmin;4*Rmin;Cmax;Cmax/2;5*Cmin];
    alg ='sqp' % options 'trust-region-reflective', 'active-set', 'interior-point' & 'sqp'
    

    
%vr_phases
%--- DATA FROM GUI ---
    % pha=str2double(get(handles.phNodes_number_textField,'String'));
    % vr_phases=transpose(strread(get(handles.PhNodes_TextField,'String'),'%s','delimiter',', '));
    % rll = str2double(get(handles.avp_textField,'String'));
    % %vin = str2double(get(handles.Vin_TextField,'String'));
    % %vramp = str2double(get(handles.Vramp_TextField,'String'));
    % vin = handles.Vin;
    % vramp = handles.Vramp;
    % f0 = str2double(get(handles.BW_TextField,'String'));
    % PHmarg = str2double(get(handles.PHmarg_TextField,'String'));
    % sense=get(handles.sense_node_tf,'String');
    % lout=str2double(get(handles.Lout_TF,'String'));
    % rout=str2double(get(handles.Rout_TF,'String'));
    % VID=str2double(get(handles.VID_TF,'String'));


    %--- TOUCHSTONE FILE NEEDS TO BE THIS NAME!
    %touchstoune_file=sprintf('%sshell_deck_AVP1p2_plant_touch_roch',handles.includePath);
    %touchstoune_file=sprintf('%s.s2p',touchstoune_file);
    
    %if exist(touchstoune_file, 'file')
    %    log_append(hObject, handles,sprintf('Touchstone file successfuly read: %s%s',char(13),touchstoune_file));
    %    %log_append(hObject, handles,'Touchstone file successfuly created:');
    %else
    %    log_append(hObject, handles,sprintf('##ERROR unable to read: %s',touchstoune_file));
    %    %set(handles.GoButton,'Enable','on');
    %    set(handles.build_pushbutton,'Enable','on');
    %    set(handles.loadGO_pushbutton,'Enable','on');
    %    return;
    %end
    
   
%********** OPTIMIZE AND TUNE **************
    [Freq, Zl, plant] = GetTF(touchstoune_file);
    
    Zl= [Freq, real(Zl),imag(Zl)];
    plant= [Freq, real(plant), imag(plant)];

   
    
    
    
    %[x,fval,exitflag,output,TFini,TFtune] = SymOptimizer_core2(Zl,plant,vin,vramp,rll,x0,f0,PHmarg,tol,Nz, Ng);
    
    %log_append(hObject, handles,sprintf('Vector Fit: tol=%g Nz=%g Ng=%g itr=%g',tol,Nz,Ng,itr));
    %$log_append(hObject, handles,'Optimization in progress, please wait...');
    
    drawnow();
    
    %[x, TFini, TFtune, Zo, G] = tune_wo_ll (Zl, plant, vin, vramp, 0, x0, f0, PHmarg, Nz, Ng, itr);    
    
    try
        [x, TFini, TFtune, Zo, G, fit_z, f_z, Ns_z, freq_z, fit_g, f_g, Ns_g, freq_g] = tune_wo_ll (Zl, plant, vin, vramp, 0, x0, f0, PHmarg, Nz, Ng, itr);
    catch err
        disp(err.message)
        %log_append(hObject, handles,sprintf('%s',err.message));
        %log_append(hObject, handles,['###ERROR: ' err.message]);
    end
    
    fit_z = transpose(fit_z);
    freq_z = freq_z;
    fit_g = transpose(fit_g);
    freq_g = freq_g;
    z_vf_error=f_z -  fit_z;
    g_vf_error=f_g - fit_g;
    
    if rll ~= 0
        try
            %A = rand(3);
            %B = ones(5);
            %C = [A; B];
            
            [x,fval,exitflag,output,TFini_unused,TFtune] = SymOptimizer_core3(Zo,G,vin,vramp,rll,x,f0,180-PHmarg,tol, alg);
            [x,fval,exitflag,output,TFini_unused,TFtune] = SymOptimizer_core3(Zo,G,vin,vramp,rll,x,f0,180-PHmarg,tol,'interior-point')
        catch err
            %log_append(hObject, handles,sprintf('%s',err.message));
            %log_append(hObject, handles,['###ERROR: ' err.message]);
        end
    end
    %log_append(hObject, handles,'Optimization finished');

    MAG=20*log10(abs(evalfr(TFtune,2*pi*1i*f0)))
    PHI=(unwrap(angle(evalfr(TFtune,2*pi*1i*f0))))*180/pi
    PM= PHI+180

    %fprintf('Gain at BW=%g\n',MAG);
    %$sprintf('PHI=%g',PHI);
    %sprintf('PM=%g',PM);
    
    %log_append(hObject, handles,sprintf('Gain at BW=%g',MAG));
    %log_append(hObject, handles,sprintf('PHI=%g',PHI));
    %log_append(hObject, handles,sprintf('PM=%g',PM));
    
    if order(TFini) > 23
        %log_append(hObject, handles,'started TFini balred');
        TFini=balred(TFini,20);
        %log_append(hObject, handles,'finished TFini balred');
    end
    
     if order(TFtune) > 23
        %log_append(hObject, handles,'started TFtune balred');
        TFtune= balred(TFtune,20);        
        %log_append(hObject, handles,'finished TFtune balred');
    end
    
    TFini=TFini;
    TFtune=TFtune;
    
    %figure;
    %stepplot(TFtune/(1+TFtune),300e-6);figure(gcf);
    %figure;
    %nyquistplot(TFtune/(1+TFtune));figure(gcf);
    
    % C1 is normalized to 50.  Need to multipy x50 to denormalize.
    x(4) = x(4) * 50;
    
	%this section saves the vr model file
	%%tuning=0;    
    %%generate_vr_file_flag = generate_vr_model(includePath,pha,tuning,x,rll,lout,rout,VID);
    %%if generate_vr_file_flag==-1
    %%    %log_append(hObject, handles,'Failed to create VR include file');
    %%else
    %%    %log_append(hObject, handles,sprintf('Successfully generated: %svrstavggen_%d_ph.inc',handles.includePath,pha));
    %%end
    %%
    %%tuning=1;
    %%generate_vr_file_flag = generate_vr_model(includePath,pha,tuning,x,rll,lout,rout,VID);
    %%if generate_vr_file_flag==-1
    %%    %log_append(hObject, handles,'Failed to create VR include file');
    %%else
    %%    %log_append(hObject, handles,sprintf('Successfully generated: %svrstavggen_%d_ph_BODE.inc',handles.includePath,pha));
    %%    %log_append(hObject, handles,sprintf('INFO: Please verify results in HSPICE using %svrstavggen_%d_ph_BODE.inc as this is a mathematical approsximation.',handles.includePath,pha));
    %%end
    
    %save compensation parameters
    r1 = sprintf('%.4fk', x(1));  % 4 decimal places
    r2 = sprintf('%.4fk', x(2));  % 4 decimal places
    r3 = sprintf('%.4fk', x(3));  % 4 decimal places
    c1 = sprintf('%.4fp', x(4));  % 4 decimal places
    c2 = sprintf('%.4fn', x(5));  % 4 decimal places
    c3 = sprintf('%.4fn', x(6));  % 4 decimal places
    save_csv(comp_file,{'r1','r2','r3','c1','c2','c3'},{r1,r2,r3,c1,c2,c3})
    %CLF;
    %CLA;
    %P = bodeoptions; 
    %P.FreqUnits = 'Hz'; % Create plot with the options specified by 
    %P.MagScale = 'linear';
    %P.PhaseWrapping = 'off';
    %figure(handles.axes1);
    %bode(handles.TFini, 'b',handles.TFtune, 'r--',{1, 100e6},P);
    
    %set(handles.GoButton,'Enable','on');
    %set(handles.build_pushbutton,'Enable','on');
    %set(handles.loadGO_pushbutton,'Enable','on');
        
    % Enable popupmenu3 --> plot selector
    %set(handles.popupmenu3,'Enable','on');
    %figure(hObject);
    %popupmenu3_Callback(handles.popupmenu3, eventdata, handles);
    result=1