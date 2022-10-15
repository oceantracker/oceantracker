function d= OTreadGrid(filename, var_names_cell)

if nargin < 2
    var_names_cell={};     
end

[d, info] = readNCvarsOT(filename,var_names_cell,{'triangles','adjacency'});

d.y= d.x(:,2);
d.x= d.x(:,1);
d.xy= d.x+1i*d.y; % complex node locations



    


