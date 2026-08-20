"""
Create the "subscriptions" table -- one row per (user, subscribed song).

Composite key:
    email (partition/HASH) + title (sort/RANGE)
This lets us list all of a user's subscriptions with a single Query on email,
and add/remove an individual song by (email, title).

Run:  .venv/Scripts/python.exe setup/05_create_subscriptions_table.py
Idempotent.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import botocore, config, aws_helpers


def create_subscriptions_table():
    ddb = aws_helpers.dynamodb_client()
    if config.SUBSCRIPTIONS_TABLE in ddb.list_tables()["TableNames"]:
        print(f"[=] Table '{config.SUBSCRIPTIONS_TABLE}' already exists -- skipping create.")
        return
    print(f"[+] Creating table '{config.SUBSCRIPTIONS_TABLE}' ...")
    ddb.create_table(
        TableName=config.SUBSCRIPTIONS_TABLE,
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
    print(f"[+] Table '{config.SUBSCRIPTIONS_TABLE}' is ACTIVE.")


if __name__ == "__main__":
    try:
        create_subscriptions_table()
        print("\nSUCCESS: subscriptions table ready.")
    except botocore.exceptions.ClientError as e:
        print("AWS ERROR:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
