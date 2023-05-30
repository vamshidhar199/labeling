import boto3
s3 = boto3.resource('s3')
for bucket in s3.buckets.all():
    print(bucket.name)
# Set the name of the S3 bucket and the key of the object you want to download
def save(image):
    bucket_name = 'masterprojectbucket'
    object_key = 'ReportImages/'+image

    # Set the path of the local file where you want to save the downloaded image
    local_file_path = './img_dir/'+image
    s3.Bucket(bucket_name).download_file(object_key, local_file_path)
    
# bucket_name = 'my-bucket'
# source_key = 'path/to/my/image.jpg'
# dest_key = 'new/path/to/my/image.jpg'

# # Copy the object to the new key
# s3.copy_object(Bucket=bucket_name, CopySource={'Bucket': bucket_name, 'Key': source_key}, Key=dest_key)