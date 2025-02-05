import os
import re
import json
import mysql.connector
from datetime import datetime

def parse_log_line(line):
    match = log_pattern.match(line)
    if match:
        data = match.groupdict()
        data['datetime'] = datetime.strptime(data['datetime'], "%d/%b/%Y:%H:%M:%S %z").strftime("%Y-%m-%d %H:%M:%S")
        data['bytes'] = int(data['bytes']) if data['bytes'] != '-' else 0
        return data
    return None

def insert_db(cursor, log_data, vhost):
    sql = (
        "iNSERT INTO apache_logs (virtualhost, ip_address, identity, user, timestamp, method, endpoint, protocol, status_code, bytes_sent, referrer, user_agent) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
    )
    values = (
        vhost,
        log_data['ip'],
        '-',
        '-',
        log_data['datetime'],
        log_data['method'],
        log_data['endpoint'],
        log_data['protocol'],
        int(log_data['status']),
        log_data['bytes'],
        log_data['referrer'],
        log_data['user_agent']
    )
    cursor.execute(sql, values)
    
# ARCHIVO DE CONFIGURACIÓN DE LA BASE DE DATOS
config_file = "db_config.json"
##############################################

try:
    with open(config_file, 'r') as f:
        db_config = json.load(f)
except FileNotFoundError:
    print(f"Configuration file '{config_file}' not found.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error parsing the JSON configuration file: {e}")
    exit(1)

carpeta = "/var/log/apache2"
for root, dirs, files in os.walk(carpeta):
    for file in files:
        if file.endswith("access.log.1"):
            # print("Archivo encontrado:" + file)
            virtualh = file.split("-")[0]
            # print(virtualh)

            log_pattern = re.compile(
                r'(?P<ip>\S+) \S+ \S+ \[(?P<datetime>.*?)\] \"(?P<method>\S+) (?P<endpoint>.*?) (?P<protocol>.*?)\" (?P<status>\d{3}) (?P<bytes>\S+) \"(?P<referrer>.*?)\" \"(?P<user_agent>.*?)\"'
            )

            log_file_path = os.path.join(carpeta, file)

            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()

            try:
                with open(log_file_path, 'r') as file:
                    for line in file:
                        log_data = parse_log_line(line)
                        if log_data:
                            insert_db(cursor, log_data, virtualh)

                connection.commit()
                print("Log data inserted successfully.")

            except Exception as e:
                print(f"An error occurred: {e}")
                connection.rollback()

            finally:
                cursor.close()
                connection.close()
