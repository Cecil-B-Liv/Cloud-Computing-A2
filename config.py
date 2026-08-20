import os

AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

LOGIN_TABLE = os.environ.get("LOGIN_TABLE", "login")
MUSIC_TABLE = os.environ.get("MUSIC_TABLE", "music")
SUBSCRIPTIONS_TABLE = os.environ.get("SUBSCRIPTIONS_TABLE", "subscriptions")

# my student id + name, used to seed the logins and name the bucket
STUDENT_ID = os.environ.get("STUDENT_ID", "s3978680")
STUDENT_NAME = os.environ.get("STUDENT_NAME", "Huynh Ngoc Tai")

# bucket names are globally unique, so prefix with the student id
S3_BUCKET = os.environ.get("S3_BUCKET", f"{STUDENT_ID.lower()}-a2-music-images")

DATA_FILE = os.environ.get("DATA_FILE", "Assignment2-spotify-data-1.json")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
PRESIGNED_URL_TTL = int(os.environ.get("PRESIGNED_URL_TTL", "3600"))
