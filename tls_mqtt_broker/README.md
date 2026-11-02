# TLS/SSL MQTT Telemetry Encryption for Rural Delivery Droid Fleet

This module provides end-to-end Transport Layer Security (TLS v1.3/v1.2) with **Mutual Authentication (mTLS)** for the delivery droid telemetry and command channel.

---

## 1. Why TLS/SSL is Essential for Rural Delivery Droids

In rural parcel delivery operations, droids operate across long distances (5–30+ km) traversing isolated roads, farms, and hills, communicating with a central Node-RED fleet operations hub over public cellular (4G/LTE/GSM) or satellite links.

Without TLS/SSL:
1. **Payload Sniffing:** Attackers can intercept real-time GPS coordinates, order values, customer names, delivery addresses, and medical supply manifests.
2. **Man-in-the-Middle (MitM) Attacks:** An adversary on the local GSM network or rogue Wi-Fi hotspot could spoof the broker, injecting fake route waypoints or unauthorized remote unlock commands.
3. **Impersonation & Rogue Droids:** With standard username/password, compromised credentials allow unauthorized hardware to connect. With **mTLS (Mutual TLS)**, the broker strictly checks that the droid possesses an authentic private key signed by your private Fleet CA.

---

## 2. Certificate Architecture & Public Key Infrastructure (PKI)

```
                       ┌────────────────────────┐
                       │  Fleet Master Root CA  │
                       │   (ca.crt / ca.key)    │
                       └───────────┬────────────┘
                                   │ signs
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│  Mosquitto MQTT  │      │ Delivery Droid   │      │ Node-RED Central │
│  Broker Server   │      │ Companion Client │      │ Dispatch Console │
│(server.crt/.key) │      │(droid01.crt/.key)│      │(nodered.crt/.key)│
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

| Entity | Public Certificate | Private Key | Purpose |
| :--- | :--- | :--- | :--- |
| **Root CA** | `ca.crt` | `ca.key` (Store securely offline) | Signs all fleet certificates. Installed as trusted root on broker, droids, and Node-RED. |
| **Broker Server** | `server.crt` | `server.key` | Authenticates Mosquitto server identity on port 8883. Contains SANs (`localhost`, IP, FQDN). |
| **Droid Client** | `droid01.crt` | `droid01.key` | Authenticates Droid Alpha-01 via mTLS. CN: `droid-alpha-01`. |
| **Node-RED Client** | `nodered.crt` | `nodered.key` | Authenticates Central Dispatch Console via mTLS. CN: `nodered-central-dispatch`. |

---

## 3. How to Generate or Regenerate Certificates

### On Windows (PowerShell):
```powershell
powershell -ExecutionPolicy Bypass -File .\tls_mqtt_broker\generate_certs.ps1 -BrokerHost "localhost" -BrokerIP "127.0.0.1"
```

### On Linux / Raspberry Pi / macOS (Bash + OpenSSL):
```bash
chmod +x ./tls_mqtt_broker/generate_certs.sh
./tls_mqtt_broker/generate_certs.sh
```

---

## 4. Configuring Mosquitto MQTT Broker

1. Copy `mosquitto.conf` to your Mosquitto configuration folder (e.g., `/etc/mosquitto/mosquitto.conf` or `C:\Program Files\mosquitto\mosquitto.conf`).
2. Copy `ca.crt`, `server.crt`, and `server.key` to the designated `certs/` folder.
3. Start or restart Mosquitto:
   ```bash
   # Linux / systemd
   sudo systemctl restart mosquitto

   # Windows
   net stop mosquitto && net start mosquitto
   ```
4. Verify port 8883 is listening:
   ```bash
   netstat -an | grep 8883
   ```

---

## 5. Testing the Encrypted Connection

Test publishing telemetry from the droid using `mosquitto_pub` with mTLS client certificates:
```bash
mosquitto_pub -h localhost -p 8883 \
  --cafile certs/ca.crt \
  --cert certs/droid01.crt \
  --key certs/droid01.key \
  -t "droid/droid-alpha-01/telemetry" \
  -m '{"droid_id":"droid-alpha-01","battery":{"soc_pct":92},"gps":{"lat":-29.8587,"lon":31.0218}}'
```

---

## 6. Importing the Flow into Node-RED

1. Open Node-RED (`http://localhost:1880`).
2. Click the Hamburger menu (top-right) -> **Import**.
3. Select **Upload file** and choose `node_red_tls_flow.json`, or copy-paste its JSON text.
4. Click **Import**.
5. The `tls-config` node and `mqtt-broker` node are pre-wired.
6. If running Node-RED in Docker or remote server:
   - Double-click `Rural Fleet Mosquitto (mTLS:8883)`.
   - Click the pencil next to `Droid Fleet mTLS Security Profile`.
   - Ensure the server name matches your broker's domain/IP, or upload the `ca.crt`, `nodered.crt`, and `nodered.key` files.
7. Click **Deploy**. Telemetry messages are now fully encrypted over port 8883.

