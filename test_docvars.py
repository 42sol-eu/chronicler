#!/usr/bin/env python3

import zipfile
from xml.etree import ElementTree as ET

# Extract settings.xml directly
with zipfile.ZipFile('tests/STMA4000D0001__SW_QSP_B__2025-08-21.docx', 'r') as zip_ref:
    try:
        settings_xml = zip_ref.read('word/settings.xml').decode('utf-8')
        print('=== Found settings.xml ===')
        
        # Parse XML
        root = ET.fromstring(settings_xml)
        
        # Look for docVars in different ways
        print('\n=== Looking for docVars ===')
        
        # Method 1: Find all elements containing 'docVar'
        for elem in root.iter():
            if 'docVar' in elem.tag:
                print(f'Found docVar element: {elem.tag}')
                print(f'Attributes: {elem.attrib}')
        
        # Method 2: Find with namespace
        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        doc_vars = root.findall('.//w:docVar', namespaces)
        print(f'\nFound {len(doc_vars)} docVar elements with namespace')
        
        for doc_var in doc_vars:
            name = doc_var.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}name')
            val = doc_var.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
            print(f'{name}: {val}')
            
        # Method 3: Find without namespace
        doc_vars_no_ns = root.findall('.//docVar')
        print(f'\nFound {len(doc_vars_no_ns)} docVar elements without namespace')
        
        # Method 4: Let's look at the raw XML around docVars
        if 'docVar' in settings_xml:
            print('\n=== Raw XML containing docVar ===')
            lines = settings_xml.split('\n')
            for i, line in enumerate(lines):
                if 'docVar' in line:
                    start = max(0, i-2)
                    end = min(len(lines), i+3)
                    for j in range(start, end):
                        marker = '>>> ' if j == i else '    '
                        print(f'{marker}{lines[j]}')
                    print()
        
    except KeyError:
        print('settings.xml not found in the zip file')
