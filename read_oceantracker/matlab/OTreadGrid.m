function d= OTreadGrid(filename,n_grid)



[d, info] = readNCvarsOT(filename);

d.y= d.x(:,2);
d.x= d.x(:,1);
d.xy= d.x+1i*d.y; % complex node locations

d.triangles = d.triangles +1; % matlab is one based indices



    


