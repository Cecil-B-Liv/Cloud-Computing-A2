# Deploying the Music App to EC2 (Ubuntu 20.04)

Public flow:  Browser :80  ->  Apache  ->  gunicorn 127.0.0.1:8000  ->  Flask

## 1. Launch the instance (AWS console, in the Learner Lab)
- AMI: **Ubuntu Server 20.04 LTS**, Architecture 64-bit (x86)
- Type: **t2.micro** (free tier)
- Key pair: **vockey** (download `labsuser.pem` from the lab if you don't have it)
- IAM instance profile: **LabInstanceProfile** (Advanced details -> IAM instance profile)
- Security group inbound rules: **SSH 22** (My IP) and **HTTP 80** (Anywhere 0.0.0.0/0)

## 2. SSH in (from your PC)
    ssh -i labsuser.pem ubuntu@<PUBLIC-IPv4-DNS>

## 3. Install packages
    sudo apt update
    sudo apt install -y python3-venv python3-pip apache2
    sudo a2enmod proxy proxy_http

## 4. Copy the project (run on your PC, then it lands in ~/music-app)
    # from your project folder, create a bundle without the Windows venv:
    #   (PowerShell) Compress-Archive -Path * -DestinationPath music-app.zip -Force
    scp -i labsuser.pem music-app.zip ubuntu@<PUBLIC-IPv4-DNS>:~
    # back on the instance:
    unzip music-app.zip -d ~/music-app

## 5. Python env + deps (on the instance)
    cd ~/music-app
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt

## 6. Verify AWS access (instance profile should just work)
    .venv/bin/python -c "import boto3; print(boto3.client('sts').get_caller_identity()['Arn'])"
    # If that errors, copy your ~/.aws/credentials to the instance as a fallback.

## 7. Run under gunicorn (systemd)
    sudo cp deploy/gunicorn.service /etc/systemd/system/music.service
    sudo systemctl daemon-reload
    sudo systemctl enable --now music
    sudo systemctl status music        # should be "active (running)"

## 8. Apache in front on port 80
    sudo cp deploy/music.conf /etc/apache2/sites-available/music.conf
    sudo a2dissite 000-default
    sudo a2ensite music
    sudo systemctl restart apache2

## 9. Open it
    http://<PUBLIC-IPv4-DNS>       (no port number needed)

## Handy checks
    sudo systemctl status music apache2
    sudo journalctl -u music -n 50 --no-pager     # app logs
    sudo tail -n 50 /var/log/apache2/music_error.log

## 10. (Optional) HTTPS with a self-signed cert
    sudo a2enmod ssl
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout /etc/ssl/private/music-selfsigned.key \
      -out /etc/ssl/certs/music-selfsigned.crt -subj "/CN=music-app"
    sudo cp deploy/music-ssl.conf /etc/apache2/sites-available/music-ssl.conf
    sudo a2ensite music-ssl
    sudo systemctl restart apache2
    # then open port 443 (HTTPS) in the security group
    # self-signed -> browser shows "not private" -> Advanced -> Proceed
