function d= OTreadTracks(filename, var_names_cell)

if nargin < 2
    var_names_cell={};
end


info= readNCinfoOT(filename);

if isfield(info.Dimensions, 'time_particle')
    default_vars= {'time','x','write_step_index','particle_ID'};    
else
    default_vars={'time','x'};
end


d = readNCvarsOT(filename,var_names_cell,{'ID','IDrelease_group','IDpulse','n_cell'},default_vars);


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
