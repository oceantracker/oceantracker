function d= OTreadTracks(filename, var_names_cell)

if nargin < 2
    var_names_cell={};     
end

[d, info] = OTreadNCvars(filename,var_names_cell,{'ID','IDrelease_group','IDpulse','n_cell'}); 

    

