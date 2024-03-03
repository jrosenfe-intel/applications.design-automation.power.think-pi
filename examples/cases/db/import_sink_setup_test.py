from thinkpi.flows import tasks

if __name__ == '__main__':
    pkg = tasks.PdcTask(
        r'..\thinkpi_test_db\donahue\sink_test.spd'
    )
    pkg.import_sink_setup(r'..\thinkpi_test_db\donahue\sink_test_sinksetup.xlsx')
    pkg.db.save()