import subprocess
from pyairtable import Api
import platform
import subprocess
import uuid
from asyncio.windows_events import NULL

from pyairtable import Api

from amir_adv.globals import ENV_NAME


class AirTableApi:
    def __init__(self, config):
        self.api_key = config["airtable_api_key"]
        self.base_id = config["airtable_base_id"]
        self.table_name = config["airtable_table_name"]
        self.api = Api(self.api_key)
        self.table = self.api.table(self.base_id, self.table_name)
# supported at Win 11
    def get_hardware_id(self):
        try:
            if platform.system() == "Windows":
                cmd = "powershell -Command \"(Get-CimInstance -Class Win32_ComputerSystemProduct).UUID\""
                hw_id = subprocess.check_output(cmd, shell=True, text=True).strip()
                if hw_id:
                    return f"winner_{hw_id}"
                else :
                    return ENV_NAME
        except Exception:
            pass

        return str(uuid.getnode())

    def verify_or_register_license(self, hw_id_field_name="HWID", status_field_name="Status",
                                   counter_field_name="Counter"):

        hw_id = self.get_hardware_id()

        formula = f"{{{hw_id_field_name}}} = '{hw_id}'"
        records = self.table.all(formula=formula)

        if records:
            record = records[0]
            record_id = record['id']
            status = str(record['fields'].get(status_field_name, '')).strip().lower()

            if status == 'valid':
                current_count = record['fields'].get(counter_field_name, 0)
                if current_count is None:
                    current_count = 0

                new_count = int(current_count) + 1

                self.table.update(record_id, {
                    counter_field_name: new_count
                })
                return True
            else:
                print ("License Expired Found")
                return False
        else:
            print("HW ID not Found creating new one")

            self.table.create({
                hw_id_field_name: hw_id,
                status_field_name: 'Pending',
                counter_field_name: 0
            })
            return False

