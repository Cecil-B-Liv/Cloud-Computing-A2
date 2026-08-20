import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import botocore
import config
import aws_helpers


def password_for(i):
    # 6 digits rolling over: 0->012345, 9->901234
    return "".join(str((i + d) % 10) for d in range(6))


def create_login_table():
    ddb = aws_helpers.dynamodb_client()
    if config.LOGIN_TABLE in ddb.list_tables()["TableNames"]:
        print(f"[=] '{config.LOGIN_TABLE}' already exists")
        return

    print(f"[+] creating '{config.LOGIN_TABLE}'")
    ddb.create_table(
        TableName=config.LOGIN_TABLE,
        KeySchema=[{"AttributeName": "email", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "email", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    ddb.get_waiter("table_exists").wait(TableName=config.LOGIN_TABLE)
    print(f"[+] '{config.LOGIN_TABLE}' is active")


def seed_users():
    table = aws_helpers.table(config.LOGIN_TABLE)
    print("[+] seeding 10 users")
    for i in range(10):
        item = {
            "email": f"{config.STUDENT_ID}{i}@student.rmit.edu.au",
            "user_name": f"{config.STUDENT_NAME}{i}",
            "password": password_for(i),
        }
        table.put_item(Item=item)
        print(f"    {item['email']:38}  {item['user_name']:20}  {item['password']}")


if __name__ == "__main__":
    try:
        create_login_table()
        seed_users()
        print("\ndone")
    except botocore.exceptions.ClientError as e:
        print("AWS error:", e.response["Error"]["Code"], "-", e.response["Error"]["Message"])
        sys.exit(1)
