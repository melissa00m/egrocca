#!/usr/bin/env bash
# ==============================================================================
# Rural Delivery Droid Fleet - Automated TLS/SSL Certificate Generator
# Generates:
#   1. Fleet Root CA (Certificate Authority)
#   2. MQTT Broker Server Certificate (with SAN - Subject Alternative Names)
#   3. Droid Client Certificate (mTLS Authentication)
#   4. Node-RED Dispatch Client Certificate
# ==============================================================================

set -euo pipefail

OUT_DIR="./certs"
DAYS_VALID=1825 # 5 Years
CONFIG_FILE="openssl.cnf"

echo "=== [1/5] Initializing Certificate Directory ==="
mkdir -p "${OUT_DIR}"
touch "${OUT_DIR}/index.txt"
[ ! -f "${OUT_DIR}/serial" ] && echo 1000 > "${OUT_DIR}/serial"

cd "${OUT_DIR}"

echo "=== [2/5] Generating Root CA (Fleet Master Authority) ==="
# Generate private key for CA (4096-bit RSA)
openssl genrsa -out ca.key 4096
chmod 400 ca.key

# Generate self-signed Root CA certificate
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt \
    -config "../${CONFIG_FILE}" -extensions v3_ca \
    -subj "/C=US/ST=Rural/L=Hub/O=Rural Droid Logistics/OU=Security/CN=Rural-Delivery-Fleet-CA"

echo "Root CA generated: ${OUT_DIR}/ca.crt"

echo "=== [3/5] Generating MQTT Broker Server Certificate ==="
# Generate Broker Server Private Key
openssl genrsa -out server.key 2048
chmod 400 server.key

# Generate Broker CSR (Certificate Signing Request)
openssl req -new -key server.key -out server.csr \
    -subj "/C=US/ST=Rural/L=Hub/O=Rural Droid Logistics/OU=Broker/CN=mqtt.ruraldelivery.local"

# Sign Broker Certificate using Root CA with Server Extensions & SAN
openssl x509 -req -days ${DAYS_VALID} -in server.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out server.crt \
    -extfile "../${CONFIG_FILE}" -extensions server_cert

echo "Server Certificate generated: ${OUT_DIR}/server.crt"

echo "=== [4/5] Generating Droid Client Certificate (mTLS) ==="
# Generate Droid Client Key
openssl genrsa -out droid01.key 2048
chmod 400 droid01.key

# Generate Droid CSR
openssl req -new -key droid01.key -out droid01.csr \
    -subj "/C=US/ST=Rural/L=Hub/O=Rural Droid Logistics/OU=Droids/CN=droid-alpha-01"

# Sign Droid Client Certificate
openssl x509 -req -days ${DAYS_VALID} -in droid01.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out droid01.crt \
    -extfile "../${CONFIG_FILE}" -extensions client_cert

echo "Droid Client Certificate generated: ${OUT_DIR}/droid01.crt"

echo "=== [5/5] Generating Node-RED Dispatch Client Certificate ==="
# Generate Node-RED Client Key
openssl genrsa -out nodered.key 2048
chmod 400 nodered.key

# Generate Node-RED CSR
openssl req -new -key nodered.key -out nodered.csr \
    -subj "/C=US/ST=Rural/L=Hub/O=Rural Droid Logistics/OU=Dispatch/CN=nodered-central-dispatch"

# Sign Node-RED Client Certificate
openssl x509 -req -days ${DAYS_VALID} -in nodered.csr -CA ca.crt -CAkey ca.key \
    -CAcreateserial -out nodered.crt \
    -extfile "../${CONFIG_FILE}" -extensions client_cert

echo "Node-RED Client Certificate generated: ${OUT_DIR}/nodered.crt"

echo "=== Verification Check ==="
openssl verify -CAfile ca.crt server.crt
openssl verify -CAfile ca.crt droid01.crt
openssl verify -CAfile ca.crt nodered.crt

echo "================================================================="
echo "All certificates successfully generated in ${OUT_DIR}:"
echo "  - ca.crt, ca.key           : Fleet Root CA (Keep ca.key strictly secret!)"
echo "  - server.crt, server.key   : For Mosquitto MQTT Broker (port 8883)"
echo "  - droid01.crt, droid01.key : Installed on Delivery Droid companion computer"
echo "  - nodered.crt, nodered.key : Installed on Central Node-RED server"
echo "================================================================="

