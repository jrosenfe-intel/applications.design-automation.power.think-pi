function save_csv(filename, names, values)
    % Open the file for writing
    fileID = fopen(filename, 'w');

    % Write the header line
    fprintf(fileID, 'parameter,value\n');

    % Write the data to the file
    for i = 1:length(names)
        if ischar(values{i})
            fprintf(fileID, '%s,%s\n', names{i}, values{i});
        else
            fprintf(fileID, '%s,%f\n', names{i}, values{i});
        end
    end

    % Close the file
    fclose(fileID);
end