import datetime
import pandas as pd
import re
import time

from os.path import exists
from random import randint

from nofakes import blob_extraction, robust_positions
from nofakes import sign_key_gen, digital_signature, verification
from nofakes import generation, reproduction, secure_sketch, reconstruction
from nofakes import mk_dir

TODAY = str(datetime.date.today()).replace('-', '')

ssk_folder_path = 'secure_sketch/' + TODAY + '/'
mk_dir(ssk_folder_path)


def enrollment(attempt: str, case: str, txt_enr: str, ssk_file_enr: str) -> (pd.DataFrame, pd.DataFrame):
    """
    :param attempt: path to read the set of images
    :param case:
    :param txt_enr: file to write the info related to the enrolled data
    :param ssk_file_enr:
    :return: omega_robust, sketch
    """

    str1 = [m.start() for m in re.finditer(r"/", attempt)][-2]
    str2 = [m.start() for m in re.finditer(r"/", attempt)][-1]

    omegas, image_size, blob_diameter, N = blob_extraction(attempt, txt_enr)
    t0 = time.time()
    omega_robust = robust_positions(omegas, txt_enr)
    time_robust = round(time.time() - t0, 4)

    data = []

    t1 = time.time()
    sketch = secure_sketch(omega_robust, blob_diameter, N)
    time_ssk = round(time.time() - t1, 4)
    sketch.to_pickle(ssk_folder_path + case + ' ' + attempt[str1 + 1:str2] + '.pkl')

    t2 = time.time()
    P, R = generation(omega_robust, sketch)
    _, hash, r = P
    time_gen = round(time.time() - t2, 4)

    pubkey, _ = sign_key_gen(R)

    n_AS = "{0:x}".format(randint(0, 2 ** 256))
    data.append([attempt[str1 + 1:str2], R, hash, r, pubkey, n_AS, time_robust, time_ssk, time_gen])

    if not exists(ssk_file_enr):
        dataframe = pd.DataFrame(data, columns=['csr', 'R', 'h', 'r', 'pubkey', 'n_AS',
                                                'time_robust', 'time_ssk', 'time_gen'])
        dataframe.to_pickle(ssk_file_enr)
    else:
        df = pd.read_pickle(ssk_file_enr)
        df.loc[len(df)] = data[0]
        df.to_pickle(ssk_file_enr)

    return None


def authentication(attempt: str, case: str, txt_auth: str, ssk_file_enr: str, ssk_file_auth: str):
    """
    :param attempt:
    :param case:
    :param txt_auth:
    :param ssk_file_enr:
    :param ssk_file_auth:
    :return:
    """
    global time_rec, time_rep, answer
    str1 = [m.start() for m in re.finditer(r"/", attempt)][-2]
    str2 = [m.start() for m in re.finditer(r"/", attempt)][-1]
    csr = attempt[str1 + 1:str2]

    omegas, image_size, blob_diameter, N = blob_extraction(attempt, txt_auth)
    t0 = time.time()
    omega_robust = robust_positions(omegas, txt_auth)
    time_robust = round(time.time() - t0, 4)

    ssk_info = pd.read_pickle(ssk_file_enr)
    ssk_info.set_index('csr', inplace=True)
    df_ssk_info = ssk_info.loc[csr]
    h, r, psk, n_AS = df_ssk_info['h'], df_ssk_info['r'].encode(), df_ssk_info['pubkey'], df_ssk_info['n_AS']

    data = []

    sketch = pd.read_pickle(ssk_folder_path + case + ' ' + csr + '.pkl')
    if len(sketch) == len(omega_robust):

        time_rec_0 = time.time()
        omega_rec = reconstruction(omega_robust, sketch, blob_diameter)
        time_rec = round(time.time() - time_rec_0, 4)

        time_rep_0 = time.time()
        R = reproduction(omega_rec, sketch, h, r)
        # omega_rec, R = reproduction(omega_robust, sketch, blob_diameter, h, r)
        time_rep = round(time.time() - time_rep_0, 4)
        print("R Authentication:\t", R)

        n_AD = "{0:x}".format(randint(0, 2 ** 256))
        if R == "{0:d}".format(int(0.0)):
            answer = 0
        else:
            _, privkey = sign_key_gen(R)
            signature = digital_signature(privkey, int((n_AS + n_AD), 16))
            answer = 1 if verification(psk, signature, n_AS, n_AD) else 0
    else:
        time_rec, time_rep, answer = 0, 0, 0
        print("Non-Authenticated")

    actual_value = 1 if 'intra' in txt_auth else 0

    data.append([attempt[str2 + 1:], csr, answer, actual_value, time_robust, time_rec, time_rep])

    if not exists(ssk_file_auth):
        dataframe = pd.DataFrame(data, columns=['attempt', 'csr', 'answer', 'actual_value',
                                                'time_robust', 'time_rec', 'time_rep'])
        dataframe.to_pickle(ssk_file_auth)
    else:
        df = pd.read_pickle(ssk_file_auth)
        df.loc[len(df)] = data[0]
        df.to_pickle(ssk_file_auth)

    return None


def authentication_interdistance(attempt, case, csr, txt_auth, ssk_file_enr, ssk_file_auth):
    """
    :param attempt:
    :param case:
    :param csr:
    :param txt_auth:
    :param ssk_file_enr:
    :param ssk_file_auth:
    :return:
    """
    secure_sketch_path = ssk_folder_path + case + ' ' + csr + '.pkl'
    str1 = [m.start() for m in re.finditer(r"/", attempt)][-2]
    str2 = [m.start() for m in re.finditer(r"/", attempt)][-1]

    omegas, image_size, blob_diameter, N = blob_extraction(attempt, txt_auth)
    t0 = time.time()
    omega_robust = robust_positions(omegas, txt_auth)
    time_robust = round(time.time() - t0, 4)

    ssk_info = pd.read_pickle(ssk_file_enr)
    ssk_info.set_index('csr', inplace=True)
    df_ssk_info = ssk_info.loc[csr]
    h, r, psk, n_AS = df_ssk_info['h'], df_ssk_info['r'].encode(), df_ssk_info['pubkey'], df_ssk_info['n_AS']

    data = []

    sketch = pd.read_pickle(secure_sketch_path)
    if len(sketch) == len(omega_robust):

        time_rec_0 = time.time()
        omega_rec = reconstruction(omega_robust, sketch, blob_diameter)
        time_rec = round(time.time() - time_rec_0, 4)

        time_rep_0 = time.time()
        R = reproduction(omega_rec, sketch, h, r)
        time_rep = round(time.time() - time_rep_0, 4)
        print("R Authentication:\t", R)

        n_AD = "{0:x}".format(randint(0, 2 ** 256))
        if R == "{0:d}".format(int(0.0)):
            signature, answer = 'NA', 0
        else:
            _, privkey = sign_key_gen(R)
            signature = digital_signature(privkey, int((n_AS + n_AD), 16))
            answer = 1 if verification(psk, signature, n_AS, n_AD) else 0
    else:
        print("Non-Authenticated")
        time_rec, time_rep, signature, answer = 0, 0, 'NA', 0

    actual_value = 1 if 'intra' in txt_auth else 0

    data.append(
        [attempt[str1 + 1:str2], attempt[str2 + 1:], csr, answer, actual_value, time_robust, time_rec, time_rep])

    if not exists(ssk_file_auth):
        dataframe = pd.DataFrame(data, columns=['csr', 'attempt', 'csr_enr', 'answer', 'actual_value',
                                                'time_robust', 'time_rec', 'time_rep'])
        dataframe.to_pickle(ssk_file_auth)
    else:
        df = pd.read_pickle(ssk_file_auth)
        df.loc[len(df)] = data[0]
        df.to_pickle(ssk_file_auth)

    return None
