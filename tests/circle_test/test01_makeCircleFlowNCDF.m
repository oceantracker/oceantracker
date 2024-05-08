% create exmaple flows for range of grid sizes

nxlab='TSML';
nx= [2 10 50 150];
dt_days=1./24/4;


for nsize=1:length(nx)
    % write  parts to a series of files to test blocking
    
    
    for nCase = [1, 11]
     
        switch nCase
            case 1
                % 2D  eddy
                fn='circFlow2D';
                is3D= false;
                days_per_file=5;
                tmax_days =30;
            case 11
                % 3D eddy, s grid
                is3D= true;
                fn='circFlow3D';
                days_per_file=1;
                tmax_days=7;
        end     
        
        t0=10;
        fn= [fn nxlab(nsize) ];   
        clear d
        for nf=1:floor(tmax_days/days_per_file)
            time=t0+ (nf-1)*days_per_file+ (0:dt_days:days_per_file-dt_days)';
            d=makeCircleExample('nx',nx(nsize),'time',time*24*3600,'is3D',is3D);
            
            f=[ 'F:\HindcastReWrites\oceantrackerFMT\circleTest\' fn int2str(nf) '.nc'];
            
            if nsize==1 & nCase==1 | (nsize==1 & nCase==11 & nf ==1)
               delete([f '*.nc'],'file')  % remove old stufff
               % also put  small test files in module dir
               ftest=['testData\' fn int2str(nf) '.nc'];
               delete(ftest)
               WriteNCDFadvectorFile(d,ftest)
            end
            
          
            disp(f)
            WriteNCDFadvectorFile(d,f)
            
        end
        
    end
    %%
end


NCDFinfo(f)
r=NCDFread(f);

%% check time between files is continuous
files=dir( ['testData\circFlow2DT*.nc']);
t=[];
for n=1:length(files)
   r=NCDFread([files(n).folder '\' files(n).name ]);
   t=[t;r.time];
end

plot(diff(t))

