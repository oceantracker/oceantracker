%
out_dir = '..\..\demos\output\demo70_LCS_test\'

d = NCDFread([out_dir 'demo70_LCS_test_LCS.nc']);
ngrid=1;
n_lag=1;
r=  size(d.x_release_grid,1);
c=  size(d.x_release_grid,2);
nt = size(d.LCS,1);
%data= squeeze(d.LCS(:,ngrid,n_lag,:,:));
data=   squeeze(d.x_at_lag(:,ngrid,n_lag,:,:,1)) - reshape(d.x_release_grid(:,:,1),1,r,c);
ll=[];
for n = 1:2:nt
    z = squeeze(data(n,:,:));
    pcolor(z)
    nn= sum(sum(~isnan(z)));
    if nn ==0
       %disp(n)
       ll = [ll,n-1];
    end
    
    title([num2str(n) ' non nans=' num2str(nn)])
    colorbar
    shading interp
    caxis([-8000 8000])
    pause(.5)
end
ll

    