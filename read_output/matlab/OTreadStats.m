function d= OTreadStats(filename, var_names_cell)

if nargin < 2
    var_names_cell={};     
end

d = readNCvarsOT(filename,var_names_cell,{''},{'count','count_all_particles'});

% turn sums into mean values
for var = fieldnames(d.var_info)'
   v=var{1};
   if length(v) > 3 &&  strcmp(v(1:4),'sum_')
     d.([v(5:end) '_mean' ]) = d.(v)./d.count;
   end
end

    

