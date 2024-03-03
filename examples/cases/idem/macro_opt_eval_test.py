from thinkpi.flows import tasks

if __name__ == '__main__':
    results = tasks.IdemEvalResults(r"E:\Users\jrosenfe\ThinkPI\data\idem\sparams\OKS1_NFF1S_DNOX_PWRsims_ww03_processed_all_ports_clip_012623_173538_30544_DCfitted.s29p",
                                    200e6)
    results.refresh()
    
    
    