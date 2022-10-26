function [d, info] = readNCvarsOT(filename,var_names_cell,index_vars,default_vars)
% indev vars are those to convert from zero based to one based 
ncid = netcdf.open(filename,'NC_NOWRITE');



if nargin < 2,  var_names_cell={}; end
if nargin < 3,  index_vars={}; end
if nargin < 4,  default_vars={}; end

info= readNCinfoOT(filename);

% load all if varnames not given
if length(var_names_cell)==0
        var_names_cell=fieldnames(info.Variables)';
end

var_names_cell= unique([var_names_cell(:)'  default_vars(:)' ]);

d= struct('dim_info',struct,'var_info',struct);

for v = var_names_cell
    vname=v{1};
    if ~isfield(info.Variables,vname)
        disp(['OT read netcdf, cannot find variable ' v ])
        continue
    end
    
    vi=info.Variables.(vname);    

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
    for a = vi.Attributes(:)'
        d.var_info.(vname).(strip(a.Name,'_')) = a.Value;
    end   
    
    % get dims for var in reversed order to match permute above
    d.var_info.(vname).dims={};
    
    for nn=1:length(vi.Dimensions)
        d.var_info.(vname).dims{length(vi.Dimensions) -nn +1} = vi.Dimensions(nn).Name;
    end
    a=1;
    
   
   

end


for fn=  fieldnames(info.Attributes)'
    d.(fn{1})=info.Attributes.(fn{1});
end

for  fn=  fieldnames(info.Dimensions)' 
    d.dim_info.(fn{1})=info.Dimensions.(fn{1});
end

netcdf.close(ncid);
