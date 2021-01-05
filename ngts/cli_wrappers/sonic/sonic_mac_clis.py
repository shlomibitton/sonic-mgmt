import os
import tempfile
import json

from ngts.cli_wrappers.common.mac_clis_common import MacCliCommon
from ngts.helpers.network import generate_mac


class SonicMacCli(MacCliCommon):

    @staticmethod
    def show_mac(engine):
        """
        This method runs 'show mac' command
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('show mac')

    @staticmethod
    def generate_fdb_config_on_dut(engine, entries_num, vlan_id, iface, op, dest_file):
        """ Generate FDB config file and copy it to the DUT.
        Generated config file template:
        [
            {
                "FDB_TABLE:Vlan[VID]:XX-XX-XX-XX-XX-XX": {
                    "port": [Interface],
                    "type": "dynamic"
                },
                "OP": ["SET"|"DEL"]
            }
        ]
        :param engine: ssh engine object
        :param entries_num: number of fdb entries
        :param vlan_id: VLAN name
        :param iface: interface name
        :param op: config DEL or SET operation
        :param dest_file: temporal config file name stored on DUT
        """
        fdb_config_json = []
        entry_key_template = "FDB_TABLE:Vlan{vid}:{mac}"

        for mac_address in generate_mac(entries_num):
            fdb_entry_json = {entry_key_template.format(vid=vlan_id, mac=mac_address):
                {"port": iface, "type": "dynamic"},
                "OP": op
            }
            fdb_config_json.append(fdb_entry_json)

        with tempfile.NamedTemporaryFile(suffix=".json", prefix="fdb_config", mode='w') as fp:
            json.dump(fdb_config_json, fp)
            fp.flush()

            # Copy FDB JSON config to switch
            dst_dir, file_name = os.path.split(dest_file)
            engine.copy_file(source_file=fp.name, dest_file=file_name, file_system=dst_dir,
                overwrite_file=True, verify_file=False)
        return dest_file

    @staticmethod
    def fdb_config(action, engine, vlan_id, iface, entry_num):
        """
        Creates FDB config and applies it on DUT
        :param action: SET or DEL action. Will create or remove FDB config on DUT
        :param engine: ssh engine object
        :param vlan_id: VLAN name
        :param iface: interface name
        :param entry_num: number of fdb entries
        """
        dut_tmp_dir = "/tmp"
        cfg_file = "fdb.json"
        dut_fdb_config = os.path.join(dut_tmp_dir, cfg_file)
        rm_fdb_swss = "docker exec -i swss rm /{}".format(cfg_file)
        actions = ["SET", "DEL"]

        engine.run_cmd("mkdir -p {}".format(dut_tmp_dir))

        if action not in actions:
            raise Exception("Incorrect action specified {}. Supported {}".format(action, actions))

        if entry_num < 1:
            raise Exception("Incorrect number of FDB entries specified - {}".format(entry_num))

        # Generate FDB config and store it to DUT
        SonicMacCli.generate_fdb_config_on_dut(engine, entry_num, vlan_id, iface, action, dut_fdb_config)

        # Copy FDB JSON config to SWSS container
        cmd = "docker cp {} swss:/".format(dut_fdb_config)
        engine.run_cmd(cmd)

        # Add FDB entry
        cmd = "docker exec -i swss swssconfig /{}".format(cfg_file)
        engine.run_cmd(cmd)

        # Remove tmp files
        engine.run_cmd(rm_fdb_swss)
        engine.run_cmd("rm {}".format(dut_fdb_config))
