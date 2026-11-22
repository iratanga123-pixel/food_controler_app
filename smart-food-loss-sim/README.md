# Smart Food Loss Prevention: AI + IoT (simulation version)

This project reduces post-harvest grain losses in Rwanda. Sensors in a storage site measure
temperature, humidity and grain moisture, an AI model predicts spoilage risk for the next
72 hours, and the storage manager gets an SMS before the grain is damaged.

**No hardware is needed.** Every part of the system is simulated:

| Real system | Simulation in this project | File |
|---|---|---|
| Sensors in the store (ESP32, DHT22, moisture probe) | Wokwi online ESP32 simulator | `wokwi/` |
| Many sensor nodes sending data every hour | Virtual sensor nodes (Python) | `simulator.py` |
| Cloud database | SQLite database | `data/readings.db` |
| Field data to train the AI | Thousands of simulated storage situations | `make_dataset.py` |
| AI spoilage prediction | Random Forest model (scikit-learn) | `train_model.py`, `predictor.py` |
| SMS to the storage manager | SMS log file, or the free Africa's Talking sandbox | `alerts.py` |
| Web dashboard | Streamlit dashboard | `dashboard.py` |

---

## Step 1: Install the tools (once)

1. Install Python 3.10 or newer from python.org (tick "Add Python to PATH").
2. Open PowerShell in this folder and install the libraries:

```powershell
python -m pip install -r requirements.txt
```

## Step 2: Simulate the sensor hardware in Wokwi

This shows how the real sensor node works, without buying parts.

1. Go to https://wokwi.com and create a free account.
2. Start a new **ESP32** project.
3. Copy the contents of `wokwi/sketch.ino` into the `sketch.ino` tab.
4. Copy `wokwi/diagram.json` into the `diagram.json` tab.
5. Click the **Library Manager** and add: `DHT sensor library for ESPx`, `OneWire`, `DallasTemperature`.
6. Press the green **Play** button. The Serial Monitor prints a JSON reading every 5 seconds.
7. During the simulation, click the DHT22 to change temperature and humidity, and turn the
   potentiometer to change grain moisture. Watch `local_risk` change from `OK` to `WATCH` to `HIGH`.
8. Optional: create a free ThingSpeak channel with 4 fields, put its write key in
   `THINGSPEAK_KEY`, and watch your readings arrive on the internet.

If a wire is not connected after pasting the diagram, connect it by hand in the Wokwi editor:
DHT22 data → D15, DS18B20 data → D4, potentiometer middle pin → D34, and all VCC to 3V3, GND to GND.

Take screenshots of the circuit and the Serial Monitor for your report.

## Step 3: Create the training data

```powershell
python make_dataset.py --stores 800
```

This simulates 800 different storage situations (different crops, weather, rain, drying) and
saves 6,400 examples to `data/training_data.csv`. Each example has what the sensors saw in the
last 48 hours, and a label: the worst risk the grain really reached in the next 72 hours.

## Step 4: Train and test the AI model

```powershell
python train_model.py
```

You get accuracy, precision, recall, a confusion matrix, the most important inputs, and a
comparison with a simple rule that only looks at today's readings. Results from our test run:

| Method | Accuracy | Real problems caught (recall) |
|---|---|---|
| Rule on today's readings only | 61.5% | 67.8% |
| AI model (48 h of history) | 85.6% | 95.7% |

The AI catches more problems because it learns from trends, such as humidity that keeps rising.
Put these tables in your report.

## Step 5: Run the live system

Start the dashboard (opens in your browser at http://localhost:8501):

```powershell
python -m streamlit run dashboard.py
```

Then open **Simulation control** in the left menu and press **Start simulation**. The virtual sensors
open in their own window (1 simulated hour every 3 seconds). You can also start them by hand with
`python simulator.py --live --interval 3`.

On the home dashboard you see each store's status, charts with safe limits and AI probabilities.
At the bottom is the **AI prediction** for the selected store: Low / Medium / High risk, the risk percentage from the trained model,
what is causing the risk and what to do about it. Without a trained model it falls back to the
storage rule and shows no percentage. It refreshes every 5 seconds.

**Desktop notifications**: when the app opens, a card in the bottom-right corner asks
"Allow notifications?". Click **Allow**, then **Allow** again in the browser's own prompt. From then on, every
time a store's risk goes up (or comes back to Good) a pop-up appears on your computer, even when the browser
tab is in the background. This works on any page of the app at http://localhost:8501.
You can also turn them on later from the **⚙️ settings button** in the top bar (next to the ⋮ menu): it has
the language choice and a **Notifications** section with **Allow notifications** / **Send a test notification**. If you blocked
notifications by mistake, click the icon left of the address bar → Notifications → Allow, then reload.
On Windows, also check that notifications are turned on in Settings → System → Notifications.

## Step 6: Demonstrate scenarios (Simulation control page)

Open **Simulation control** from the dashboard's left menu. Pick a store, then use the three panels.
Keep the dashboard open in another tab to watch the AI prediction react.
Each time the risk goes up, an SMS is written to `data/sms_outbox.log`.

1. **Sensor simulation**: start or stop the simulation, set temperature, humidity and grain moisture,
   or reset them to the store's starting values.
2. **Simulation scenarios**: normal storage, high temperature, high humidity, high grain moisture,
   poor ventilation, sensor disconnection, power failure.
3. **Warehouse control**: see which machines are running (cooling fan, ventilation, dehumidifier, heater,
   humidifier) and why, reset the sensor connection, and record manual inspections (saved in `data/admin.db`).
   The machines are never switched by hand; see below.

Example for your report: choose **High temperature** and watch the cooling fan switch itself on when the
grain passes the crop's maximum temperature, then off again once it is back inside the limit.

### Crop limits and automatic control (Admin page)

- **Crop storage limits**: for every crop the Admin sets the lowest and highest grain temperature, air
  humidity and grain moisture. Readings outside them are flagged on the dashboards.
- **Automatic warehouse control** (always on, no manual mode): when a reading goes past the crop's limits
  the matching machine switches on by itself, and off again once the reading is safely back inside
  (5% humidity / 1 °C margin, so it does not flick on and off):
  - above the maximum temperature → cooling fan and ventilation
  - above the maximum humidity or grain moisture → dehumidifier and ventilation
  - below the minimum temperature → heater
  - below the minimum humidity or grain moisture → humidifier (ventilation and dehumidifier off)

  The Admin page lists these rules for every crop, and the Simulation control page shows each automatic
  action and why it happened. To change when the machines switch, change the crop's limits.

## Step 7 (optional): Real SMS with the Africa's Talking sandbox

1. Create a free account at https://africastalking.com and open the **sandbox** app.
2. Copy the sandbox API key.
3. Before starting the dashboard, run:

```powershell
$env:AT_USERNAME = "sandbox"
$env:AT_API_KEY = "paste-your-sandbox-key"
```

4. Open the sandbox **phone simulator** with one of the store phone numbers from `config.py`.
   Alerts appear there as real SMS messages.

## Step 8: Write your report

Suggested chapters:
1. Introduction: post-harvest losses in Rwanda and why storage monitoring matters.
2. System design: the architecture (sensor node → network → cloud → AI → SMS and dashboard).
3. Hardware design: the Wokwi circuit, sensor choice, and moisture calibration method.
4. Data and AI: how the data was simulated, the features, the Random Forest model, results.
5. Results: the comparison table, the confusion matrix, screenshots of the scenarios.
6. Limitations: the data is simulated, so the model must be retrained on real store data
   before use. The spoilage rules are simplified from grain storage literature.
7. Future work: build the real node, a pilot with a cooperative, and USSD support.

---

## How the simulation works

- `spoilage.py` plays the role of "reality". It uses a rule of thumb from grain storage
  research: safe storage time roughly halves for every 1% moisture above the crop's safe level,
  for every ~6 °C above 22 °C, and quickly once humidity passes about 70%.
- `simulator.py` models each store: daily temperature cycles, rain showers, grain slowly
  absorbing water from humid air, grain heating up when mould is active, and sensor noise.
- The AI never sees the true conditions, only the noisy sensor readings, like in reality.

## Files

```
config.py          crops, stores, phone numbers, file paths
spoilage.py        storage physics ("reality" of the simulation)
simulator.py       virtual sensor nodes
features.py        turns 48 h of readings into model inputs
make_dataset.py    creates training data
train_model.py     trains and evaluates the AI
predictor.py       runs the AI on live data (also works without the dashboard)
alerts.py          SMS messages (log file or Africa's Talking)
dashboard.py       Streamlit web dashboard
notify.py          desktop (browser) notifications for new alerts
pages/             Admin page and Simulation control page
sim_control.py     link between the Simulation control page and the running simulator
wokwi/             ESP32 firmware and circuit for the Wokwi simulator
data/              database, dataset, model and SMS log (created when you run the steps)
```
