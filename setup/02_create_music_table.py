import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import botocore, config, aws_helpers


def create_music_table():
    ddb = aws_helpers.dynamodb_client()
    if config.MUSIC_TABLE in ddb.list_tables()["TableNames"]:
        print(f"[=] '{config.MUSIC_TABLE}' already exists")
        return
    print(f"[+] creating '{config.MUSIC_TABLE}'")
    ddb.create_table(
        TableName=config.MUSIC_TABLE,
        KeySchema=[{"AttributeName": "title", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "title", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    ddb.get_waiter("table_exists").wait(TableName=config.MUSIC_TABLE)
    print(f"[+] '{config.MUSIC_TABLE}' is active")


if __name__ == "__main__":
    try:
        create_music_table()
        print("\ndone")
    except botocore.exceptions.ClientError as e:
        print("AWS error:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
