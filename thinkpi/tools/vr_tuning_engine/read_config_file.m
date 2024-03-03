function data = read_config_file(filename)
    % Open the file
    fid = fopen(filename, 'r');
    
    % Read the file line by line
    line = fgetl(fid);
    while ischar(line)
        % Split the line into tokens
        tokens = strsplit(line, ',');
        
        % Store the data in the structure
        data.(tokens{1}) = tokens{2};
        
        % Read the next line
        line = fgetl(fid);
    end
    
    % Close the file
    fclose(fid);
end