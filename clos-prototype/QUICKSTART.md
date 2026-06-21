# Quick Start Guide

Get the prototype running in 5 minutes.

---

## Prerequisites

**System Requirements:**
- macOS / Linux / Windows (WSL)
- Python 3.8+
- Git
- ~100MB disk space

**Python Packages:**
```bash
pip install pyyaml jinja2
```

---

## Setup (First Time)

### **Step 1: Clone/Navigate to Project**

```bash
cd /Users/admin/2026_projects/myai-skills/clos-prototype
```

### **Step 2: Verify Structure**

```bash
ls -la
# Should show:
# network_types/        (template)
# network_instances/    (instances)
# templates/            (jinja2)
# output/               (generated)
# *.py                  (scripts)
```

### **Step 3: Test Python Environment**

```bash
python validate.py
# Should output: ✅ Validation passed
```

If error, install packages:
```bash
pip install pyyaml jinja2
```

---

## Basic Workflow

### **Run the Full Pipeline (One Command)**

```bash
python validate.py && \
python generate_ipam.py && \
python render_config.py && \
python generate_cutsheet.py
```

**Expected output:**
```
✅ Validation passed
✅ IPAM generated: output/ipam.yml
✅ Generated: output/configs/spine-01.conf
✅ Generated: output/configs/spine-02.conf
✅ Generated: output/configs/leaf-01.conf
✅ Generated: output/configs/leaf-02.conf
✅ Generated: output/cutsheet.csv
```

---

## Step-by-Step Breakdown

### **Step 1: Validate Network Definition**

```bash
python validate.py
```

**What it does:**
- Checks all devices exist
- Confirms no duplicate IPs
- Verifies link definitions

**Output:** ✅ or ❌ with error messages

**Purpose:** Catch errors early, before IP allocation

---

### **Step 2: Generate IP Allocation Matrix**

```bash
python generate_ipam.py
```

**What it does:**
- Calculates loopback IPs (/32)
- Allocates transit subnet IPs (/31 per link)
- Builds BGP neighbor lists
- Creates IPAM matrix

**Output:** `output/ipam.yml` (human-readable reference)

**Example:**
```yaml
devices:
  spine-01:
    loopback_ip: 10.0.1.1
    bgp_neighbors:
      - device: leaf-01, asn: 65001, ip: 10.0.0.1
      - device: leaf-02, asn: 65002, ip: 10.0.0.3
      
links:
  L1:
    source: spine-01, source_ip: 10.0.0.0
    target: leaf-01, target_ip: 10.0.0.1
```

---

### **Step 3: Render Device Configurations**

```bash
python render_config.py
```

**What it does:**
- Reads IPAM matrix
- Applies Jinja2 templates (EOS, NXOS)
- Generates device-ready configs

**Output:**
- `output/configs/spine-01.conf` (EOS)
- `output/configs/spine-02.conf` (EOS)
- `output/configs/leaf-01.conf` (NXOS)
- `output/configs/leaf-02.conf` (NXOS)

**Example generated config:**
```
hostname spine-01
!
router ospf 1
  router-id 10.0.1.1
!
router bgp 65000
  router-id 10.0.1.1
  neighbor 10.0.0.1 remote-as 65001
  neighbor 10.0.0.3 remote-as 65002
  !
  address-family ipv4 unicast
    neighbor 10.0.0.1 activate
    neighbor 10.0.0.3 activate
```

---

### **Step 4: Generate Physical Cutsheet**

```bash
python generate_cutsheet.py
```

**What it does:**
- Extracts link topology
- Creates CSV for racking team

**Output:** `output/cutsheet.csv`

```csv
src_device,src_port,target_device,target_port
spine-01,Ethernet1,leaf-01,Ethernet1/1
spine-01,Ethernet2,leaf-02,Ethernet1/1
spine-02,Ethernet1,leaf-01,Ethernet1/2
spine-02,Ethernet2,leaf-02,Ethernet1/2
spine-01,Ethernet3,spine-02,Ethernet3
leaf-01,Ethernet1/3,leaf-02,Ethernet1/3
```

---

## Viewing Results

### **View Generated Config for One Device**

```bash
cat output/configs/spine-01.conf
```

### **View Complete IPAM Matrix**

```bash
cat output/ipam.yml
```

### **View Cutsheet (CSV)**

```bash
cat output/cutsheet.csv
```

### **Import Cutsheet to Excel/Sheets**

```bash
# Copy cutsheet to clipboard (macOS)
cat output/cutsheet.csv | pbcopy

# Then paste into Excel/Google Sheets
```

---

## Modifying the Network

### **Scenario: Add a Third Leaf**

**File:** `network_instances/prototype_a/network_a.yml`

**Change:**
```yaml
devices:
  spine-01: ...
  spine-02: ...
  leaf-01: ...
  leaf-02: ...
  leaf-03:           # NEW
    hostname: leaf-03
    platform: cisco_nxos
    role: leaf
    asn: 65003
    loopback_ip: 10.0.1.5
    management_ip: 192.168.1.22
    rr_client: true
```

**Add links:**
```yaml
links:
  # ... existing links ...
  
  - name: L7      # NEW
    source: spine-01
    source_port: Ethernet4
    target: leaf-03
    target_port: Ethernet1/1
    subnet: 10.0.0.12/31
  
  - name: L8      # NEW
    source: spine-02
    source_port: Ethernet3
    target: leaf-03
    target_port: Ethernet1/2
    subnet: 10.0.0.14/31
```

**Run pipeline:**
```bash
python validate.py && python generate_ipam.py && python render_config.py
```

**Result:** 
- `output/configs/leaf-03.conf` generated
- spine configs updated with new leaf neighbor
- Cutsheet updated with new links

---

## Troubleshooting

### **Error: "Device not found in links"**

```
❌ Link L1: source spine-01 not found
```

**Fix:** Check spelling in devices section matches links section

```yaml
devices:
  spine-01: ...  # ← spelling

links:
  - source: spine-01  # ← must match exactly (case-sensitive)
```

---

### **Error: "Duplicate IP"**

```
❌ Duplicate loopback IP: 10.0.1.1
```

**Fix:** Each device needs unique loopback

```yaml
devices:
  spine-01:
    loopback_ip: 10.0.1.1  ← Unique
  spine-02:
    loopback_ip: 10.0.1.2  ← Different
```

---

### **No configs generated**

**Check:**
1. `network_instances/prototype_a/network_a.yml` exists
2. IPAM script ran successfully (`output/ipam.yml` exists)
3. Templates exist (`templates/eos_spine.j2`, `templates/nxos_leaf.j2`)

```bash
ls output/ipam.yml                   # Should exist
ls templates/*.j2                    # Should show 2 files
ls output/configs/                   # Should have 4 .conf files
```

---

## Next Steps

1. **Modify network:** Edit `network_instances/prototype_a/network_a.yml`
2. **Add instance:** Create `network_instances/production/` folder
3. **New vendor:** Add `templates/junos_leaf.j2`
4. **Automate:** Run via cron/CI pipeline
5. **Test configs:** Add syntax validation before deploy

---

## Common Commands Cheat Sheet

```bash
# Full pipeline
python validate.py && python generate_ipam.py && python render_config.py && python generate_cutsheet.py

# Individual steps
python validate.py                    # Check for errors
python generate_ipam.py              # Calculate IPs
python render_config.py              # Generate configs
python generate_cutsheet.py          # Create cutsheet

# View results
cat output/configs/spine-01.conf     # View one config
cat output/ipam.yml                  # View IP allocation
cat output/cutsheet.csv              # View physical links

# Debug
head -20 output/configs/leaf-01.conf # First 20 lines
grep "router bgp" output/configs/*.conf  # Find BGP blocks

# Clean and regenerate
rm output/configs/* output/ipam.yml output/cutsheet.csv
python validate.py && python generate_ipam.py && python render_config.py && python generate_cutsheet.py
```

---

## Time Breakdown

| Step | Time | Notes |
|------|------|-------|
| validate.py | <0.1s | Checks structure only |
| generate_ipam.py | <0.1s | Subnet math |
| render_config.py | ~0.5s | Jinja2 templating |
| generate_cutsheet.py | <0.1s | CSV generation |
| **Total** | **~1 second** | For 4 devices |

Scale to 256 devices: ~5 seconds total

---

**Ready? Run the full pipeline:**

```bash
python validate.py && python generate_ipam.py && python render_config.py && python generate_cutsheet.py
```

Check outputs in `output/` folder.
