# PharmaChain – Cold Chain Monitoring

## Project Overview
PharmaChain monitors temperature and humidity during pharmaceutical storage and transportation.

**Member 3 contribution:** Sensor simulation, machine-learning anomaly detection, breach reporting, and blockchain log verification.

## Technologies Used
- Python
- NumPy
- Scikit-learn
- Isolation Forest
- Flask
- Web3.py
- Blockchain
- Keccak-256 hashing

## System Workflow
1. Sensor simulator generates temperature and humidity readings.
2. Isolation Forest detects unusual readings.
3. The system checks the safe temperature range of 2–8°C.
4. Three consecutive anomalies trigger a breach report.
5. The backend communicates with the smart contract.
6. Reading hashes are stored on the blockchain.
7. The verification script checks whether readings have been modified.

## Main Files

| File | Purpose |
|---|---|
| `simulator.py` | Runs sensor simulations |
| `train_model.py` | Trains the machine-learning model |
| `detector.py` | Detects anomalies |
| `verify_logs.py` | Verifies reading hashes |
| `mock_backend.py` | Local testing backend |
| `requirements.txt` | Python dependencies |

## Setup

Activate the virtual environment:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Train the model:

```bash
python train_model.py
```

## Demo Commands

Normal readings:

```bash
python simulator.py --backend http://127.0.0.1:5003 --batch batch_member3_test --scenario none --max-readings 25 --interval 1
```

Door-open scenario:

```bash
python simulator.py --backend http://127.0.0.1:5003 --batch batch_member3_door_open --scenario door_open --start-after 8 --interval 1 --max-readings 50
```

Verify logs:

```bash
python verify_logs.py --batch batch_member3_test
```

Test tampering:

```bash
python verify_logs.py --batch batch_member3_test --tamper
```

## Testing Results
Tests covered normal readings, door-open, power-failure, compressor-fault, temperature-spike, and tampering detection.

Normal and spike batches remained genuine. Door-open, power-failure, and compressor-fault batches were flagged as compromised.

## Important Notes
- Sensor readings are simulated, not collected from physical sensors.
- The blockchain stores hashes rather than complete raw readings.
- The Hardhat node and Member 2 backend must be running for integrated demonstrations.

## Member 3 Contribution
Developed sensor simulation, machine-learning anomaly detection, breach reporting, blockchain integration testing, and log verification.