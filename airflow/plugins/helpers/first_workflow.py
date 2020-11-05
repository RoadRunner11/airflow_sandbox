import airflow.hooks.S3_hook
from airflow.models import Variable

from datetime import datetime
import base64
import six
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import json
import os
import io
import boto3
import gzip
import pandas as pd
import codecs
from flatten_json import flatten
from smart_open import open
import pyarrow as pa
import awswrangler as wr

def simulate(*args, **kwargs):
    ts = kwargs["params"]["timedate"]
    prov_ts = kwargs["execution_date"].strftime('%Y-%m-%d')
    datet = datetime.strptime(prov_ts, '%Y-%m-%d')
    moment = datetime.now()
    # moment = moment.strftime("%Y-%m-%d %H:%M:%S")
    return moment, moment.year, '%02d' % moment.month, '%02d' % moment.day, moment.hour
    #bucket_key_template = 's3://[bucket_name]/datatfile_{}.csv'.format(file_suffix)

def get_file_from_s3(*args, **kwargs):
    hook = airflow.hooks.S3_hook.S3Hook('s3_task')
    bucket = Variable.get("s3_bucket")
    data = io.BytesIO()
    key = hook.get_key(key="ypsource.json", bucket_name=bucket )
    key.download_fileobj(data)
    return data.getvalue()
    #kwargs["ti"].xcom_push(key="s3_key", value= key)

def flatten_data(data_json):
    ##keys = kwargs["ti"].xcom_pull(key= "s3_keys", task_ids="get_from_S3")
    #with gzip.open(data_json, "rb") as f: #open file was used because it's a closed file
    reader = codecs.getreader("utf-8")
    #data_byte= data_json.decode("utf-8")
    y = json.loads(data_json.read())
    f_json= (flatten(record, '.') for record in y)
    dframe = pd.DataFrame(f_json)
        
    return dframe


def upload_file_to_S3_with_hook(*args, **kwargs):
    moment = datetime.now()
    b_name = Variable.get("s3_bucket")
    source = Variable.get("pinpoint")
    year = moment.year
    month = '%02d' % moment.month
    day = '%02d' % moment.day
    hr = moment.hour
    filename = kwargs['params']['filename']
    key = kwargs['params']['key']
    bucket_name = kwargs['params']['bucket_name']
    aws_access_key_id = Variable.get("aws_access_key_id")
    aws_secret_key = Variable.get("aws_secret_key")
    session = boto3.Session(
        aws_access_key_id="",
        aws_secret_access_key=""
     )
    hook = airflow.hooks.S3_hook.S3Hook('s3_task')
    bucket = Variable.get("s3_bucket")
    raw_bucket = Variable.get("raw_bucket")

    data_buffer = io.BytesIO()
    key = hook.get_key(key=f'{source}/{year}/{month}/{day}/ypsource.json', bucket_name=bucket )
    key.download_fileobj(data_buffer)
    data_buffer.seek(0)
    
    f_data = flatten_data(data_buffer)
    #f_data = pa.table(f_data).to_pandas()
    output_data = io.BytesIO()
    #kwargs["ti"].xcom_push(key="data", value= f_data)
    #with open(output_data, "wb") as parq_file:
    #f_data.to_parquet(output_data)# engine="auto", compression="snappy")
    #output_data.seek(0)
    #hook.load_file_obj(output_data, key="ypsource.parquet", bucket_name=bucket)
    #with open(f's3://{bucket_name}/ypsource.parquet', 'wb', transport_params={'session': session}) as out_file:
        #f_data[["event_type", "application.app_id"]].to_parquet("out_file.parquet", compression=None)
    wr.s3.to_parquet(
        df=f_data[["event_type", "application.app_id"]],
        path = f"s3://{raw_bucket}/{source}/{year}/{month}/{day}/ypsource.parquet",
       boto3_session =session,
           )