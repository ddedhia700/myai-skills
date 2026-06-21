# CLOS Prototype - Network Automation Framework

## Directory Structure

```
clos-prototype/
│
├── network_types/                    # Network type TEMPLATES (reusable patterns)
│   └── spine_leaf_3tier.schema.yml   # Template: 3-tier CLOS fabric definition
│
├── network_instances/                # Network INSTANCES (deployed networks)
│   └── prototype_a/                  # Instance A: Prototype network
│       ├── config.yml                # Configuration values for this instance
│       └── network_a.yml             # GENERATED network definition
│
├── templates/                        # Jinja2 config templates
│   ├── eos_spine.j2                  # EOS Spine configuration template
│   └── nxos_leaf.j2                  # NXOS Leaf configuration template
│
├── output/                           # Generated outputs
│   ├── configs/                      # Device-ready configurations
│   │   ├── spine-01.conf
│   │   ├── spine-02.conf
│   │   ├── leaf-01.conf
│   │   └── leaf-02.conf
│   ├── ipam.yml                      # IP allocation matrix
│   └── cutsheet.csv                  # Physical racking topology
│
├── validate.py                       # Validate network.yml structure
├── generate_ipam.py                  # Calculate IP allocations
├── render_config.py                  # Render device configs from templates
├── generate_cutsheet.py              # Generate physical cutsheet
└── README.md                         # This file
```

---

## Usage

### **Workflow: Define → Generate → Deploy**

```bash
# 1. Create/edit instance configuration
vi network_instances/prototype_a/config.yml

# 2. Create/edit network definition
vi network_instances/prototype_a/network_a.yml

# 3. Validate structure
python validate.py

# 4. Generate IPAM matrix
python generate_ipam.py
# Output: output/ipam.yml

# 5. Render device configurations
python render_config.py
# Output: output/configs/spine-01.conf, etc.

# 6. Generate physical cutsheet
python generate_cutsheet.py
# Output: output/cutsheet.csv
```

---

## Creating New Network Instances

To add a new network (e.g., production DC):

```bash
# 1. Create new instance folder
mkdir -p network_instances/production

# 2. Copy and customize config
cp network_instances/prototype_a/config.yml network_instances/production/

# 3. Edit values
vi network_instances/production/config.yml

# 4. Create network definition
vi network_instances/production/network_prod.yml

# 5. Update Python scripts to reference new path:
# - Change 'prototype_a' → 'production' in validate.py, etc.
```

---

## File Descriptions

### **network_types/** - Reusable Templates
- `spine_leaf_3tier.schema.yml`: Defines the pattern for 3-tier CLOS fabrics
  - Parameters (scale, addressing, features)
  - Constraints (min/max device counts)
  - Link generation rules

### **network_instances/** - Deployed Networks
- `prototype_a/config.yml`: Values for prototype (site_prefix, counts, ASNs)
- `prototype_a/network_a.yml`: Complete network definition (devices, links, VRFs)

### **templates/** - Jinja2 Config Templates
- `eos_spine.j2`: Generates EOS Spine configurations
- `nxos_leaf.j2`: Generates NXOS Leaf configurations

### **output/** - Generated Artifacts
- `ipam.yml`: IP allocation matrix (loopbacks, transit subnets, neighbors)
- `configs/`: Device-ready configurations (ready to deploy to hardware)
- `cutsheet.csv`: Physical link topology for racking team

---

## Architecture

```
network_instances/prototype_a/
├── config.yml          (User-provided values)
└── network_a.yml       (Input to pipeline)
          ↓
    [validate.py]       ← Schema compliance check
          ↓
    [generate_ipam.py]  ← IPAM calculation
          ↓
    [render_config.py]  ← Config generation (via Jinja2)
          ↓
    output/
    ├── ipam.yml
    ├── configs/
    └── cutsheet.csv
```

---

## Scaling to Multiple Networks

Add new instances by creating parallel folders:

```
network_instances/
├── prototype_a/    ← Current
├── production/     ← New
├── campus_east/    ← New
└── wAn_hub/        ← New
```

Each instance:
- Has its own config.yml
- Generates its own network definition
- Produces its own device configs

---

## Next Steps

1. **Parameterize:** Convert network_a.yml to use config.yml values
2. **Multi-vendor:** Add Cisco IOS-XE template
3. **Testing:** Add config syntax validation
4. **Documentation:** Auto-generate design documents
5. **CI/CD:** Integrate into deployment pipeline
