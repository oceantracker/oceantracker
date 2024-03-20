function d = readJSONfile(JSONfileName)

fid = fopen(JSONfileName); 
raw = fread(fid,inf); 
str = char(raw'); 
fclose(fid); 
d = jsondecode(str);