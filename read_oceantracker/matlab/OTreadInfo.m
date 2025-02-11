function info= OTreadInfo(caseInfoFileName)

output_dir= [fileparts(caseInfoFileName) '\'];

info = readJSONfile(caseInfoFileName);