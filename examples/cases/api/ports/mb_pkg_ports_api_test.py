import queue

from thinkpi.backend_api import api

que = queue.Queue()

if __name__ == '__main__':
        ports = api.PortHandler(que)
        r'''
        brd_reponse = ports.setup_motherboard_ports(
                                db=r'..\thinkpi_test_db\DNH\brd_DPS_pk187_080421.spd',
                                pwr_net_names=['P1V1_L', 'P3V3_E'], cap_finder='C*',
                                cap_layer_top='Signal$TOP', reduce_num_top=3,
                                cap_layer_bot='Signal$BOTTOM', reduce_num_bot=2,
                                vrm_layer='Signal$TOP', ref_z=10, socket_mode='create',
                                skt_num_ports=5
                        )
        '''

        r'''
        # Boxes
        pkg_response = ports.setup_pkg_ports(
                                db=r'..\thinkpi_test_db\DMR\dmr_ap_pwr_vccddr_hv_east_22ww50p4_proc_ports_cports_red_23ww20_new_portsspd_box2.spd',
                                sinks_mode='boxes',
                                pwr_net_names=['vccddr_hv_q_1'], cap_finder='C*',
                                cap_layer_top='Signal$surface', reduce_num_top=30,
                                cap_layer_bot='Signal$base', reduce_num_bot=5,
                                socket_mode='create', ref_z=1, skt_num_ports=10
                        )
        '''
    
        # Auto
        pkg_response = ports.setup_pkg_ports(
                                db=r'..\thinkpi_test_db\DMR\dmr_ap_pwr_vccddr_hv_east_22ww50p4_proc_ports_cports_red_23ww20_new_portsspd.spd',
                                sinks_mode='auto', sinks_layer='Signal$surface',
                                sinks_num_ports=10, sinks_area=(12.3e-3, 2.64e-3, 15.6e-3, 14.5e-3),
                                pwr_net_names=['vccddr_hv_q_1'], cap_finder='C*',
                                cap_layer_top='Signal$surface', reduce_num_top=30,
                                cap_layer_bot='Signal$base', reduce_num_bot=5,
                                socket_mode='create', ref_z=1, skt_num_ports=10
                        )
    
    
    
    

    

    