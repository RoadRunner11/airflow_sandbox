from airflow import DAG, macros
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
from airflow.operators.dummy_operator import DummyOperator
#slack
from airflow.hooks.base_hook import BaseHook
import airflow.hooks.S3_hook
from airflow.contrib.operators.slack_webhook_operator import SlackWebhookOperator
from airflow.operators.sensors import BaseSensorOperator
from airflow.operators.sensors import S3KeySensor
from datetime import datetime, timedelta
from airflow.models import Variable
#from __future__ import unicode_literals

from airflow.utils.dates import days_ago
from helpers import simulate, get_file_from_s3, flatten_data, upload_file_to_S3_with_hook

schedule = timedelta(minutes=5)
today = datetime.combine(datetime.today() ,
                                  datetime.min.time())
default_args = {
    'owner': 'Ypsource',
    'depends_on_past': False,
    'start_date': today,#days_ago(1), #datetime(2020, 11, 1),
    'email': ['ypsource@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=2),
    'provide_context': True,
}



with DAG('S3_task', default_args=default_args, schedule_interval="02 * * * *") as dag:
    
    start_task = DummyOperator(
            task_id='dummy_start'
    )


    dt = "2020-11-05"
    # dt = datetime.strptime(dt, '%Y-%m-%d')

    # simulate_task = PythonOperator(
    #     task_id='simulate_task_',
    #     python_callable=simulate,
    #     params={
    #             "timedate": dt,
    #         },
    #     provide_context=True,
    #     dag=dag
    #     )
    
    moment = datetime.now()
    b_name = Variable.get("s3_bucket")
    source = Variable.get("pinpoint")
    year = moment.year
    month = '%02d' % moment.month
    day = '%02d' % moment.day
    hr = moment.hour
    bucket_key_template = f'{source}/{year}/{month}/{day}/ypsource.json'
                        
    
    get_new_json = S3KeySensor(
        task_id= "get_new_json",
        poke_interval = 60 *2, 
        timeout = 60 * 60 *3,
        bucket_key = bucket_key_template,
        bucket_name = b_name,
        wildcard_match = False,
        aws_conn_id = "s3_task",
        dag= dag 
        )

    # get_from_S3 = PythonOperator(
    #     task_id='get_from_S3',
    #     python_callable=get_file_from_s3,
    #     dag=dag
    #     )

    upload_to_S3_task = PythonOperator(
            task_id='upload_file_to_S3',
            python_callable=upload_file_to_S3_with_hook,
            params={
                'filename': '/home/akorede/Documents/mycsv.csv',
                'key': 'mycsv.csv',
                'bucket_name': 'ypsource-bucket',
            },
            provide_context=True,
            dag=dag)

    # Use arrows to set dependencies between tasks
    upload_to_S3_task.set_upstream(get_new_json)