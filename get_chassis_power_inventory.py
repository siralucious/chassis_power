"""Get UCS Chassis Power Inventory (General tab) by Chassis Serial Number

This script queries Cisco Intersight for a UCS chassis identified by its
serial number, then retrieves the chassis-level power inventory summary -
the same data shown on the Intersight UI's:

    Chassis > Inventory > Power > General tab

e.g. https://intersight.com/an/infrastructure-service/an/network/chassis/<moid>/inventory/power

This is the overall chassis power-budget/capacity information (Maximum
Required Power, Maximum Available Grid Power, etc.) - NOT the list of
individual PSU (Power Supply Unit) hardware details.

Reference material used to build this script:
    - Intersight API docs / API reference:        https://intersight.com/apidocs/
    - Intersight Python SDK:                       https://github.com/CiscoDevNet/intersight-python
    - Intersight Python SDK usage examples:        https://github.com/CiscoDevNet/intersight-python-utils

API objects used:
    - equipment.Chassis  -> resolve chassis Moid from its Serial number
    - power.ControlState -> chassis power budget/capacity summary
                             (the "General" tab of the chassis Power Inventory
                             page), related to equipment.Chassis via the
                             'EquipmentChassis' relationship/Moid

Authentication:
    Uses the same v3 API key (HTTP signature) pattern as credentials.py from
    intersight-python-utils. Provide credentials via CLI args or environment
    variables:

        export INTERSIGHT_API_KEY_ID=<api key id>
        export INTERSIGHT_API_PRIVATE_KEY=/path/to/SecretKey.txt

    or:

        python get_chassis_power_inventory.py \
            --api-key-id <api key id> \
            --api-key-file /path/to/SecretKey.txt \
            --serial FOX2743P0LL

Requirements:
    pip install intersight tabulate
"""

import logging
import sys
import traceback

import intersight
from intersight.api import equipment_api
from intersight.api import power_api

import credentials
from helpers import print_results_to_table

FORMAT = '%(asctime)-15s [%(levelname)s] [%(filename)s:%(lineno)s] %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
logger = logging.getLogger('chassis_power_inventory')

# Fields to select/display for the chassis lookup
CHASSIS_SELECT = 'Moid,Dn,Name,Model,Serial'

# power.ControlState field -> human readable label, matching the Intersight
# UI's Chassis > Inventory > Power > General tab
POWER_CONTROL_STATE_LABELS = {
    'max_required_power': 'Maximum Required Power (W)',
    'grid_max_power': 'Maximum Available Grid Power (W)',
    'min_required_power': 'Minimum Required Power (W)',
    'allocated_power': 'Allocated Power (W)',
    'non_redundant_max_power': 'Non-Redundant Maximum Power (W)',
    'n1_max_power': 'N+1 Maximum Power (W)',
    'n2_max_power': 'N+2 Maximum Power (W)',
    'extended_power_capacity': 'Extended Power Capacity',
    'power_rebalancing': 'Power Rebalancing',
    'power_save_mode': 'Power Save Mode',
}


def get_chassis_by_serial(api_client, serial):
    """Look up a single equipment.Chassis resource by its Serial number."""
    api_instance = equipment_api.EquipmentApi(api_client)
    response = api_instance.get_equipment_chassis_list(
        filter=f"Serial eq '{serial}'",
        select=CHASSIS_SELECT
    )
    if not response.results:
        raise ValueError(f"No chassis found with serial number '{serial}'")
    return response.results[0]


# API (PascalCase) field names to request via $select - must match the
# OpenAPI 'attribute_map' names, not the Python snake_case attribute names.
POWER_CONTROL_STATE_SELECT = (
    'MaxRequiredPower,GridMaxPower,MinRequiredPower,AllocatedPower,'
    'NonRedundantMaxPower,N1MaxPower,N2MaxPower,ExtendedPowerCapacity,'
    'PowerRebalancing,PowerSaveMode'
)


def get_chassis_power_control_state(api_client, chassis_moid):
    """Get the power.ControlState (chassis power budget/capacity summary) for a chassis Moid.

    This corresponds to the "General" tab of the chassis Power Inventory
    page in the Intersight UI.
    """
    api_instance = power_api.PowerApi(api_client)
    response = api_instance.get_power_control_state_list(
        filter=f"EquipmentChassis.Moid eq '{chassis_moid}'",
        select=POWER_CONTROL_STATE_SELECT
    )
    if not response.results:
        return None
    return response.results[0]


def main():
    # Get existing argument parser from credentials and extend it
    parser = credentials.Parser
    parser.description = 'Get UCS Chassis Power Inventory (General tab: Maximum Required Power, Maximum Available Grid Power, etc.) by chassis serial number'
    parser.add_argument('--serial', default='FOX2743P0LL',
                         help='Serial number of the UCS chassis to look up (default: FOX2743P0LL)')

    # Create Intersight API client instance and parse authentication arguments
    api_client = credentials.config_credentials()

    # Parse arguments again to retrieve the --serial value
    args = parser.parse_args()

    try:
        # Step 1: Resolve the chassis Moid from its serial number
        chassis = get_chassis_by_serial(api_client, args.serial)
        logger.info(
            "Found chassis '%s' (Moid: %s, Model: %s, Serial: %s)",
            chassis.dn, chassis.moid, chassis.model, chassis.serial
        )

        # Step 2: Retrieve the chassis-level power budget/capacity summary
        # (the "General" tab of the chassis Power Inventory page)
        power_state = get_chassis_power_control_state(api_client, chassis.moid)

        if power_state is None:
            logger.warning("No power inventory (power.ControlState) entry found for chassis serial '%s'", args.serial)
            return

        print(f"\nPower Inventory (General) for Chassis {chassis.dn} (Serial: {chassis.serial})\n")
        state_dict = power_state.to_dict()
        rows = [
            {'Property': label, 'Value': state_dict.get(field)}
            for field, label in POWER_CONTROL_STATE_LABELS.items()
        ]
        try:
            print_results_to_table(rows)
        except NameError:
            # tabulate not installed - fall back to plain output
            for row in rows:
                print(f"{row['Property']}: {row['Value']}")

    except intersight.OpenApiException as exp:
        logger.error("Exception when calling Intersight API: %s\n", exp)
        traceback.print_exc()
        sys.exit(1)
    except ValueError as exp:
        logger.error(str(exp))
        sys.exit(1)


if __name__ == "__main__":
    main()
