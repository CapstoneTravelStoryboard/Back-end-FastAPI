import requests

import boto3
from botocore.exceptions import NoCredentialsError
from botocore.config import Config


from config.settings import AWS_BUCKET_NAME

config = Config(connect_timeout=90, read_timeout=90, retries={'max_attempts': 7})

def upload_to_s3(local_file: str, s3_file: str, bucket_name: str = AWS_BUCKET_NAME):
    # S3 client 생성
    s3_client = boto3.client('s3', config=config)

    try:
        # 파일 업로드
        s3_client.upload_file(local_file, bucket_name, s3_file)
        print(f'Upload Successful: {s3_file}')
        return True
    except FileNotFoundError:
        print(f'The file {local_file} was not found')
        return False
    except NoCredentialsError:
        print('Credentials not available')
        return False
    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return False


def download_image_from_url(url, local_file_path):
    # 이미지 다운로드
    response = requests.get(url)
    with open(local_file_path, 'wb') as f:
        f.write(response.content)
    print(f'Downloaded image from {url} to {local_file_path}')


# # 사용 예시
# if __name__ == '__main__':
#     image_url = r'https://files.oaiusercontent.com/file-9rBoAQS8JQBPE9wwJnoTvc?se=2024-12-09T19%3A38%3A49Z&sp=r&sv=2024-08-04&sr=b&rscc=max-age%3D604800%2C%20immutable%2C%20private&rscd=attachment%3B%20filename%3Dbf6ac881-eea0-4d8d-8c0c-a19d7847c4eb.webp&sig=jjX/Wp62W%2BOaY5q2lQ/nh012NvrvCLm6RNhRZ4Vf%2Bdw%3D'
#     local_image_path = 'image.jpg'
#
#     download_image_from_url(image_url, local_image_path)
#     upload_to_s3(local_image_path, 'images/image.jpg')
