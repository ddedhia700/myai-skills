#!/usr/bin/env python3
import yaml
import ipaddress
import os

def generate_ipam(network_file):
    with open(network_file) as f:
        net = yaml.safe_load(f)
    
    ipam = {
        'devices': {},
        'links': {},
        'vrfs': net['vrfs']
    }
    
    # Loopback IPs (from network.yml)
    for device, config in net['devices'].items():
        ipam['devices'][device] = {
            'role': config['role'],
            'asn': config.get('asn'),
            'loopback_ip': config['loopback_ip'],
            'management_ip': config['management_ip'],
            'platform': config['platform'],
            'bgp_neighbors': []
        }
    
    # Link IPs from subnet /31
    for link in net['links']:
        subnet = ipaddress.ip_network(link['subnet'])
        ips = list(subnet.hosts())
        
        ipam['links'][link['name']] = {
            'source': link['source'],
            'source_port': link['source_port'],
            'source_ip': str(ips[0]),
            'target': link['target'],
            'target_port': link['target_port'],
            'target_ip': str(ips[1]),
            'subnet': link['subnet']
        }
    
    # Build BGP neighbor list (bidirectional)
    for link in net['links']:
        source_device = link['source']
        target_device = link['target']
        source_ip = str(list(ipaddress.ip_network(link['subnet']).hosts())[0])
        target_ip = str(list(ipaddress.ip_network(link['subnet']).hosts())[1])
        target_asn = net['devices'][target_device].get('asn')
        source_asn = net['devices'][source_device].get('asn')
        
        # Add neighbor from source perspective
        if target_asn:
            ipam['devices'][source_device]['bgp_neighbors'].append({
                'device': target_device,
                'asn': target_asn,
                'ip': target_ip
            })
        
        # Add neighbor from target perspective (reverse direction)
        if source_asn:
            ipam['devices'][target_device]['bgp_neighbors'].append({
                'device': source_device,
                'asn': source_asn,
                'ip': source_ip
            })
    
    # Add VRF interface assignments
    for device in ipam['devices']:
        if ipam['devices'][device]['role'] == 'leaf':
            ipam['devices'][device]['vrf_interfaces'] = {
                'blue': 'Vlan100',
                'red': 'Vlan200'
            }
    
    os.makedirs('output', exist_ok=True)
    with open('output/ipam.yml', 'w') as f:
        yaml.dump(ipam, f, default_flow_style=False)
    
    print("✅ IPAM generated: output/ipam.yml")
    return ipam

if __name__ == '__main__':
    generate_ipam('network_instances/prototype_a/network_a.yml')
