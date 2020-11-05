import boto3
import json
import os

import pandas as pd
from flatten_json import flatten
import warnings 
warnings.filterwarnings('ignore')

from __future__ import unicode_literals
import base64
import six
from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

#connect with s3
session= boto3.Session(aws_access_key_id= 'AKIAT7F4NWZDU3DL6FIS', aws_secret_access_key= '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', region_name= 'us-east-1')

s3=session.resource('s3')

#connect with bucket that hold file
bucket= s3.Bucket('ypsource-bucket')
print(bucket)

#connect to desired file(i.e your file)
obj= bucket.Object(key= 's3/buckets/ypsource-bucket/ypsource.json')
print(obj)

#downloading a file from s3 using boto3
def download_file_from_bucket(bucket_name, s3_key, dst_path):
    bucket = s3.Bucket(bucket_name)
    bucket.download_file(Key=s3_key, Filename=dst_path)

download_file_from_bucket('ypsource-bucket', 'ypsource.json', 'C:/Users/USER/Documents/data science/David_386')


#open the just downloaded file to read from it
with open('C:/Users/USER/Documents/data science/David_386/ypsource.json') as f: #open file was used because it's a closed file
    y= json.load(f)
    json= (flatten(record, '.') for record in y)
    dframe = pd.DataFrame(json)

#Anonymization of column containing sensitive data
# coding: utf-8
class PublicKeyFileExists(Exception): pass

class RSAEncryption(object):
    PRIVATE_KEY_FILE_PATH = None
    PUBLIC_KEY_FILE_PATH = None
    
    def encrypt(self, message):
        public_key = self._get_public_key()
        public_key_object = RSA.importKey(public_key)
        public_key_object = PKCS1_OAEP.new(public_key_object)
        random_phrase = 'M'
        encrypted_message = public_key_object.encrypt(self._to_format_for_encrypt(message))
        # use base64 for save encrypted_message in database without problems with encoding
        return base64.b64encode(encrypted_message)
        
    def decrypt(self, encoded_encrypted_message):
        encrypted_message = base64.b64decode(encoded_encrypted_message)
        private_key = self._get_private_key()
        private_key_object = RSA.importKey(private_key)
        private_key_object = PKCS1_OAEP.new(private_key_object)
        decrypted_message = private_key_object.decrypt(encrypted_message)
        return six.text_type(decrypted_message, encoding='utf8')
    
    def generate_keys(self):
        """Be careful rewrite your keys"""
        random_generator = Random.new().read
        key = RSA.generate(1024, random_generator)
        private, public = key.exportKey(), key.publickey().exportKey()

        if os.path.isfile(self.PUBLIC_KEY_FILE_PATH):
            pass
            # raise PublicKeyFileExists('Файл с публичным ключом существует. Удалите ключ')
        else:
            self.create_directories()

            with open(self.PRIVATE_KEY_FILE_PATH, 'wb') as private_file:
                private_file.write(private)
            with open(self.PUBLIC_KEY_FILE_PATH, 'wb') as public_file:
                public_file.write(public)
            return private, public
        
    def create_directories(self, for_private_key=True):
        public_key_path = self.PUBLIC_KEY_FILE_PATH.rsplit('/', 1)
        if not os.path.exists(public_key_path[0]):
            os.makedirs(public_key_path[0])
        if for_private_key:
            private_key_path = self.PRIVATE_KEY_FILE_PATH.rsplit('/', 1)
            if not os.path.exists(private_key_path[0]):
                os.makedirs(private_key_path[0])
                
    def _get_public_key(self):
        """run generate_keys() before get keys """
        with open(self.PUBLIC_KEY_FILE_PATH, 'r') as _file:
            return _file.read()
        
    def _get_private_key(self):
        """run generate_keys() before get keys """
        with open(self.PRIVATE_KEY_FILE_PATH, 'r') as _file:
            return _file.read()
        
    def _to_format_for_encrypt(self, value):
        if isinstance(value, int):
            return six.binary_type(value)
        for str_type in six.string_types:
            if isinstance(value, str_type):
                return value.encode('utf8')
        if isinstance(value, six.binary_type):
            return value
        
KEYS_DIRECTORY = "keys/"

class TestingEncryption(RSAEncryption):
    PRIVATE_KEY_FILE_PATH = KEYS_DIRECTORY + 'private.key'
    PUBLIC_KEY_FILE_PATH = KEYS_DIRECTORY + 'public.key'
    
TestingEncryption().generate_keys() 
dframe['application.sdk.name'].apply(lambda x: TestingEncryption().encrypt(x))
dframe.rename(columns= {'application.sdk.name': 'application.sdk.name_anony'}, inplace= True)

#converting to parquet format as requested
dframe.to_parquet ('flattenedypsource.parquet', compression= None) #converting from pandas dataframe to parquet


#creating a bucket
def make_bucket(name, acl): #acl represent Access control list policy
    return s3.create_bucket(Bucket= name, ACL= acl)

s3_bucket= make_bucket('rawbucket-yp', 'public-read')

#uploading a file to s3 using boto3
def upload_file_to_bucket(bucket_name, file_path):
    file_dir, file_name = os.path.split(file_path)

    bucket = s3.Bucket(bucket_name)
    bucket.upload_file(
        Filename = file_path,
        Key = file_name,
        ExtraArgs= {'ACl': 'public-read'}
    ) 

    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
    return s3_url

s3_url = upload_file_to_bucket('rawbucket-yp', 'C:/Users/USER/Documents/data science/David_386/flattenedypsource.parquet')
print(s3_url)