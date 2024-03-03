from thinkpi.operations import pman as pm

if __name__ == '__main__':
    db_sinks = pm.PortGroup(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_vrms.spd')
    db_ports = db_sinks.vrms_to_ports(suffix='_temp')
    db_ports.add_ports(save=False)

    # Convert sense points to ports
    db_ports = db_ports.vrms_sense_to_ports(suffix='_sense')
    db_ports.add_ports(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_vrms_to_ports.spd')



    


    