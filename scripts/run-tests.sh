#!/bin/bash

# Exit on error
set -e

echo "Starting tests with coverage..."

# Start test services
docker-compose -f docker-compose.test.yml up -d

# Wait for services
sleep 20

# Run tests
cd server
pytest --cov=app --cov-report=html --cov-report=term --cov-report=xml tests/

# Check coverage
python -c "
import xml.etree.ElementTree as ET
tree = ET.parse('coverage.xml')
root = tree.getroot()
line_rate = float(root.attrib['line-rate'])
print(f'Coverage: {line_rate*100:.2f}%')
if line_rate < 0.90:
    print('ERROR: Coverage below 90%!')
    exit(1)
"

# Cleanup
cd ..
docker-compose -f docker-compose.test.yml down