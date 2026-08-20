"""
Task 1.2 -- Create the "music" DynamoDB table (partition key = title).

Run:  .venv/Scripts/python.exe setup/02_create_music_table.py
Idempotent.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import botocore, config, aws_helpers


def create_music_table():
    ddb = aws_helpers.dynamodb_client()
    if config.MUSIC_TABLE in ddb.list_tables()["TableNames"]:
        print(f"[=] Table '{config.MUSIC_TABLE}' already exists -- skipping create.")
        return
    print(f"[+] Creating table '{config.MUSIC_TABLE}' ...")
    ddb.create_table(
        TableName=config.MUSIC_TABLE,
        KeySchema=[{"AttributeName": "title", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "title", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    ddb.get_waiter("table_exists").wait(TableName=config.MUSIC_TABLE)
    print(f"[+] Table '{config.MUSIC_TABLE}' is ACTIVE.")


if __name__ == "__main__":
    try:
        create_music_table()
        print("\nSUCCESS: music table ready.")
    except botocore.exceptions.ClientError as e:
        print("AWS ERROR:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
