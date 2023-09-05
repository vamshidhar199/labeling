import cv2
import time
import boto3

# AWS S3 Configuration
S3_BUCKET_NAME = 'masterprojectbucket'
AWS_ACCESS_KEY = 'AKIARWZZ67ATZUF5ROV6'
AWS_SECRET_KEY = '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'
S3_DIRECTORY = 'ReportImages/'

# Webcam Configuration
webcam = cv2.VideoCapture(0)  # Use 0 for default webcam
image_counter = 0

def upload_to_s3(local_file_path, s3_file_name):
    s3 = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )
    
    s3.upload_file(local_file_path, S3_BUCKET_NAME, s3_file_name)
    print(f'Uploaded {s3_file_name} to S3')
    

while True:
    ret, frame = webcam.read()
    if not ret:
        break
    
    image_counter += 1
    image_filename = f"image_{int(time.time())}.jpg" 

    cv2.imwrite(image_filename, frame)
    print(f'Saved {image_filename}')
    
    s3_file_name = S3_DIRECTORY + image_filename
    try:
        upload_to_s3(image_filename, s3_file_name)
    except Exception as e:
        print('Error uploading to S3:', e)

    time.sleep(1)  # Wait for 1 second

webcam.release()
cv2.destroyAllWindows()