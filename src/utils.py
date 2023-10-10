import os
import glob
import pandas as pd
from datetime import datetime

def read_files_from_folder(data_name: str, from_date: str = '', to_date: str = '') -> pd.DataFrame:
    folder = os.path.join('.', 'data' , data_name)
    path = os.getcwd()
    csv_files = glob.glob(os.path.join(folder, "*.csv"))

    if len(csv_files) == 0:
        raise Exception(f'ERROR: no file found in {folder}')

    df = pd.DataFrame()

    for file_name in csv_files:
        df = pd.concat([df, pd.read_csv(file_name, parse_dates=['Datetime'])], axis=0)

    if from_date != '' and to_date != '':
        start_date = datetime.strptime(from_date, '%Y-%m-%d')
        end_date = datetime.strptime(to_date, '%Y-%m-%d')
        df = df.reset_index()
        df['Datetime'] = df.apply(lambda row: row['Datetime'].replace(tzinfo=None), axis=1)
        df = df[(df['Datetime'] > start_date) & (df['Datetime'] < end_date)]

    df = df.set_index('Datetime').sort_index()
    return df