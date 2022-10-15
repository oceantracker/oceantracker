function d= OTreadTracks(filename, var_names_cell)

if nargin < 2
    var_names_cell={};     
end

[d, info] = readNCvarsOT(filename,var_names_cell,{'x','ID','IDrelease_group','IDpulse','n_cell'}); 

    
f=fieldnames(d.var_info);
wID=d.write_step_index+1; % copy for use in reshaping
pID=d.particle_ID;
for n=1:length(f)
    vn = f{n};
    if any(strcmp(d.var_info.(vn).dims, 'time_particle'))
        % put compact tracks into rectangular form (time, parriulce)
        ncomp= size( d.(vn),2);
        
        % below faster when comp initially first
        data = ones(ncomp, d.dim_info.time, d.dim_info.particle)*double(d.var_info.(vn).FillValue);
        for nn = 1:ncomp
            data(nn, pID*d.dim_info.time+ wID) = d.(vn)(:,nn);
        end
     
        d.(vn)= squeeze(shiftdim(data,1));
    end
    
end
a=1;
