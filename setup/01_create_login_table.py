"""
Task 1.1 -- Create the "login" DynamoDB table and seed 10 users.

Run:  .venv/Scripts/python.exe setup/01_create_login_table.py
Safe to run multiple times (idempotent).
"""
import sys, os
# Allow importing config.py / aws_helpers.py from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import botocore
import config
import aws_helpers


def password_for(i: int) -> str:
    """Index i -> 6 digits that roll over: 0->'012345', 1->'123456', 9->'901234'."""
    return "".join(str((i + d) % 10) for d in range(6))


def create_login_table():
    ddb = aws_helpers.dynamodb_client()
    existing = ddb.list_tables()["TableNames"]
    if config.LOGIN_TABLE in existing:
        print(f"[=] Table '{config.LOGIN_TABLE}' already exists -- skipping create.")
        return

    print(f"[+] Creating table '{config.LOGIN_TABLE}' ...")
    ddb.create_table(
        TableName=config.LOGIN_TABLE,
        # KeySchema: 'email' is the partition (HASH) key -- how items are found.
        KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
        # You only declare attributes that are part of a key.
        AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
        # On-demand: pay per request, no capacity planning.
        BillingMode="PAY_PER_REQUEST",
    )
    # Block until the table is ready to accept writes.
    ddb.get_waiter("table_exists").wait(TableName=config.LOGIN_TABLE)
    print(f"[+] Table '{config.LOGIN_TABLE}' is ACTIVE.")


def seed_users():
    table = aws_helpers.table(config.LOGIN_TABLE)
    print(f"[+] Seeding 10 users into '{config.LOGIN_TABLE}' ...")
    for i in range(10):
        item = {
            "email": f"{config.STUDENT_ID}{i}@student.rmit.edu.au",
            "user_name": f"{config.STUDENT_NAME}{i}",
            "password": password_for(i),
        }
        table.put_item(Item=item)  # put_item = insert-or-overwrite (upsert)
        print(f"    {item['email']:38}  {item['user_name']:20}  {item['password']}")
    print("[+] Done seeding.")


if __name__ == "__main__":
    try:
        create_login_table()
        seed_users()
        print("\nSUCCESS: login table ready with 10 users.")
    except botocore.exceptions.ClientError as e:
        print("AWS ERROR:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
