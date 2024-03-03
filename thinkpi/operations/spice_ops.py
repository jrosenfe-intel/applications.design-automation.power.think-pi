import pathlib

class Spice:

    def __init__(self, root_spice_file, root_spice_deck):

        self.root_spice_file = pathlib.Path(root_spice_file)
        self.root_spice_deck = pathlib.Path(root_spice_deck)
        self.spice_files = {}

    def replace_params(self, lines):

        # Find all parameters
        params = {}
        for idx, line in enumerate(lines.copy()):
            if not line or line[0] == '*':
                continue
            if '=' in line:
                if '.subckt' not in line.lower() and line[0].lower() != 'x':
                    split_equal = line.strip('+').strip().split('=')
                    params[split_equal[0].split()[-1].lower()] = split_equal[1].split()[0]
                    lines[idx] = f'* {line}'
                #else:
                #    lines[idx] = line.replace(f"{split_equal[0].split(' ')[-1]}",
                #                                f"* {split_equal[0].split(' ')[-1]}")
            else:
                for param_name in params.keys():
                    if param_name in line.lower():
                        line = line.lower().replace(param_name, params[param_name])
                lines[idx] = line

        return lines

    def replace_subckt_params(self, lines):

        inst_params = {}
        inst_no_params = set()
        subckt_idx = 0
        # Find parameterized and non-parameterized circuit instantiations
        for idx, line in enumerate(lines.copy()):
            if not line:
                continue
            if line[0].lower() == 'x':
                if '=' in line:
                    split_equal = line.strip().split('=')
                    subckt_name = split_equal[0].split()[-2]

                    params = []
                    for param in line.split(subckt_name)[1].split('='):
                        params += param.split()
                    inst_params[(subckt_name, subckt_idx)] = []
                    for param_name, param_val in zip(params[::2], params[1::2]):
                        inst_params[(subckt_name, subckt_idx)].append((param_name, param_val))
                    lines[idx] = f'{line.split(subckt_name)[0].strip()} {subckt_name}_{subckt_idx}'
                    subckt_idx += 1
                else:
                    inst_no_params.add(line.split()[-1])

        subckt_templates = {}
        subckt_defaults = {}
        find_ends = False
        new_lines = []
        # Find subckt as templates
        for line in lines:
            if find_ends:
                if '.ends' in line.lower():
                    find_ends = False
                    subckt_templates[subckt_name] += '.ENDS\n'
                    subckt_defaults[subckt_name] = subckt_templates[subckt_name]
                    for param_name, param_val in zip(default_params[::2],
                                                        default_params[1::2]):
                        subckt_defaults[subckt_name] = (
                            subckt_defaults[subckt_name].replace(param_name.lower(), param_val)
                        )
                else:
                    subckt_templates[subckt_name] += f'{line}\n'
                continue
            if '.subckt' in line.lower() and '=' in line:
                subckt_name = line.split()[1]
                # Save default parameters for instances without params
                default_params = []
                split_equal = line.split('=')
                default_params = [split_equal[0].split()[-1]]
                for param in split_equal[1:]:
                    default_params += param.split()

                split_equal = line.strip().split('=')
                subckt_templates[subckt_name] = f"{' '.join(split_equal[0].split()[:-1])}\n"
                find_ends = True
                continue
            if line.lower() == '.end':
                continue
            new_lines.append(line)

        # Insert new subckts with explicit parameter values
        for ckt_name in inst_no_params:
            try:
                new_lines += subckt_defaults[ckt_name].split('\n')
            except KeyError:
                pass
        for (ckt_name, ckt_idx), ckt_params in inst_params.items():
            try:
                subckt_def = subckt_templates[ckt_name]
            except KeyError:
                continue
            subckt_def = subckt_def.lower().replace(ckt_name.lower(), f'{ckt_name}_{ckt_idx}')
            for (param_name, param_val) in ckt_params:
                subckt_def = subckt_def.lower().replace(param_name.lower(), param_val)
            new_lines += subckt_def.split('\n')
            
        return new_lines

    def comment_out(self, lines):

        includes = []
        params = []
        comment_plus = False
        for idx, line in enumerate(lines.copy()):
            if not line or line[0] == '*':
                continue
            orig_line = line
            line = line.lower()
            if (line[0] == '+' and comment_plus) or 'vr' in line:
                lines[idx] = f'* {orig_line}'
                continue
            if '.inc' in line:
                split_line = line.split()
                line = ' '.join(split_line[1:]).strip('"').strip("'")
                try:
                    includes.append((idx, self.spice_files[pathlib.Path(line).name]))
                except KeyError:
                    print(f'Cannot find include file {line}')
                lines[idx] = f'* {orig_line}'
                continue
            else:
                comment_plus = False
            if line[0] == '.':
                if '.end' in line:
                    continue
                if '.subckt' not in line:
                    lines[idx] = f'* {orig_line}'
                '''
                if '.param' in line:
                    params.append((line.split('=')[0].split()[1],
                                    line.split('=')[1].strip('"').strip("'"))
                                )
                '''
            if line[0] == 'i' or line[0] == 'v' or line[0] == 'g':
                if line[0] == 'v' and line.split()[-1] == '0':
                    orig_line = 'R' + orig_line[1:]
                    lines[idx] = orig_line
                else:
                    lines[idx] = f'* {orig_line}'
                    comment_plus = True

        return includes

    def replace_include(self, lines, include_files):

        inc_idx = 0
        for idx, fname in include_files:
            new_lines = fname.read_text().split('\n')
            lines[idx+inc_idx+1:idx+inc_idx+1] = new_lines #self.replace_params(new_lines)
            inc_idx += len(new_lines)

    def convert(self, fname):

        self.spice_files = {path.name.lower(): path for path in sorted(self.root_spice_deck.rglob('*'))}
        lines = self.root_spice_file.read_text().split('\n')
        
        include_files = self.comment_out(lines)
        while include_files:
            self.replace_include(lines, include_files)
            include_files = self.comment_out(lines)

        lines = self.replace_params(lines)
        lines = self.replace_subckt_params(lines)

        # Replace gnd or ref nodes to to 0
        lines_str = '\n'.join(lines)
        lines_str = lines_str.replace('gnd', '0').replace('GND', '0').replace('ref', '0').replace('REF', '0')

        pathlib.Path(fname).write_text(lines_str)


    





    