function d = readJSONfile(JSONfileName)

fid = fopen(JSONfileName,'r'); 
raw = fread(fid,inf); 
str = char(raw'); 
fclose(fid); 
d = jsondecode(str);