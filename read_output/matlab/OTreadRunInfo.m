function r = OTreadRunInfo(file_name)

fid = fopen(file_name); 
raw = fread(fid,inf); 
str = char(raw'); 
fclose(fid); 
r = jsondecode(str);