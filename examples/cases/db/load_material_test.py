from thinkpi.operations import speed as spd


if __name__ == '__main__':
    db = spd.Database()
    m = db.load_material(r"..\thinkpi_test_db\ACI_Materials_WW5'22.txt")

    db.save_material(r"..\thinkpi_test_db\ACI_Materials_WW5'22_new.txt", m)

    

    