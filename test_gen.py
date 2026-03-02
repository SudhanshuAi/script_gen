import json
import yaml
from pprint import pprint
from backend.generator import DataGenerator

yaml_schema = '''
project: supply_chain_data_generator
version: '1.0.0'
temporal:
  start_date: '2023-01-01'
  end_date: '2024-12-31'
global_messiness:
  null_pct: 0.0
database:
  entities:
    - name: warehouses
      row_count: 5
      columns:
        - name: warehouse_id
          type: uuid
          primary_key: true
        - name: created_at
          type: timestamp
          temporal: true
api_dumps:
  - name: warehouse_api
    output_dir: api
    total_records: 5
    page_size: 5
    filename_pattern: 'page_{page}.json'
    columns:
      - name: warehouse_id
        type: uuid
      - name: created_at
        type: timestamp
        temporal: true
'''
schema = yaml.safe_load(yaml_schema)
gen = DataGenerator(schema, output_dir='backend/test_out_normal')
res = gen.run()

import os
print('---- NORMAL GENERATION (TODAY 2026-03-02) ----')
with open('backend/test_out_normal/api/page_1.json') as f:
    data = json.load(f)
    print(f"Total Pages: {data.get('total_pages')}, Total Records: {data.get('total_records')}")
    for row in data['data']:
        print(row['created_at'])

# Now incremental daily for next 3 days
print('\n---- DAILY GENERATION (03, 04, 05) ----')
gen = DataGenerator(schema, output_dir='backend/test_out_normal', generate_days=3, rows_per_day=3)
res = gen.run()

for pg in ['1', '2', '3']:
    try:
        with open(f'backend/test_out_normal/api/page_{pg}.json') as f:
            data = json.load(f)
            print(f"File page_{pg}.json -> Total Pages: {data.get('total_pages')}, Total Records: {data.get('total_records')}")
            for row in data['data']:
                print(row['created_at'])
    except Exception as e:
        print(e)
