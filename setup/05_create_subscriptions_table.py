import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import botocore, config, aws_helpers


def create_subscriptions_table():
    ddb = aws_helpers.dynamodb_client()
    if config.SUBSCRIPTIONS_TABLE in ddb.list_tables()["TableNames"]:
        print(f"[=] '{config.SUBSCRIPTIONS_TABLE}' already exists")
        return
    print(f"[+] creating '{config.SUBSCRIPTIONS_TABLE}'")
    ddb.create_table(
        TableName=config.SUBSCRIPTIONS_TABLE,
        # email = who, title = which song
        KeySchema=[
            {"AttributeName": "email", "KeyType": "HASH"},
            {"AttributeName": "title", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "email", "AttributeType": "S"},
            {"AttributeName": "title", "AttributeType": "S"},
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    ddb.get_waiter("table_exists").wait(TableName=config.SUBSCRIPTIONS_TABLE)
    print(f"[+] '{config.SUBSCRIPTIONS_TABLE}' is active")


if __name__ == "__main__":
    try:
        create_subscriptions_table()
        print("\ndone")
    except botocore.exceptions.ClientError as e:
        print("AWS error:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
