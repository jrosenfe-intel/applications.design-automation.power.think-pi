from thinkpi.flows import tasks

if __name__ == '__main__':
    brd = tasks.PdcTask(
        r'..\thinkpi_test_db\SKX\vrm_test.spd'
    )
    brd.import_vrm_setup(r'..\thinkpi_test_db\SKX\vrm_test_vrmsetup.xlsx')
    brd.db.save()
