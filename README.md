# Chassis Power Inventory (Cisco Intersight)

Sample Python script to fetch the **UCS Chassis Power Inventory ("General"
tab)** for a chassis identified by its serial number, using the Cisco
Intersight Python SDK.

This returns the same chassis-level power budget/capacity data shown on the
Intersight UI page:

```
https://intersight.com/an/infrastructure-service/an/network/chassis/<chassis-moid>/inventory/power
```

e.g. **Maximum Required Power**, **Maximum Available Grid Power**, Minimum
Required Power, Allocated Power, Non-Redundant/N+1/N+2 Maximum Power,
Extended Power Capacity, Power Rebalancing, and Power Save Mode.

It does **not** return individual PSU (Power Supply Unit) hardware details -
only the chassis-level summary.

Built using:
- Intersight API docs: https://intersight.com/apidocs/
- Intersight Python SDK: https://github.com/CiscoDevNet/intersight-python
- Intersight Python SDK examples: https://github.com/CiscoDevNet/intersight-python-utils
  (`credentials.py` and `helpers.py` in this repo are adapted from that repo)

## Files
| File | Purpose |
|---|---|
| `get_chassis_power_inventory.py` | Main script - looks up a chassis by serial and prints its power inventory summary |
| `credentials.py` | Configures the Intersight API client using a v3 API key (HTTP signature auth) |
| `helpers.py` | Table formatting helper (requires `tabulate`) |
| `requirements.txt` | Python package dependencies |

## ⚠️ Credentials are never stored in this repo
This repo contains **no API keys, secret keys, or tokens**. `.gitignore` is
configured to block common credential file patterns (`*SecretKey*`, `*.pem`,
etc.) from ever being committed. You must supply your own Intersight API
key and secret key locally when running the script (see below) - they stay
on your machine only.

## Setup

```bash
git clone https://github.com/siralucious/chassis_power.git
cd chassis_power
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 1. Generate an Intersight API key
1. Log in to Intersight (https://intersight.com, or your region/appliance URL).
2. Go to **System > Settings > API Keys** (top-right gear icon > Settings > API Keys),
   or navigate to your user Account's API Keys page.
3. Click **Generate API Key**.
4. Choose API key version **v3** (recommended; supports EC or RSA keys).
5. Give it a purpose/description and generate it.
6. **Copy/download the Secret Key** shown - this is only displayed once.
   Save it to a file, e.g. `~/.intersight/SecretKey.txt`.
7. Note the **API Key ID** shown next to it (format:
   `<accountMoid>/<userMoid>/<apikeyMoid>`, e.g.
   `5f8a1234.../5f8b5678.../5f8c9012...`). This ID is not itself secret, but
   is only useful together with the secret key.

## 2. Provide credentials to the script
The script (via `credentials.py`) reads credentials from **environment
variables** (recommended) or **CLI arguments**. It never reads them from a
file checked into this repo.

### Option A - Environment variables (recommended)
```bash
export INTERSIGHT_API_KEY_ID="<accountMoid>/<userMoid>/<apikeyMoid>"
export INTERSIGHT_API_PRIVATE_KEY="/absolute/path/to/SecretKey.txt"
```
Keep the secret key file permissions locked down:
```bash
chmod 600 /absolute/path/to/SecretKey.txt
```

### Option B - CLI arguments
```bash
python3 get_chassis_power_inventory.py \
    --api-key-id "<accountMoid>/<userMoid>/<apikeyMoid>" \
    --api-key-file /absolute/path/to/SecretKey.txt \
    --serial <chassis serial number>
```

> Never commit your `SecretKey.txt` file, and never paste its contents into
> a chat, issue, or commit message. Anyone with the secret key + key ID has
> full API access as your Intersight account/user.

## 3. Run the script
```bash
python3 get_chassis_power_inventory.py --serial FOX2743P0LL
```

For an EMEA-region SaaS account or an on-prem Intersight Appliance, pass the
appropriate `--url`:
```bash
python3 get_chassis_power_inventory.py --url https://eu-central-1.intersight.com --serial FOX2743P0LL
```

### Example output
```
Found chassis 'chassis-1' (Moid: 68a33cc56176753701f2d267, Model: UCSX-9508, Serial: FOX2743P0LL)

Power Inventory (General) for Chassis chassis-1 (Serial: FOX2743P0LL)

| Property                         | Value    |
|-----------------------------------+----------|
| Maximum Required Power (W)       | 6818     |
| Maximum Available Grid Power (W) | 8400     |
| Minimum Required Power (W)       | 4959     |
| Allocated Power (W)              | 0        |
| Non-Redundant Maximum Power (W)  | 16800    |
| N+1 Maximum Power (W)            | 14000    |
| N+2 Maximum Power (W)            | 11200    |
| Extended Power Capacity          | Disabled |
| Power Rebalancing                | Enabled  |
| Power Save Mode                  | Enabled  |
```

## How it works
1. Queries `equipment.Chassis` filtered by `Serial eq '<serial>'` to resolve
   the chassis Moid.
2. Queries `power.ControlState` filtered by
   `EquipmentChassis.Moid eq '<chassis moid>'` - this object holds the
   chassis-level power budget/capacity summary shown on the Intersight UI's
   Power Inventory **General** tab.
3. Prints the result as a table.

## Troubleshooting
- **`401 Unauthorized` / `iam_apikey_authheader_invalid`** - Key ID/secret
  mismatch, or wrong region `--url`. Confirm the key file starts with
  `-----BEGIN RSA PRIVATE KEY-----` or `-----BEGIN EC PRIVATE KEY-----`.
- **`ValueError: No chassis found with serial number '...'`** - the
  account/API key doesn't have visibility to that chassis, or the serial is
  incorrect.
- **`ModuleNotFoundError`** - activate the virtual environment
  (`source .venv/bin/activate`) before running.
