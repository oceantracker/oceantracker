function d = readNCinfoOT(filename)
% indev vars are those to convert from zero based to one based 

info=ncinfo(filename);

d=struct('Variables',struct,'Attributes',struct,'Dimensions',struct);

for n=1:length(info.Variables)
  d.Variables.(info.Variables(n).Name) =info.Variables(n);
end

for n=1:length(info.Attributes)
  d.Attributes.(info.Attributes(n).Name) =info.Attributes(n).Value;
end


for n=1:length(info.Dimensions)
  d.Dimensions.(info.Dimensions(n).Name) =info.Dimensions(n).Length;
end

