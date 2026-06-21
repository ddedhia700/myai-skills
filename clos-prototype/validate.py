#!/usr/bin/env python3
import yaml
import sys

def validate_network(network_file):
    with open(network_file) as f:
        net = yaml.safe_load(f)
    
    errors = []
    devices = net['devices'].keys()
    
    # Check devices in links exist
    for link in net['links']:
        if link['source'] not in devices:
            errors.append(f"Link {link['name']}: source {link['source']} not found")
        if link['target'] not in devices:
            errors.append(f"Link {link['name']}: target {link['target']} not found")
    
    # Check bidirectional links
    for link in net['links']:
        reverse = next((l for l in net['links'] 
                       if l['source'] == link['target'] and 
                          l['target'] == link['source']), None)
        if not reverse:
            print(f"⚠️  Warning: Link {link['name']} has no reverse from {link['target']} to {link['source']}")
    
    # Check duplicate IPs
    ips = []
    for device, config in net['devices'].items():
        ip = config['loopback_ip']
        if ip in ips:
            errors.append(f"Duplicate loopback IP: {ip}")
        ips.append(ip)
    
    return errors if errors else None

if __name__ == '__main__':
    errors = validate_network('network_instances/prototype_a/network_a.yml')
    if errors:
        print("❌ Validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("✅ Validation passed")
        sys.exit(0)
