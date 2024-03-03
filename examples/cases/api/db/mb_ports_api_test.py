from thinkpi.backend_api import api


if __name__ == '__main__':
    db_api = api.DbApi(r'..\thinkpi_test_db\Donahue\brd_DPS_pk187_080421.spd')
    db_api.load_data()
    response = db_api.setup_motherboard_ports(r'..\thinkpi_test_db\Donahue\brd_DPS_pk187_080421_ports.spd',
                                              ['P1V1_L', 'P3V3_E'],
                                              'Signal$TOP', 3,
                                              'Signal$BOTTOM', 2,
                                              'Signal$TOP',
                                              'Create', 10)
    
    

    

    