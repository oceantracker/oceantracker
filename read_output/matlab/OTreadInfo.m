function info= OTreadInfo(runInfoFileName,case_number)

if nargin < 2, case_number=1;end
output_dir= [fileparts(runInfoFileName) '\'];

info= struct('case_number',case_number);
info.runInfo = readJSONfile(runInfoFileName);

info.caseInfo = readJSONfile([ output_dir  info.runInfo.output_files.case_info{case_number}]);
info.grid = OTreadGrid([ output_dir info.runInfo.output_files.grid]);
info.grid_outline = readJSONfile([ output_dir info.runInfo.output_files.grid_outline]);

info.particle_release_groups=info.caseInfo.full_params.particle_release_groups;