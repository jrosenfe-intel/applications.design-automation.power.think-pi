from thinkpi.operations import speed as spd
from thinkpi.operations import pman as pm


if __name__ == '__main__':
    d = spd.Database(r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21.spd')
    d.load_flags = {'layers': False, 'nets': False,
                    'nodes': True, 'ports': True,
                    'shapes': False, 'padstacks': False,
                    'vias': False, 'components': False,
                    'traces': False, 'plots': False}
    d.load_data()

    pg = pm.PortGroup(d)
    pg.import_port_info(r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_ports.csv',
                        r'..\Albert\SPR_noTFC_VCCIN_clean_reduced_V21_new_ports.spd')

    