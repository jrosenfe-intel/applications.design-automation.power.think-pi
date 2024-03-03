from thinkpi.operations import pman as pm

if __name__ == '__main__':
    db_sinks = pm.PortGroup(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_sinks.spd')
    db_ports = db_sinks.sinks_to_ports(suffix='sinky')
    db_ports.add_ports(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_sinks_to_ports.spd')



    


    