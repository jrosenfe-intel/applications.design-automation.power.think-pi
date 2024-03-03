from thinkpi.flows import tasks

if __name__ == '__main__':
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\SKX\vrm_test.spd'
    )
    brd.export_vrm_setup()
