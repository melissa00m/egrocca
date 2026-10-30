# Shopping Droid – Node-RED Implementation

## 1. Overview
Node-RED is used to manage communication, sensor data storage, offline message handling, inventory and customer orders for the Shopping Droid project.

It works with an MQTT broker and an SQLite database.

## 2. Main Node-RED Flows

### 1. Telemetry Storage Flow
Receives sensor data through MQTT and stores the incoming telemetry information in the SQLite database.

### 2. Offline Queue
Stores incoming messages in the offline queue so that data is retained for later synchronization.

### 3. Retry Flow
Retrieves pending messages from the offline queue and attempts to resend them through HTTP requests. It updates the synchronization status depending on the receiver's response.

### 4. Shopping Droid Management
Manages the shopping system's supplier inventory and customer orders. It supports adding products, checking product availability, recording orders and updating stock quantities.

### 5. HTTP Test Receiver
Receives HTTP requests from the Retry Flow and returns a test response indicating whether the message was accepted.

## 3. Database

The system uses SQLite for data storage.

**Database file:** `database.db`

**Database schema:** `database_schema.sql`

The database contains the following tables:

- suppliers
- inventory
- customers
- orders
- order_items
- deliveries
- telemetry
- offline_queue
- system_logs

## 4. Software Requirements

- Node.js
- Node-RED
- Mosquitto MQTT Broker
- SQLite

## 5. Running the System

Start the MQTT broker:

```bash
sudo service mosquitto start
