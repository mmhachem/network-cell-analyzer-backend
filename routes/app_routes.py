from flask import Blueprint, request, jsonify
from models import db, CellRecord
from datetime import datetime
from utils.auth_utils import verify_token

# ✅ Define the blueprint for Android App Routes
app_routes = Blueprint("app_routes", __name__)

# ✅ Submit network data (Android sends data every 10 seconds)
@app_routes.route('/submit_data', methods=['POST'])
def submit_data():
    user = verify_token()  # Ensure authenticated request
    
    data = request.json
    if not data or 'device_id' not in data:
        return jsonify({"error": "Invalid data or missing device_id"}), 400

    try:
        record = CellRecord(
            operator=data.get('operator'),
            signal_power=data.get('signal_power'),
            sinr=data.get('sinr'),
            network_type=data.get('network_type'),
            frequency_band=data.get('frequency_band'),
            cell_id=data.get('cell_id'),
            timestamp=datetime.strptime(data.get('timestamp'), "%d %b %Y %I:%M %p"),
            device_ip=request.remote_addr,
            device_mac=data.get('device_mac'),
            device_id=data.get('device_id'),
            username=user.username  # ✅ Store username in record
        )
        db.session.add(record)
        db.session.commit()
        return jsonify({"message": "✅ Data submitted successfully!"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ✅ Get average connectivity time per operator (by username & device_id)
@app_routes.route('/stats/operator', methods=['GET'])
def operator_stats():
    user = verify_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    device_id = request.args.get('device_id')

    if not start_date or not end_date or not device_id:
        return jsonify({"error": "Start date, end date, and device_id required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)
    
    records = CellRecord.query.filter(
        CellRecord.timestamp.between(start_dt, end_dt),
        CellRecord.device_id == device_id,
        CellRecord.username == user.username
    ).all()

    total = len(records)
    stats = {}
    for rec in records:
        stats[rec.operator] = stats.get(rec.operator, 0) + 1

    operators = ["Alfa", "Touch"]
    for op in operators:
        count = stats.get(op, 0)
        stats[op] = f"{(count / total) * 100:.2f}%" if total > 0 else "0.00%"

    return jsonify(stats)


# ✅ Get average connectivity time per network type (by username & device_id)
@app_routes.route('/stats/network_type', methods=['GET'])
def network_type_stats():
    user = verify_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    device_id = request.args.get('device_id')

    if not start_date or not end_date or not device_id:
        return jsonify({"error": "Start date, end date, and device_id required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(
        CellRecord.timestamp.between(start_dt, end_dt),
        CellRecord.device_id == device_id,
        CellRecord.username == user.username
    ).all()

    total = len(records)
    stats = {}
    for rec in records:
        stats[rec.network_type] = stats.get(rec.network_type, 0) + 1

    network_types = ["2G", "3G", "4G"]
    for nt in network_types:
        count = stats.get(nt, 0)
        stats[nt] = f"{(count / total) * 100:.2f}%" if total > 0 else "0.00%"

    return jsonify(stats)


# ✅ Get average signal power per network type (by username & device_id)
@app_routes.route('/stats/signal_power_per_network', methods=['GET'])
def signal_power_per_network():
    user = verify_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    device_id = request.args.get('device_id')

    if not start_date or not end_date or not device_id:
        return jsonify({"error": "Start date, end date, and device_id required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(
        CellRecord.timestamp.between(start_dt, end_dt),
        CellRecord.device_id == device_id,
        CellRecord.username == user.username
    ).all()

    stats = {}
    for rec in records:
        stats.setdefault(rec.network_type, []).append(rec.signal_power)

    network_types = ["2G", "3G", "4G"]
    avg_stats = {nt: (sum(stats[nt]) / len(stats[nt]) if nt in stats else 0.0) for nt in network_types}
    return jsonify(avg_stats)


# ✅ Get average signal power per device (by username & device_id)
@app_routes.route('/stats/signal_power_per_device', methods=['GET'])
def signal_power_per_device():
    user = verify_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    device_id = request.args.get('device_id')

    if not start_date or not end_date or not device_id:
        return jsonify({"error": "Start date, end date, and device_id required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(
        CellRecord.timestamp.between(start_dt, end_dt),
        CellRecord.device_id == device_id,
        CellRecord.username == user.username
    ).all()

    signal_powers = [rec.signal_power for rec in records]
    avg_power = sum(signal_powers) / len(signal_powers) if signal_powers else 0.0

    return jsonify({
        "device_id": device_id,
        "average_signal_power": avg_power
    })


# ✅ Get average SINR per network type (by username & device_id)
@app_routes.route('/stats/sinr_per_network', methods=['GET'])
def sinr_per_network():
    user = verify_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    device_id = request.args.get('device_id')

    if not start_date or not end_date or not device_id:
        return jsonify({"error": "Start date, end date, and device_id required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(
        CellRecord.timestamp.between(start_dt, end_dt),
        CellRecord.device_id == device_id,
        CellRecord.username == user.username
    ).all()

    stats = {}
    for rec in records:
        stats.setdefault(rec.network_type, []).append(rec.sinr)

    network_types = ["2G", "3G", "4G"]
    avg_stats = {nt: (sum(stats[nt]) / len(stats[nt]) if nt in stats else 0.0) for nt in network_types}
    return jsonify(avg_stats)
