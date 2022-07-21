function [d, info] = OTreadNCvars(filename,var_names_cell,index_vars)

ncid = netcdf.open(filename,'NC_NOWRITE');

if nargin < 2,  var_names_cell={}; end
if nargin < 3,  index_vars={}; end

info=ncinfo(filename);
d= struct;
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
    
    d.([vname '_info'])= struct;
    for a = v.Attributes(:)'
        d.([vname '_info']).(strip(a.Name,'_')) = a.Value;
    end
    
    d.([vname '_info']).dims={};
    for n= 1:length(v.Dimensions(:))
         d.([vname '_info']).dims{length(v.Dimensions(:))-n+1} = v.Dimensions(n).Name;
    end
   

end

for a = info.Attributes(:)'
    d.(['attr_' a.Name])=a.Value;
end

for dim= info.Dimensions(:)'
    d.(['dim_' dim.Name])=dim.Length;
end

netcdf.close(ncid);
