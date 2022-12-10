import datetime
import glob
import multiprocessing as mp
import time

from os import remove
from os.path import exists

from nofakes import head_txt_csr_file, numerical_sort, mk_dir
from protocol_phases import enrollment, authentication

N_CORES = 1

TODAY = str(datetime.date.today()).replace('-', '')

data_folder_path = 'results/' + TODAY + '/'
mk_dir(data_folder_path)

csr_responses_path = 'dataset/csr_responses/'
cases = ['case1', 'case2']
distance = ' intra'
stages = ['Enrollment', 'Authentication']


def result_align_score(result):
    global align
    align.append(result)


if __name__ == '__main__':
    for case in cases[:]:
        txt_enr = data_folder_path + case + distance + ' enrol_information.txt'
        ssk_enr = data_folder_path + case + distance + ' enrol_ssk.pickle'
        txt_auth = data_folder_path + case + distance + ' auth_information.txt'
        ssk_auth = data_folder_path + case + distance + ' auth_ssk.pickle'
        iteration = 0
        for stage in stages[:]:
            if 'Enrollment' in stage:
                head_txt_csr_file(txt_enr)
                csr_responses = sorted(glob.glob(csr_responses_path + stage + '/*'), key=numerical_sort)
                ts0 = time.time()
                for csr_response in csr_responses[:]:
                    attempts = sorted(glob.glob(csr_response + '/*'), key=numerical_sort)
                    align = []
                    pool = mp.Pool(N_CORES)
                    for attempt in attempts:
                        print('Attempt:', attempt)
                        pool.apply_async(enrollment, args=(attempt, case, txt_enr, ssk_enr),
                                         callback=result_align_score)
                    pool.close()
                    pool.join()
                print(f'{(time.time() - ts0) / 60}', 'minutes')
            else:
                head_txt_csr_file(txt_auth)
                csr_responses = sorted(glob.glob(csr_responses_path + stage + '/*'), key=numerical_sort)
                ts0 = time.time()
                for csr_response in csr_responses[:]:
                    attempts = sorted(glob.glob(csr_response + '/*'), key=numerical_sort)
                    align = []
                    pool = mp.Pool(N_CORES)
                    # with suppress(Exception):
                    for attempt in attempts:
                        print('Attempt:', attempt)
                        pool.apply_async(authentication, args=(attempt, case, txt_auth, ssk_enr, ssk_auth),
                                         callback=result_align_score)
                    pool.close()
                    pool.join()
                print(f'{(time.time() - ts0) / 60}', 'minutes')
