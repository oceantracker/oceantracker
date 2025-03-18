%% basic demo of reading and plotting oceantracker output files in matlab

%output_dir = '../../demos/output/demo02_animation/';
output_dir ='../../../oceantracker_output/unit_tests/unit_test_08_statistics_00/'


% read case info, eg outputfilenames etc
fn =[output_dir,'unit_test_08_statistics_00_caseInfo.json']
info= OTreadInfo(fn);

% read grid file, using name from info, there may be more than one grid if nested
grid= OTreadGrid([output_dir,info.output_files.grid{1}]);

release_groups= OTreadReleaseGroups([output_dir,info.output_files.release_groups]);

%% plot tracks
% read tracks file, using name from info, if tracks a split into time steps may be more

% than one tracks file, here take the first
tracks=OTreadTracks([output_dir,info.output_files.tracks_writer{1}],{'x','tide'});

figure(1)
% show grid
triplot(grid.triangles,grid.x,grid.y,'color',.8*[ 1 1 1]);
hold on
plot(tracks.x(:,:,1),tracks.x(:,:,2))

% plot release points or polygons from  info.release_group
for rg1  = release_groups % cell array of release groups
    rg = rg1{1};
    switch rg.release_type
        case 'point'    
            plot(rg.points(:,1), rg.points(:,2),'g.','markersize',18)
            
        case 'polygon'
            plot(rg.points(:,1), rg.points(:,2),'g-','linewidth',2)
        case 'grid'
            plot(rg.points(:,:,1), rg.points(:,:, 2),'g.','markersize',18)
    end
end
title('Tracks in demo domain')
hold off

figure(2)
plot(tracks.time/24/3600+datenum(1970,1,1),tracks.tide)
ylabel('Tide at particle locations')
datetick


%% read gridded time stats

%get info from user given name "gridstats1"
fn = info.output_files.particle_statistics.my_heatmap;
s = OTreadStats([output_dir,fn]);

% plot counts for release group 1 at last time step on log scale
% counts are dim(time, release_group,x,y)
figure(3)
n = 1;
[x,y]= meshgrid(s.x(n,:),s.y(n,:));
pcolor(x,y,log10(squeeze(s.count(end,n,:,:))))
shading interp
hold on

% put grid on top
triplot(grid.triangles,grid.x,grid.y,'color',.8*[ 1 1 1]);
hold off
colorbar
title('Particle heat map release group 1, , log scale')
% user requested water_depth heat map so plot it

figure(4)
n = 1;
pcolor(x,y,squeeze(s.water_depth(end,n,:,:)))
shading interp
colorbar
title('Water depth heat map at particle locations at last time step, release group 1')
hold on

% put grid on top
triplot(grid.triangles,grid.x,grid.y,'color',.8*[ 1 1 1]);
hold off

%% read polygons stats and  conectivity probalities
fn = info.output_files.particle_statistics.my_poly_stats;
p = OTreadStats([output_dir,fn]);

% calc connectity betwen each release group and this polygon, number 1 as a
% time series


figure(5)
plot(p.day,p.connectivity(:,1))
datetick
title('Connectivty betwen release group 1s two points and the polygon of release group 2')
xlabel('time')