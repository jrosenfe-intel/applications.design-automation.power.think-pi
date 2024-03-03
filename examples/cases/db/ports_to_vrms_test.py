from thinkpi.flows import tasks


if __name__ == '__main__':

    brd = tasks.PdcTask(r'..\thinkpi_test_db\OKS\db\OKS12CH_PI_PF_V1_B_proc_ports.spd')
    brd.ports_to_vrms()
    brd.db.save('OKS12CH_PI_PF_V1_B_proc_ports_to_vrms.spd')



    


    