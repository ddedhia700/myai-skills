# Components Reference

Detailed documentation of each component and file.

---

## Table of Contents

1. [Network Types](#network-types)
2. [Network Instances](#network-instances)
3. [Templates](#templates)
4. [Python Scripts](#python-scripts)
5. [Output Artifacts](#output-artifacts)

---

## Network Types

### `network_types/spine_leaf_3tier.schema.yml`

**Purpose:** Define the pattern for spine-leaf 3-tier CLOS fabrics

**Structure:**

```yaml
network_type: "spine_leaf_3tier"
description: "3-tier CLOS spine-leaf fabric with full mesh topology"

parameters:
  # All configurable parameters
  # Each has type, default, min/max constraints

description_notes: |
  # Explains design pattern and topology
```

**Key Fields:**

| Field | Type | Purpose |
|-------|------|---------|
| `network_type` | string | Identifier (must be unique) |
| `description` | string | Human-readable summary |
| `parameters` | dict | Allowed configuration options |
| `description_notes` | string | Design pattern explanation |

**Example Parameter:**

```yaml
spine_count:
  type: integer
  min: 2
  max: 32
  description: "Number of spine switches"
```

**Validator** (`validate.py`) checks that instance values conform to schema constraints.

**How to Extend:**

Add new schema for different topology:

```bash
cp network_types/spine_leaf_3tier.schema.yml network_types/collapsed_core.schema.yml
# Edit collapsed_core.schema.yml with new parameters
```

---

## Network Instances

### `network_instances/prototype_a/`

Directory structure for one network instance.

```
network_instances/prototype_a/
├── config.yml       (parameter values)
└── network_a.yml    (full network definition - GENERATED from config.yml + logic)
```

---

### `network_instances/prototype_a/config.yml`

**Purpose:** Store parameter values for this specific instance

**What:** Only the values, no logic

```yaml
network_type: "spine_leaf_3tier"
network_name: "prototype_a"

parameters:
  site_prefix: "proto"
  spine_count: 2
  leaf_count: 2
  loopback_base: "10.0.1.0/24"
  management_base: "192.168.1.0/24"
  transit_base: "10.0.0.0/24"
  routing_protocol: "bgp"
  underlay: "ospf"
  overlay: "vxlan"
  vrf_count: 2

vrfs:
  blue:
    rd: "65000:1"
    subnet: "10.0.10.0/23"
  red:
    rd: "65000:2"
    subnet: "10.0.20.0/23"
```

**Rules:**
- Must match schema in `network_types/`
- Values are literal (no calculations)
- CIDR blocks must be valid
- VRF RDs must be unique

**How to Create New Instance:**

```bash
# Create folder
mkdir -p network_instances/production

# Copy and modify config
cp network_instances/prototype_a/config.yml network_instances/production/config.yml
# Edit production/config.yml with your values

# Create network definition
vi network_instances/production/network_prod.yml
# (Full device/link definitions for production)

# Run pipeline with new paths
# (Update paths in *.py scripts)
```

---

### `network_instances/prototype_a/network_a.yml`

**Purpose:** Complete network definition (devices, links, VRFs)

**What:** This is the **input** to the pipeline

```yaml
design:
  name: clos-prototype
  architecture: spine_leaf
  routing_protocol: bgp
  underlay: ospf

devices:
  spine-01:
    hostname: spine-01
    platform: arista_eos
    role: spine
    asn: 65000
    loopback_ip: 10.0.1.1
    management_ip: 192.168.1.10
    rr_server: true

links:
  - name: L1
    source: spine-01
    source_port: Ethernet1
    target: leaf-01
    target_port: Ethernet1/1
    subnet: 10.0.0.0/31

vrfs:
  blue:
    rd: "65000:1"
    subnet: 10.0.10.0/23
```

**Key Sections:**

### `design` (metadata)
```yaml
design:
  name: string              # Network name
  architecture: string      # Topology type (spine_leaf, collapsed_core)
  routing_protocol: string  # bgp or ospf
  underlay: string          # ospf or isis (for transit links)
```

### `devices` (all network devices)
```yaml
device_name:
  hostname: string          # Config hostname
  platform: string          # arista_eos, cisco_nxos, juniper_junos
  role: string              # spine, leaf, access, core
  asn: integer              # BGP ASN (can be null for access)
  loopback_ip: CIDR         # Loopback /32
  management_ip: CIDR       # Management IP
  rr_server: boolean        # BGP Route Reflector (for spines)
  rr_client: boolean        # BGP RR client (for leaves)
```

### `links` (connections between devices)
```yaml
- name: string              # Link ID (L1, L2, etc.)
  source: string            # Source device name
  source_port: string       # Source interface
  target: string            # Target device name
  target_port: string       # Target interface
  subnet: CIDR              # /31 subnet for link
```

### `vrfs` (virtual routing/forwarding)
```yaml
vrf_name:
  rd: string                # Route Distinguisher (e.g., "65000:1")
  subnet: CIDR              # VRF subnet pool
  description: string       # Human-readable
```

**Editing Rules:**
- Device names must be unique
- Link names must be unique
- ASN must be valid (1-4200000000)
- CIDR blocks must not overlap
- Link subnets must be /31
- Referenced devices in links must exist
- VRF RDs must be unique

---

## Templates

### `templates/eos_spine.j2`

**Purpose:** Generate Arista EOS configuration for spine devices

**Syntax:** Jinja2 template language

```jinja2
hostname {{ device }}
!
router ospf 1
  router-id {{ config.loopback_ip }}
!
router bgp {{ config.asn }}
  router-id {{ config.loopback_ip }}
  {% if config.rr_server %}
  bgp cluster-id {{ config.loopback_ip }}
  {% endif %}
  !
  {% for neighbor in config.bgp_neighbors %}
  neighbor {{ neighbor.ip }} remote-as {{ neighbor.asn }}
  {% endfor %}
```

**Variables Available:**

| Variable | Type | Content |
|----------|------|---------|
| `device` | string | Device name (e.g., "spine-01") |
| `config` | dict | Device configuration (asn, loopback_ip, etc.) |
| `config.bgp_neighbors` | list | List of BGP neighbors (calculated by generate_ipam.py) |
| `links` | dict | Links for this device |
| `links[name]` | dict | {port, ip, neighbor, neighbor_ip} |
| `vrfs` | dict | VRF definitions |

**How Variables are Populated:**

```python
# From render_config.py
context = {
    'device': 'spine-01',                    # Device name
    'config': ipam['devices']['spine-01'],   # From IPAM
    'links': {...},                          # Filtered for this device
    'vrfs': ipam['vrfs']                     # From IPAM
}
rendered = template.render(context)
```

**Extending for New Features:**

Add VLAN configuration:

```jinja2
! VLANs
{% for vlan_id, vlan_name in vlans.items() %}
vlan {{ vlan_id }}
  name {{ vlan_name }}
{% endfor %}
```

Then add `vlans` to context in render_config.py:
```python
context['vlans'] = {...}  # VLANs from network definition
```

---

### `templates/nxos_leaf.j2`

**Purpose:** Generate Cisco NXOS configuration for leaf devices

**Syntax:** Jinja2 (same as EOS, but NXOS-specific syntax)

**Differences from EOS:**
- `ip router ospf` instead of `ip ospf`
- `vrf context` instead of `vrf definition`
- `mtu` instead of `ip mtu`
- `Ethernet1/1` port naming (module/port)

**Example Differences:**

```jinja2
! EOS
interface Ethernet1
  ip mtu 9000

! NXOS
interface Ethernet1/1
  mtu 9000
```

---

## Python Scripts

### `validate.py`

**Purpose:** Check network.yml for structural errors

**Runs:** `validate_network(network_file)`

**Checks:**
1. All device names referenced in links exist
2. No duplicate loopback IPs
3. No invalid ASNs
4. Link endpoints are valid
5. (Optional) Links are bidirectional

**Exit Codes:**
- `0` = Valid
- `1` = Errors found

**Usage:**
```bash
python validate.py
# OR
python validate.py network_instances/custom/network.yml
```

**Output:**
```
✅ Validation passed
# OR
❌ Validation failed:
  - Link L1: source spine-01 not found
  - Duplicate loopback IP: 10.0.1.1
```

**Extending:**

Add new validations:

```python
def validate_device_naming(net):
    """Check device names follow convention"""
    errors = []
    for device in net['devices']:
        if not device.startswith(net['design']['site_prefix']):
            errors.append(f"Device {device} doesn't match site prefix")
    return errors

# In main:
errors += validate_device_naming(net) or []
```

---

### `generate_ipam.py`

**Purpose:** Calculate IP allocations and build IPAM matrix

**Runs:** `generate_ipam(network_file)`

**Calculates:**
1. Loopback IPs from network.yml (already assigned)
2. Transit link IPs from subnet definitions (/31 per link)
3. BGP neighbor relationships (bidirectional)
4. VRF configurations

**Outputs:** `output/ipam.yml`

**IPAM Structure:**

```yaml
devices:
  device_name:
    role: string              # From network.yml
    asn: integer              # From network.yml
    loopback_ip: string       # From network.yml
    management_ip: string     # From network.yml
    platform: string          # From network.yml
    bgp_neighbors:            # CALCULATED
      - device: string        # Neighbor device name
        asn: integer          # Neighbor ASN
        ip: string            # Neighbor's IP on this link

links:
  link_name:
    source: string
    source_port: string
    source_ip: string         # CALCULATED
    target: string
    target_port: string
    target_ip: string         # CALCULATED
    subnet: string            # From network.yml

vrfs:
  # Copy from network.yml
```

**How IPs are Calculated:**

```python
# For each link with subnet 10.0.0.0/31
subnet = ipaddress.ip_network("10.0.0.0/31")
ips = list(subnet.hosts())  # [10.0.0.0, 10.0.0.1]

link['source_ip'] = str(ips[0])  # 10.0.0.0
link['target_ip'] = str(ips[1])  # 10.0.0.1
```

**Extending:**

Add static routes:

```python
# In generate_ipam()
ipam['static_routes'] = []
for device in net['devices']:
    if device['role'] == 'leaf':
        ipam['static_routes'].append({
            'device': device_name,
            'destination': '192.168.1.0/24',
            'next_hop': '10.0.1.1'  # Spine loopback
        })
```

---

### `render_config.py`

**Purpose:** Generate device configurations from IPAM + templates

**Runs:** `render_configs(network_file, ipam)`

**Process:**
1. Load network.yml
2. Load IPAM from previous step
3. For each device:
   - Determine platform (EOS, NXOS)
   - Select corresponding template
   - Build context (device data + links + VRFs)
   - Render template with context
   - Write to output/configs/

**Context Variables:**

```python
context = {
    'device': 'spine-01',
    'config': {
        'role': 'spine',
        'asn': 65000,
        'loopback_ip': '10.0.1.1',
        'bgp_neighbors': [...]
    },
    'links': {
        'L1': {
            'port': 'Ethernet1',
            'ip': '10.0.0.0',
            'neighbor': 'leaf-01',
            'neighbor_ip': '10.0.0.1'
        }
    },
    'vrfs': {
        'blue': {'rd': '65000:1', ...},
        'red': {'rd': '65000:2', ...}
    }
}
```

**Link Direction Handling:**

For each link in IPAM:
- If device is SOURCE: use source_port, source_ip
- If device is TARGET: use target_port, target_ip

Example:

```python
# Link L1: spine-01 (source) → leaf-01 (target)
# When rendering spine-01: uses source_port (Eth1), source_ip (10.0.0.0)
# When rendering leaf-01: uses target_port (Eth1/1), target_ip (10.0.0.1)
```

**Output:**
```
output/configs/spine-01.conf
output/configs/spine-02.conf
output/configs/leaf-01.conf
output/configs/leaf-02.conf
```

**Extending:**

Support new platform:

```python
# In render_configs()
if 'juniper' in platform:
    template = env.get_template('junos_device.j2')
elif 'dell' in platform:
    template = env.get_template('dell_os10.j2')
```

Add pre-deployment validation:

```python
rendered = template.render(context)

# Validate syntax
if validate_syntax(rendered, platform):
    write to file
else:
    print error, skip
```

---

### `generate_cutsheet.py`

**Purpose:** Extract physical link topology for racking team

**Runs:** `generate_cutsheet(network_file)`

**Extracts:** All links from network.yml, outputs as CSV

**CSV Format:**

```csv
src_device,src_port,target_device,target_port
spine-01,Ethernet1,leaf-01,Ethernet1/1
```

**Output:** `output/cutsheet.csv`

**Columns:**
- `src_device`: Source device name
- `src_port`: Source interface name
- `target_device`: Target device name
- `target_port`: Target interface name

**Use Cases:**
1. Racking team uses to physically cable devices
2. Procurement uses to order correct cable types
3. Validation against physical wiring

**Extending:**

Add bandwidth/cable type:

```python
writer.writerow([
    link['source'],
    link['source_port'],
    link['target'],
    link['target_port'],
    link.get('bandwidth', '100G'),  # Add bandwidth
    get_cable_type(link['bandwidth'])  # Add cable type
])
```

---

## Output Artifacts

### `output/ipam.yml`

**Purpose:** Auditable IP allocation matrix

**Use Cases:**
- Verify IP calculations
- Reference for network documentation
- Troubleshooting (check neighbor IPs)
- Compliance (IP audit trail)

**Structure:** Complete mapping of all IPs to devices/links

---

### `output/configs/`

**Files:**
- `spine-01.conf` (EOS)
- `spine-02.conf` (EOS)
- `leaf-01.conf` (NXOS)
- `leaf-02.conf` (NXOS)

**Purpose:** Ready-to-deploy device configurations

**Next Steps:**
1. Validate syntax (EOS/NXOS specific)
2. Run configs through pre-check tool
3. Deploy to lab first
4. Production deployment with change control

---

### `output/cutsheet.csv`

**Purpose:** Physical link mapping for racking team

**Use Cases:**
- Physically cable devices
- Order cables (length, type, quantity)
- Validation checklist
- Troubleshooting (verify cables match plan)

**Open in:** Excel, Google Sheets, or any CSV viewer

---

## File Relationships

```
network_types/spine_leaf_3tier.schema.yml
                    ↓
                    (validates)
                    ↓
network_instances/prototype_a/config.yml
                    ↓
                    (provides values)
                    ↓
network_instances/prototype_a/network_a.yml
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
    validate.py  generate_  render_
                  ipam.py    config.py
        ↓           ↓           ↓
        ✅         ipam.yml   configs/
                                ↓
                         cutsheet.py
                                ↓
                         cutsheet.csv
```

---

**Understanding these components enables:**
- Creating new network types
- Adding new instances
- Supporting new vendors
- Extending functionality
- Troubleshooting issues
