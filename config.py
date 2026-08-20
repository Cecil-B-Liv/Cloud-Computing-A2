"""
Central configuration for the whole app.

Every setting has a sensible default but can be overridden with an environment
variable. That means the SAME code runs locally and on EC2 -- you only change
environment variables (or the defaults below), never the logic.
"""
import os

# AWS region. Learner Lab runs in us-east-1.
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

# --- DynamoDB table names ---
LOGIN_TABLE = os.environ.get("LOGIN_TABLE", "login")
MUSIC_TABLE = os.environ.get("MUSIC_TABLE", "music")
SUBSCRIPTIONS_TABLE = os.environ.get("SUBSCRIPTIONS_TABLE", "subscriptions")

# ======================================================================
#  YOUR DETAILS  --  used to seed the 10 login rows and name the bucket.
# ======================================================================
STUDENT_ID = os.environ.get("STUDENT_ID", "s3978680")          # RMIT SID, lowercase
STUDENT_NAME = os.environ.get("STUDENT_NAME", "Huynh Ngoc Tai")  # goes into user_name

# --- S3 bucket that holds the song images ---
# NOTE: S3 bucket names are GLOBALLY unique across all AWS accounts.
# Defaults to "<student-id>-a2-music-images" so it's unique to you.
S3_BUCKET = os.environ.get("S3_BUCKET", f"{STUDENT_ID.lower()}-a2-music-images")

# --- Assignment data file (the spec calls it a2.json) ---
DATA_FILE = os.environ.get("DATA_FILE", "Assignment2-spotify-data-1.json")

# --- Flask session secret (signs the login cookie) ---
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# --- How long a presigned image URL stays valid, in seconds (1 hour) ---
PRESIGNED_URL_TTL = int(os.environ.get("PRESIGNED_URL_TTL", "3600"))
