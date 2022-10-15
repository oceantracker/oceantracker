% test basic read outputs in matlab

output_dir = '../../demos/output/demo02_animation/';

info= OTreadInfo([output_dir,'demo02_animation_runInfo.json'],1);


% track read of compact output format
d=OTreadTracks([output_dir,info.caseInfo.output_files.tracks_writer{1}]);
figure(1)
triplot(info.grid.triangles,info.grid.x,info.grid.y,'color',.8*[ 1 1 1]);
hold on
plot(d.x(:,:,1),d.x(:,:,2))
hold off

figure(2)
plot(d.time/24/3600+datenum(1970,1,1),d.tide)
datetick


%% read time stats
output_dir = '../../demos/output/demo03_heatmaps/';
info= OTreadInfo([output_dir,'demo03_heatmaps_runInfo.json'],1);
for sf = info.caseInfo.output_files.particle_statistics'
    s= OTreadStats([output_dir,sf{1}]);
end

%% read age  stats
output_dir = '../../demos/output/demo04_ageBasedHeatmaps/';
info= OTreadInfo([output_dir,'demo04_ageBasedHeatmaps_runInfo.json'],1);
for sf = info.caseInfo.output_files.particle_statistics'
    s= OTreadStats([output_dir,sf{1}]);
end