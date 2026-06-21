#!/usr/bin/env python3
import yaml
import csv
import os

def generate_cutsheet(network_file):
    with open(network_file) as f:
        net = yaml.safe_load(f)
    
    os.makedirs('output', exist_ok=True)
    with open('output/cutsheet.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['src_device', 'src_port', 'target_device', 'target_port'])
        
        for link in net['links']:
            writer.writerow([
                link['source'],
                link['source_port'],
                link['target'],
                link['target_port']
            ])
    
    print("✅ Generated: output/cutsheet.csv")

if __name__ == '__main__':
    generate_cutsheet('network_instances/prototype_a/network_a.yml')
