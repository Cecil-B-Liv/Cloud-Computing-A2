# Demo-Day Cheat Sheet — COSC2980 A2

The app is **hosted on EC2**. Your laptop is just a **browser** (plus optional SSH).
The DynamoDB tables and S3 bucket persist independently of the instance.

Seed logins: `s39786800@student.rmit.edu.au` … `s39786809@...`
Passwords (rotating digits): user0 `012345`, user1 `123456`, … user9 `901234`.

---

## A. Start-up ritual (every session — the address changes each time)
1. **Learner Lab** → Start Lab (wait for green dot).
2. **EC2 console** → select **MyMusicApp** → Instance state → **Start** → wait "Running" + 2/2 checks.
3. Copy the new **Public IPv4 DNS** (e.g. `ec2-XX-XX-XX-XX.compute-1.amazonaws.com`).
4. Open **http://<that-dns>** in the browser. The app auto-starts (systemd) — no launching needed.
   - Click login once yourself to confirm it works before the marker watches.

## B. Reset the login table to exactly 10  (do this before the demo)
Testing the register page adds real users; rubric 1.1.1 wants exactly 10.
Download `labsuser.pem` from the lab (AWS Details), then run **on the instance**:
```
ssh -i labsuser.pem ubuntu@<dns> 'cd ~/music-app && .venv/bin/python setup/01_create_login_table.py'
```

## C. (Optional) refresh LOCAL creds — only if running AWS stuff from the laptop
```
bash deploy/refresh-creds.sh <dns>      # macOS / Git Bash
.\deploy\refresh-creds.ps1 <dns>        # Windows PowerShell
```
Not needed if you only use the browser.

---

## D. Demo walkthrough (maps to the rubric)
Open the AWS console tabs for DynamoDB + S3 alongside the browser.

| Rubric | What to show |
|---|---|
| 1.1.1 | DynamoDB `login` table → 10 items |
| 1.1.2 / 1.1.3 | DynamoDB `music` table → 128 items with title/artist/year/web_url/image_url |
| 1.2 | S3 bucket `s3978680-a2-music-images` → image objects |
| 1.3.1 | Login with WRONG password → "email or password is invalid" |
| 1.3.2 | Login correct (user0 / 012345) → redirected to main page |
| 1.5.1 | Main page header shows "Welcome, Huynh Ngoc Tai0" |
| 1.5.2 | Subscribe to a song → it appears under "Your Subscriptions" with image + Remove |
| 1.5.2.3 | Click Remove → gone from area and DynamoDB `subscriptions` |
| 1.5.3.1 | Query nonsense (e.g. Title "zzz") → "No result is retrieved. Please query again" |
| 1.5.3.2 | Query "american" → results (title/artist/year + image + Subscribe); try Title "40oz" + Artist "Sublime" to show AND |
| 1.5.3.2.3 | Subscribe from results → appears in subscription area + stored in DynamoDB |
| 1.4.1 | Register with an existing email → "The email already exists" |
| 1.4.2 | Register a NEW email → back to login → log in with it (⚠ then re-run step B to reset to 10) |
| 1.5.4 | Click Logout → back to login page |
| Hosting | Point out the URL is the EC2 Public IPv4 DNS on port 80 (Apache), not Beanstalk |

Nice extra to mention: images are served from S3 via **presigned URLs**; the whole app
was written from scratch (no templates); search matches by word in any order.

---

## E. If something's wrong
- **Page won't load:** the DNS changed — re-copy it from the EC2 console. Confirm the instance is "Running".
- **App error / 500:** on the instance, `sudo systemctl restart music apache2`, then check `sudo journalctl -u music -n 50`.
- **Instance missing entirely:** re-deploy with `deploy/DEPLOY.md` (~10 min); tables/images are safe in the cloud.
