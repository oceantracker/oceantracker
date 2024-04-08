function d= OTreadReleaseGroups(filename)

rgs = readNCvarsOT(filename);
d=[];
fn = fieldnames(rgs);
for n= 1: length(fn)
  v = fn{n};
  if ~startsWith(v,'ReleaseGroup'), continue;end
  info =  rgs.var_info.(v);
 
  dd = struct('release_type',info.release_type, 'points',rgs.(v),'name', info.release_group_name);
  d=  [d,dd];
  
 
end

