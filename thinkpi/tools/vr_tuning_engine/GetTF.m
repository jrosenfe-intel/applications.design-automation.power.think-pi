%%% get touchtone info funtion .
function [Freq, Zl, Av] = GetTF(File)

Data = read(rfdata.data, File);
Freq = Data.Freq;
%Z = extract(Data,'Z_PARAMETERS', 0.1);
Z = extract(Data,'Z', 0.1);

Z11 = Z(1,1,:);
Z21 = Z(2,1,:);

Zl = Z11(:);
Av = Z21(:)./Z11(:);

end

