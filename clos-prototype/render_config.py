#!/usr/bin/env python3
import yaml
import os
from jinja2 import Environment, FileSystemLoader

def render_configs(network_file, ipam):
    with open(network_file) as f:
        net = yaml.safe_load(f)
    
    env = Environment(loader=FileSystemLoader('templates'))
    
    for device_name, device_data in ipam['devices'].items():
        platform = device_data['platform']
        
        if 'eos' in platform:
            template = env.get_template('eos_spine.j2')
        else:
            template = env.get_template('nxos_leaf.j2')
        
        # Build bidirectional link context
        device_links = {}
        for link_name, link_data in ipam['links'].items():
            if link_data['source'] == device_name:
                # This device is source
                device_links[link_name] = {
                    'direction': 'source',
                    'port': link_data['source_port'],
                    'ip': link_data['source_ip'],
                    'neighbor': link_data['target'],
                    'neighbor_ip': link_data['target_ip'],
                    'neighbor_port': link_data['target_port'],
                    'subnet': link_data['subnet']
                }
            elif link_data['target'] == device_name:
                # This device is target
                device_links[link_name] = {
                    'direction': 'target',
                    'port': link_data['target_port'],
                    'ip': link_data['target_ip'],
                    'neighbor': link_data['source'],
                    'neighbor_ip': link_data['source_ip'],
                    'neighbor_port': link_data['source_port'],
                    'subnet': link_data['subnet']
                }
        
        context = {
            'device': device_name,
            'config': device_data,
            'links': device_links,
            'vrfs': ipam['vrfs']
        }
        
        rendered = template.render(context)
        
        os.makedirs('output/configs', exist_ok=True)
        with open(f'output/configs/{device_name}.conf', 'w') as f:
            f.write(rendered)
        
        print(f"✅ Generated: output/configs/{device_name}.conf")

if __name__ == '__main__':
    import generate_ipam
    ipam = generate_ipam.generate_ipam('network_instances/prototype_a/network_a.yml')
    render_configs('network_instances/prototype_a/network_a.yml', ipam)
