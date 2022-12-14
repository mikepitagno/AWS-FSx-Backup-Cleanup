#!/usr/bin/env python3
    
'''
#############################
AWS FSx Backup Report
#############################
'''
    
from datetime import date
from datetime import datetime
import json
import subprocess
import smtplib
from email.mime.text import MIMEText
    
email_sender = '<EMAIL SENDER>'
email_receiver = '<EMAIL RECEIVER>'
smtp_server = '<SMTP SERVER>'
max_age = 7
    
def get_backup_info(profile='default'): # Use Python subprocess to have the AWS CLI pull all user initated backups into a JSON formatted variable
    
    backupinfo = subprocess.run(["/usr/local/bin/aws", "fsx", "describe-backups", "--output", "json", "--filter", "Name=backup-type,Values=USER_INITIATED", "--profile", profile], stdout=subprocess.PIPE)
    backupinfo_utf8 = backupinfo.stdout.decode('utf-8')
    backupinfo_utf8_json = json.loads(backupinfo_utf8)
    return backupinfo_utf8_json

def get_backups2delete(backup_dict, max_age): # Iterate through 'backup_dict' and find any backups older than 'max_age' 
    
    backups2delete = {}
    date_current = date.today()
    
    for i in backup_dict['Backups']:
        backupid = i['BackupId']
        filesystem = i['FileSystem']
        date_backup = (i['CreationTime'].split('T')[0])
        new_date_backup = datetime.strptime(date_backup, '%Y-%m-%d').date()
        duration = date_current - new_date_backup
        if duration.days > max_age:
            backups2delete[backupid] = { "FileSystem Details": filesystem, "Backup Date": date_backup }
    return backups2delete

def convert_dict2string(backups2delete): # Convert 'backups2delete' into string format for use in email 
    
    output_file = ''
    for k, v in sorted(backups2delete.items()):
        output_file = output_file + '\n'
        output_file = output_file + k + '\n'
        for k1, v1 in sorted(v.items()):
            output_file = output_file + "-%s: %s" % (k1, v1) + '\n'
    return output_file

def email_report(backups2delete, email_sender, email_receiver, smtp_server, max_age): # Email backup report
    
    max_age_str = str(max_age)
    title = "### AWS FSx Backups older than " + max_age_str + " days ###\n"
    body = title + "\n" + convert_dict2string(backups2delete) + "\n"
    msg = MIMEText(body)
    msg['Subject'] = "AWS FSx Backup Report"
    msg['From'] = email_sender
    msg['To'] = email_receiver
    s = smtplib.SMTP(smtp_server)
    s.sendmail(email_sender, [email_receiver], msg.as_string())
    s.quit()

# Call 'get_backup_info' function to create a dictionary of all AWS FSx user initiated backups
backup_dict_default = get_backup_info()
backup_dict_dev = get_backup_info('dev')
backup_dict_prod = get_backup_info('prod')
    
# Call 'get_backups2delete' function to get a dictionary of all backups older than days specified in second argument
backups2delete_default = get_backups2delete(backup_dict_default, max_age)
backups2delete_dev = get_backups2delete(backup_dict_dev, max_age)
backups2delete_prod = get_backups2delete(backup_dict_prod, max_age)
    
# Combine dictionaries created from backups2delete function into single dictionary
backups2delete_all = {}
backups2delete_all['Backups-default'] = backups2delete_default
backups2delete_all['Backups-dev'] = backups2delete_dev
backups2delete_all['Backups-prod'] = backups2delete_prod
    
# Call 'email_report' to covert 'backups2delete_all' dictionary into email format and send
email_report(backups2delete_all, email_sender, email_receiver, smtp_server, max_age)
