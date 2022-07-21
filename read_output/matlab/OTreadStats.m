function d= OTreadStats(filename, var_names_cell)

if nargin < 2
    var_names_cell={};     
end

[d, info] = readNCvars(filename,var_names_cell,{''});

% turn sums into mean values
for var = info.Variables(:)'
   v=var.Name;
   if length(v) > 3 &&  strcmp(v(1:4),'sum_')
     d.([v(5:end) '_mean' ]) = d.(v)./d.count;
   end
end

    

