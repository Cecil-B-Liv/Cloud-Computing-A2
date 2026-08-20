#!/usr/bin/env bash
#
# Refresh local AWS credentials from the running EC2 instance's LabRole.
# Cross-platform: works on macOS (Terminal) and Windows (Git Bash).
#
# It SSHes into the instance, reads fresh temporary keys from the instance
# metadata service, and writes them to ~/.aws/credentials -- so you never
# copy-paste from the lab UI. Only works while the instance is running.
#
# USAGE:
#     bash deploy/refresh-creds.sh <public-dns-or-ip>
# EXAMPLE:
#     bash deploy/refresh-creds.sh ec2-98-94-64-239.compute-1.amazonaws.com
#
set -e

HOST="$1"
if [ -z "$HOST" ]; then
  echo "usage: bash deploy/refresh-creds.sh <public-dns-or-ip>"
  exit 1
fi

KEY="$HOME/.aws/labsuser.pem"
if [ ! -f "$KEY" ]; then
  echo "SSH key not found at $KEY"
  exit 1
fi
chmod 600 "$KEY" 2>/dev/null || true   # ssh refuses keys that are too open

echo "Fetching LabRole credentials from $HOST ..."
# -n stops ssh from swallowing stdin (otherwise capture comes back empty).
JSON=$(ssh -n -i "$KEY" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=25 "ubuntu@$HOST" \
  'TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300"); ROLE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/); curl -s -H "X-aws-ec2-metadata-token: $TOKEN" "http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE"')

# Pull each value out of the JSON with sed (no jq/python needed).
get() { printf '%s' "$JSON" | sed -n "s/.*\"$1\" : \"\([^\"]*\)\".*/\1/p"; }
AKID=$(get AccessKeyId)
SECRET=$(get SecretAccessKey)
TOKEN=$(get Token)

if [ -z "$AKID" ] || [ -z "$SECRET" ] || [ -z "$TOKEN" ]; then
  echo "ERROR: could not read credentials. Raw response:"
  echo "$JSON"
  exit 1
fi

CREDS="$HOME/.aws/credentials"
printf '[default]\naws_access_key_id=%s\naws_secret_access_key=%s\naws_session_token=%s\n' \
  "$AKID" "$SECRET" "$TOKEN" > "$CREDS"

echo "OK - refreshed $CREDS"
echo "     keys expire at $(get Expiration)"
