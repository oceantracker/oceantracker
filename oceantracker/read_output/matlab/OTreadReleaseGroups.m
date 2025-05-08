function d= OTreadReleaseGroups(filename)

rgs = readNCvarsOT(filename);
d={};
fn = fieldnames(rgs);
for n= 1: length(fn)
  v = fn{n};
  if ~startsWith(v,'ReleaseGroup'), continue;end
  info =  rgs.var_info.(v);
 
  dd = struct('release_type',info.release_type, 'points',rgs.(v),'name', info.release_group_name);
  if size(dd.points,2)==1
      % single point
      dd.points = dd.points.';
  end
  
  d{length(d)+1}=  dd;

 
end



