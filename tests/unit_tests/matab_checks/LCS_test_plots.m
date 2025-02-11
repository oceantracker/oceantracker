% romains
r= NCDFread('E:\H_Local_drive\ParticleTracking\hindcast_formats_examples\generic2D_structured_DoubleGyre\Double_gyre.nc');

%OT output
d= NCDFread('unit_test_80_LagrangianStructuresFTLE_01_doubleGyre\unit_test_80_LagrangianStructuresFTLE_01_doubleGyre_LCS.nc');


figure(1)
pcolor(r.X0,r.Y0,r.FTLE)
colormap(red_blue_colormap)
shading interp
colorbar
axis([0,2,0,1])
title('Romain')

figure(2)
x= d.x_LSC_grid(:,:,1);
y= d.x_LSC_grid(:,:,2);
pcolor(x,y,d.FTLE)
hold on 

% first eigen vector
nn=4;
xy2 =x(1:nn:end,1:nn:end)+i*y(1:nn:end,1:nn:end);

v = d.eigen_vectors(1:nn:end,1:nn:end,1,1)+i *d.eigen_vectors(1:nn:end,1:nn:end,2,1);
ev = d.eigen_values(1:nn:end,1:nn:end,1);
v = v.*log(ev)/log(max(ev(:)))*.05;
%plotarr(xy2(:), v(:),'k-',0)
plot(xy2,'k.')
p = xy2(:)+ [-v(:), v(:)]/2;
plot(p.','k-')

shading interp
colorbar
colormap(red_blue_colormap)
title('Oceantracker')
axis([0,2,0,1])
hold off

%%
figure(3)
FT = interp2(x,y,d.FTLE,r.X0,r.Y0);
plot(r.FTLE,FT,'.')
hold on
ax=axis;
plot([0,ax(2)],[0,ax(2)],'k--')
xlabel('FTLE romian')
ylabel('FTLE Oceantracker')
grid on 



