ncase=1;
tag='_B';
tag='_F';
dir='D:\OceanTrackerOuput\circleTests\';
if ncase==1
    rn=[dir 'circFlow2D'];
    fn='test_particle';

else
    rn=[dir  'circFlow3D'];
    fn='test_particle';

end

ff=[rn '\' fn tag];
%g=NCDFread([rn '/grid.nc']);
d=otRead_track_file2(ff);

%NCDFinfo(ff)
% deimate fro plotting
sel=1:1:size(d.x,2);


xyi=d.xy;

clf

subplot(3,2,1)

triplot(d.tri,d.grid_x(:,1),d.grid_x(:,2),'color',.8*[1 1 1 ])
hold on
plot(d.grid_x(d.grid_boundary_nodes,1),d.grid_x(d.grid_boundary_nodes,2),'g.');

plot(xyi,'-')

plot(d.xy_lastGood(d.status(end,:)==0),'o')

% use start points to plot circiles
ndim=size(d.x,3);

if isfield(d,'x0Info_x0')
    xy0=d.x0Info_x0(:,1)+1i*d.x0Info_x0(:,2)+100i*eps;
    plotcirc(0,abs(xy0),'--');
    plot(xy0,'g.')
else
   for n=1:length(d.polygons)
       xy=d.polygons{n}(:,1)+i*d.polygons{n}(:,2);
       plot(xy,'k--')
   end
end

plot(d.xy0_actual,'k.')
hold off

subplot(3,2,2)
plot(d.time/3600/24,bsxfun(@minus,abs(xyi),abs(d.xy0_actual.') ) )
title(' Deviation from circle')

subplot(3,2,3)

hl=plot(d.time(2:end)/3600/24,cumsum(abs(diff(xyi))) );
title('Horizontal Dist Traveled')


subplot(3,2,4)

plot(d.time(2:end)/3600/24,abs(diff(xyi))./diff(d.time),'-')
title('Particle Speed')

subplot(3,2,5)
plot(d.time,d.status)
title('Status')

subplot(3,2,6)
if ncase==1
  plot(d.time,d.depth)
  
else
    plot(d.time/3600/24,d.x(:,:,3))
end

disp(ff)
% s=NCDFread([rn '/' rn '_P1stats.nc']);
% subplot(3,2,6)
% pcolor(sum(s.grid_count(:,:,:,end-20)+1,3))
% shading interp

%pcolor(s.grid_count(:,:,4,end))
%shading interp