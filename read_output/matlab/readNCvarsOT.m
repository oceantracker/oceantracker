function [d, info] = readNCvarsOT(filename,var_names_cell,index_vars)

ncid = netcdf.open(filename,'NC_NOWRITE');

if nargin < 2,  var_names_cell={}; end
if nargin < 3,  index_vars={}; end

info=ncinfo(filename);
d= struct('dim_info',struct,'var_info',struct);
for v = info.Variables(:)'
    vname=v.Name;
    if  length(var_names_cell) > 0  && ~any(contains(var_names_cell,vname)), continue;end
    
    % read data
    varid = netcdf.inqVarID(ncid,vname);
    data= netcdf.getVar(ncid,varid); 
    
    % put dims order back as c convection in net cdf
    if size(data,2) > 1 | ndims(data) > 2
        data =permute( data, [ndims(data):-1:1]);
    end
    
    d.(vname) = double(data);
    
    if any(contains(index_vars,vname))
        % matlab has 1 based indicies
        d.(vname)= d.(vname)+1;        
    end
    
    d.var_info.(vname)= struct;
    for a = v.Attributes(:)'
        d.var_info.(vname).(strip(a.Name,'_')) = a.Value;
    end   
    
    % get dims for var in reversed order to match permute above
    d.var_info.(vname).dims={};
    
    for nn=1:length(v.Dimensions)
        d.var_info.(vname).dims{length(v.Dimensions) -nn +1} = v.Dimensions(nn).Name;
    end
    a=1;
    
   
   

end

for a = info.Attributes(:)'
    d.(a.Name)=a.Value;
end

for dim= info.Dimensions(:)'
    d.dim_info.(dim.Name)=dim.Length;
end

netcdf.close(ncid);
