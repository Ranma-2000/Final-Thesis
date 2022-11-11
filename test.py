import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = "jv0vc7lfTuKACYxvWu_n6rgEbPMgwy4s72YFUnqnPUrpnvSpA0iNVs4qlH3Jz3l2h3enAb2zcW191KbjeS2GUg=="
org = "18146115@student.hcmute.edu.vn"
url = "https://us-east-1-1.aws.cloud2.influxdata.com"

client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
