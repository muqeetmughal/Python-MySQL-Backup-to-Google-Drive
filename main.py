import configparser
import os
import time
import getpass
from dataclasses import fields
from google.auth.transport.requests import Request
import os
import os.path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build
import os
import shutil
from sys import platform


class BackScript:
    BASE_DIR = os.path.dirname(os.path.realpath(__file__))
    foldername = "dbbackups"
    folderpath = os.path.join(BASE_DIR, foldername)

    def __init__(self):
        self.delete_all_backupfiles()
        time.sleep(2.5)
        self.make_folder()
        time.sleep(2.5)

    def delete_all_backupfiles(self):
        try:
            shutil.rmtree(self.folderpath)
        except Exception as e:
            # print(e)
            pass

    def make_folder(self):
        try:
            os.mkdir(self.folderpath)
        except Exception as e:
            # print(e)
            pass

    def google_drive_backup_init(self):
        SCOPES = ["https://www.googleapis.com/auth/drive"]

        creds = None

        if os.path.exists(os.path.join(self.BASE_DIR, "token.json")):
            creds = Credentials.from_authorized_user_file(os.path.join(self.BASE_DIR, "token.json"), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(os.path.join(self.BASE_DIR, "credentials.json"), SCOPES)
                creds = flow.run_local_server(port=0)

            with open(os.path.join(self.BASE_DIR, "token.json"),"w") as token:
                token.write(creds.to_json())



        try:
            service = build("drive","v3", credentials=creds)

            response = service.files().list(
                q="name='BackupFolder2022' and mimeType='application/vnd.google-apps.folder'", spaces='drive'
            ).execute()


            if not response['files']:
                file_metadata = {
                    "name" : "BackupFolder2022",
                    "mimeType" : "application/vnd.google-apps.folder"
                }
                file = service.files().create(body=file_metadata, fields="id").execute()

                folder_id = file.get('id')
            else:
                folder_id = response['files'][0]['id']

            for file in os.listdir(self.folderpath):
                file_metadata = {
                    "name" : file,
                    "parents" : [folder_id]
                }
                media = MediaFileUpload(os.path.join(self.folderpath, file))
                upload_file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()
                print(upload_file)
                print("backed up file : ", file)

        except HttpError as e:
            print("Error: ", str(e))




    def get_dump(self, database):

        HOST = database.get("host")
        DATABASE = database.get("db_name")

        PORT = database.get("port")
        DB_USER = database.get("db_user")
        DB_PASS = database.get("db_pass")

        timestamp = time.strftime('%Y-%m-%d--%H-%M')
        filepath = os.path.join(
            self.BASE_DIR, self.foldername, f"{HOST}_{DATABASE}_{timestamp}.sql")

        if platform == "linux" or platform == "linux2":
            mysqldump_path = "mysqldump"

        elif platform == "darwin":
            mysqldump_path = "mysqldump"

        elif platform == "win32":
            mysqldump_path = "C:\\xampp\\mysql\\bin\\mysqldump"

        if len(DB_PASS) == 0:

            dump_command = "%s -h %s -P %s -u %s %s > %s" % (
                mysqldump_path, HOST, PORT, DB_USER, DATABASE, filepath)

        else:
            dump_command = "%s -h %s -P %s -u %s -p%s %s > %s" % (
                mysqldump_path, HOST, PORT, DB_USER, DB_PASS, DATABASE, filepath)

        try:
            os.popen(dump_command)
            print(f"Database dumped to {filepath}")
        except Exception as e:
            print(e)


if __name__ == "__main__":

    instance = BackScript()
    databases = [
        {
            "host": '192.168.5.4',
            "port": '3306',
            "db_user": 'db_backup',
            "db_pass": '12345',
            "db_name": 'tmc_hrms'
        },
        {
            "host": '192.168.5.219',
            "port": '3306',
            "db_user": 'aun',
            "db_pass": '1234',
            "db_name": 'hesk'
        }
    ]

    for database in databases:

        instance.get_dump(database)

    instance.google_drive_backup_init()
