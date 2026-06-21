# Extension Guide

How to extend the prototype for new use cases.

---

## Adding a New Network Instance

### Scenario: Create a production network (4 spine, 8 leaf)

#### Step 1: Create Instance Folder

```bash
mkdir -p network_instances/production
```

#### Step 2: Create config.yml

```bash
cp network_instances/prototype_a/config.yml network_instances/production/config.yml
```

Edit `network_instances/production/config.yml`:

```yaml
network_type: "spine_leaf_3tier"
network_name: "production"

parameters:
  site_prefix: "prod"
  spine_count: 4              # Changed: 4 spines
  leaf_count: 8               # Changed: 8 leaves
  loopback_base: "10.0.1.0/22"  # Larger pool for 12 devices
  management_base: "192.168.1.0/24"
  transit_base: "10.0.0.0/22"   # Larger pool (4×8 + 6 = 38 links)
  routing_protocol: "bgp"
  underlay: "ospf"
  overlay: "vxlan"
  vrf_count: 2

vrfs:
  blue:
    rd: "65000:1"
    subnet: "10.0.10.0/21"     # Larger for more tenants
  red:
    rd: "65000:2"
    subnet: "10.0.20.0/21"
```

#### Step 3: Create network_prod.yml

Create `network_instances/production/network_prod.yml` with:
- 4 spine devices (spine-01 through spine-04)
- 8 leaf devices (leaf-01 through leaf-08)
- Full mesh links (4 × 8 = 32 spine-leaf links)
- Spine-to-spine redundancy (4-1=3 spine-spine links)
- Leaf-to-leaf redundancy (8-1=7 leaf-leaf links)
- **Total: 42 links**

```yaml
design:
  name: production
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
    management_ip: 192.168.1.50
    rr_server: true
  
  spine-02:
    # ... similar ...
    loopback_ip: 10.0.1.2
    rr_server: true
  
  # spine-03, spine-04 ...
  
  leaf-01:
    hostname: leaf-01
    platform: cisco_nxos
    role: leaf
    asn: 65001
    loopback_ip: 10.0.1.11
    management_ip: 192.168.1.60
    rr_client: true
  
  # leaf-02 through leaf-08 ...

links:
  # Spine-to-leaf (4 spines × 8 leaves = 32 links)
  - name: L1
    source: spine-01
    source_port: Ethernet1
    target: leaf-01
    target_port: Ethernet1/1
    subnet: 10.0.0.0/31
  
  # ... (L2-L32 for all spine-leaf combinations)
  
  # Spine-to-spine (full mesh of 4 spines = 3 additional links)
  - name: L33
    source: spine-01
    source_port: Ethernet49
    target: spine-02
    target_port: Ethernet49
    subnet: 10.0.0.64/31
  
  # ... (L34-L35 for spine-03, spine-04)
  
  # Leaf-to-leaf (chain: leaf-01↔leaf-02↔...↔leaf-08 = 7 links)
  - name: L36
    source: leaf-01
    source_port: Ethernet49
    target: leaf-02
    target_port: Ethernet49
    subnet: 10.0.0.72/31
  
  # ... (L37-L42 for remaining leaf pairs)

vrfs:
  blue:
    rd: "65000:1"
    subnet: "10.0.10.0/21"
  red:
    rd: "65000:2"
    subnet: "10.0.20.0/21"
```

#### Step 4: Update Script Paths

Edit `validate.py`, `generate_ipam.py`, `render_config.py`, `generate_cutsheet.py`:

Change:
```python
if __name__ == '__main__':
    generate_ipam('network_instances/prototype_a/network_a.yml')
```

To:
```python
if __name__ == '__main__':
    # For production
    generate_ipam('network_instances/production/network_prod.yml')
    # OR make it configurable:
    import sys
    network_file = sys.argv[1] if len(sys.argv) > 1 else 'network_instances/production/network_prod.yml'
    generate_ipam(network_file)
```

#### Step 5: Generate Configs

```bash
python validate.py
python generate_ipam.py
python render_config.py
python generate_cutsheet.py
```

**Result:**
- 4 spine configs + 8 leaf configs in output/configs/
- 42 links in cutsheet.csv
- Complete IPAM matrix in ipam.yml

---

## Adding a New Network Type

### Scenario: Collapsed Core Architecture (No spine tier)

#### Step 1: Create Schema

Create `network_types/collapsed_core.schema.yml`:

```yaml
network_type: "collapsed_core"
description: "Collapsed core (core + access, no spine tier)"

parameters:
  site_prefix:
    type: string
    description: "Site identifier"
  
  core_count:
    type: integer
    min: 2
    max: 4
    description: "Core switches (replaces spine)"
  
  access_count:
    type: integer
    min: 2
    max: 100
    description: "Access switches (replaces leaf)"
  
  loopback_base:
    type: cidr
  
  management_base:
    type: cidr
  
  core_links_base:
    type: cidr
    description: "Core-to-core links"
  
  access_links_base:
    type: cidr
    description: "Core-to-access links"
```

#### Step 2: Create Instance

Create `network_instances/campus/config.yml`:

```yaml
network_type: "collapsed_core"
network_name: "campus"

parameters:
  site_prefix: "campus"
  core_count: 2
  access_count: 12
  loopback_base: "10.0.2.0/24"
  management_base: "192.168.2.0/24"
  core_links_base: "10.1.0.0/24"
  access_links_base: "10.1.1.0/21"
```

#### Step 3: Create Network Definition

Create `network_instances/campus/network_campus.yml`:

```yaml
design:
  name: campus
  architecture: collapsed_core
  routing_protocol: bgp

devices:
  core-01:
    hostname: core-01
    platform: arista_eos
    role: core
    asn: 65100
    loopback_ip: 10.0.2.1
  
  core-02:
    hostname: core-02
    platform: arista_eos
    role: core
    asn: 65101
    loopback_ip: 10.0.2.2
  
  access-01:
    hostname: access-01
    platform: arista_eos
    role: access
    asn: 65200
    loopback_ip: 10.0.2.10
  
  # ... access-02 through access-12 ...

links:
  # Core-to-core full mesh
  - name: L1
    source: core-01
    source_port: Ethernet49
    target: core-02
    target_port: Ethernet49
    subnet: 10.1.0.0/31
  
  # Core-to-access (every access connects to both cores)
  - name: L2
    source: core-01
    source_port: Ethernet1
    target: access-01
    target_port: Ethernet49
    subnet: 10.1.1.0/31
  
  # ... (24 more core-to-access links) ...
```

#### Step 4: Generate

```bash
# Update script to use new path
python validate.py network_instances/campus/network_campus.yml
python generate_ipam.py network_instances/campus/network_campus.yml
python render_config.py network_instances/campus/network_campus.yml
```

---

## Adding Support for a New Vendor

### Scenario: Add Juniper Junos Support

#### Step 1: Create Junos Templates

Create `templates/junos_spine.j2`:

```jinja2
set system hostname {{ device }}
set system domain-name example.com
!
set routing-options router-id {{ config.loopback_ip }}
!
set protocols ospf area 0.0.0.0 interface all
!
set protocols bgp local-as {{ config.asn }}
set protocols bgp router-id {{ config.loopback_ip }}
{% if config.rr_server %}
set protocols bgp cluster {{ config.loopback_ip }}
{% endif %}
!
{% for neighbor in config.bgp_neighbors %}
set protocols bgp group leaves neighbor {{ neighbor.ip }} peer-as {{ neighbor.asn }}
{% endfor %}
!
{% for link_name, link in links.items() %}
set interfaces {{ link.port }} description "Link to {{ link.neighbor }}"
set interfaces {{ link.port }} unit 0 family inet address {{ link.ip }}/31
set interfaces {{ link.port }} mtu 9000
{% endfor %}
!
set interfaces lo0 unit 0 family inet address {{ config.loopback_ip }}/32
!
{% for vrf_name, vrf in vrfs.items() %}
set routing-instances {{ vrf_name }} routing-options autonomous-system {{ config.asn }}
{% endfor %}
```

Create `templates/junos_leaf.j2`:

```jinja2
# Similar to junos_spine.j2, but optimized for leaf role
```

#### Step 2: Update render_config.py

```python
# In render_configs()
def get_template(platform):
    if 'eos' in platform:
        return 'eos_spine.j2' or 'eos_leaf.j2'
    elif 'nxos' in platform:
        return 'nxos_spine.j2' or 'nxos_leaf.j2'
    elif 'junos' in platform:
        return 'junos_spine.j2' or 'junos_leaf.j2'
    else:
        raise ValueError(f"Unknown platform: {platform}")

platform = device_data['platform']
role = device_data['role']
template_name = f"{platform}_{role}.j2"
template = env.get_template(template_name)
```

#### Step 3: Add Junos Devices to Network

```yaml
devices:
  # ... existing devices ...
  
  spine-03:
    hostname: spine-03
    platform: juniper_junos  # NEW
    role: spine
    asn: 65000
    loopback_ip: 10.0.1.3
    rr_server: false
```

#### Step 4: Generate

```bash
python render_config.py
# Now produces:
# - output/configs/spine-01.conf (EOS)
# - output/configs/spine-02.conf (EOS)
# - output/configs/spine-03.conf (Junos)
# - output/configs/leaf-01.conf (NXOS)
```

---

## Adding Pre-Deployment Validation

### Scenario: Syntax Check Generated Configs

#### Step 1: Create Validator

Create `validate_configs.py`:

```python
#!/usr/bin/env python3
import os
import subprocess

def validate_eos_syntax(config_file):
    """Check EOS config syntax"""
    # Use eAPI or CloudVision to validate
    # OR use simple parser
    errors = []
    with open(config_file) as f:
        lines = f.readlines()
    
    for i, line in enumerate(lines, 1):
        if line.startswith('!'):
            continue
        if 'router bgp' in line and not line.strip().endswith('bgp'):
            errors.append(f"Line {i}: Malformed BGP statement")
    
    return errors

def validate_nxos_syntax(config_file):
    """Check NXOS config syntax"""
    # Similar to EOS
    pass

def validate_all_configs(config_dir='output/configs'):
    """Validate all generated configs"""
    errors = {}
    
    for config_file in os.listdir(config_dir):
        if not config_file.endswith('.conf'):
            continue
        
        path = os.path.join(config_dir, config_file)
        
        # Determine platform from filename or content
        if 'spine' in config_file or 'spine' in open(path).read():
            # Infer EOS for spines
            file_errors = validate_eos_syntax(path)
        else:
            file_errors = validate_nxos_syntax(path)
        
        if file_errors:
            errors[config_file] = file_errors
    
    return errors

if __name__ == '__main__':
    errors = validate_all_configs()
    
    if errors:
        print("❌ Config validation failed:")
        for config, err_list in errors.items():
            print(f"  {config}:")
            for err in err_list:
                print(f"    - {err}")
    else:
        print("✅ All configs validated successfully")
```

#### Step 2: Integrate into Pipeline

```bash
# Updated pipeline
python validate.py && \
python generate_ipam.py && \
python render_config.py && \
python validate_configs.py && \
python generate_cutsheet.py
```

---

## Adding Multi-Instance Runner

### Scenario: Generate All Networks at Once

Create `generate_all.py`:

```python
#!/usr/bin/env python3
import os
import subprocess

INSTANCES = [
    ('prototype_a', 'network_instances/prototype_a/network_a.yml'),
    ('production', 'network_instances/production/network_prod.yml'),
    ('campus', 'network_instances/campus/network_campus.yml'),
]

def generate_instance(name, network_file):
    """Generate all outputs for one instance"""
    
    print(f"\n{'='*50}")
    print(f"Generating: {name}")
    print(f"{'='*50}")
    
    cmd = [
        'python', 'validate.py',
        'python', 'generate_ipam.py',
        'python', 'render_config.py',
        'python', 'generate_cutsheet.py'
    ]
    
    # TODO: Update scripts to accept network file as argument
    # For now, update paths manually
    
    subprocess.run(f"python validate.py {network_file}", shell=True)
    subprocess.run(f"python generate_ipam.py {network_file}", shell=True)
    subprocess.run(f"python render_config.py {network_file}", shell=True)
    subprocess.run(f"python generate_cutsheet.py {network_file}", shell=True)

if __name__ == '__main__':
    for name, network_file in INSTANCES:
        generate_instance(name, network_file)
    
    print("\n✅ All instances generated")
```

Run:
```bash
python generate_all.py
```

---

## Making Scripts Parameterized

### Update Scripts to Accept Command-Line Arguments

#### Update validate.py

```python
if __name__ == '__main__':
    import sys
    network_file = sys.argv[1] if len(sys.argv) > 1 else 'network_instances/prototype_a/network_a.yml'
    errors = validate_network(network_file)
    # ...
```

Usage:
```bash
python validate.py network_instances/production/network_prod.yml
```

#### Same for generate_ipam.py, render_config.py, generate_cutsheet.py

Result: **One codebase, unlimited instances**

---

## Summary of Extension Points

| Extension | Effort | Files to Create/Modify |
|-----------|--------|------------------------|
| New instance (same type) | 1 hour | config.yml + network.yml |
| New network type | 4 hours | schema.yml + networks + templates |
| New vendor | 2-3 days | 2-4 templates + render_config.py |
| New features (VLANs, etc.) | 1-2 days | templates + generate_ipam.py |
| Pre-deployment validation | 1 day | validate_configs.py + pipeline |
| Multi-instance runner | 2 hours | generate_all.py |

**All extensions maintain backward compatibility with existing instances.**
