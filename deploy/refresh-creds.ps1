<#
  Refresh local AWS credentials from the running EC2 instance's LabRole.

  Pulls fresh temporary keys from the instance's metadata service over SSH and
  writes them to ~/.aws/credentials -- so you never copy-paste from the lab UI.
  Only works while the instance is running and reachable.

  USAGE (PowerShell, from the project folder):
      .\deploy\refresh-creds.ps1 <public-dns-or-ip>
  EXAMPLE:
      .\deploy\refresh-creds.ps1 ec2-98-94-64-239.compute-1.amazonaws.com

  If PowerShell blocks the script, run it once as:
      powershell -ExecutionPolicy Bypass -File deploy\refresh-creds.ps1 <dns-or-ip>
#>
param(
    [Parameter(Mandatory = $true, HelpMessage = "The instance's Public IPv4 DNS or IP")]
    [string]$Server
)
$ErrorActionPreference = "Stop"

$key = Join-Path $HOME ".aws\labsuser.pem"
if (-not (Test-Path $key)) { throw "SSH key not found at $key" }

# Remote one-liner: get an IMDSv2 token, the role name, then the credential JSON.
$remote = 'TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 300"); ROLE=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/); curl -s -H "X-aws-ec2-metadata-token: $TOKEN" "http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE"'

Write-Host "Fetching LabRole credentials from $Server ..."
$json = ssh -n -i $key -o StrictHostKeyChecking=accept-new -o ConnectTimeout=25 "ubuntu@$Server" $remote

$c = $json | ConvertFrom-Json
if ($c.Code -ne "Success") { throw "Metadata service did not return Success:`n$json" }

$cred = "[default]`n" +
        "aws_access_key_id=$($c.AccessKeyId)`n" +
        "aws_secret_access_key=$($c.SecretAccessKey)`n" +
        "aws_session_token=$($c.Token)`n"

$path = Join-Path $HOME ".aws\credentials"
# WriteAllText = UTF-8 without BOM (boto3-safe)
[System.IO.File]::WriteAllText($path, $cred)

Write-Host "OK - refreshed $path" -ForegroundColor Green
Write-Host "     keys expire at $($c.Expiration)"
