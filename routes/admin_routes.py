from flask import Blueprint, request, jsonify
from models import db, CellRecord
from utils.auth_utils import verify_admin_token
from datetime import datetime, timedelta

# ✅ Define the blueprint for Admin Routes
admin_routes = Blueprint("admin_routes", __name__)

# ✅ Get operator usage summary (Admin - global)
@admin_routes.route('/admin/operator_summary', methods=['GET'])
def operator_summary():
    verify_admin_token()

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Start and end dates required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(CellRecord.timestamp.between(start_dt, end_dt)).all()
    total = len(records)
    stats = {}

    for rec in records:
        stats[rec.operator] = stats.get(rec.operator, 0) + 1

    operators = ["Alfa", "Touch"]
    for op in operators:
        count = stats.get(op, 0)
        stats[op] = f"{(count / total) * 100:.2f}%" if total > 0 else "0.00%"

    return jsonify(stats)

# ✅ Count of distinct connected devices (by unique device_id)
@admin_routes.route('/admin/connected_devices_count', methods=['GET'])
def connected_devices_count():
    verify_admin_token()
    count = db.session.query(CellRecord.device_id).distinct().count()
    return jsonify({"connected_devices": count})

# ✅ Previously connected devices — show username, device_id, IP, MAC
@admin_routes.route('/admin/previously_connected_devices', methods=['GET'])
def previously_connected_devices():
    verify_admin_token()
    devices = db.session.query(
        CellRecord.username,
        CellRecord.device_id,
        CellRecord.device_ip,
        CellRecord.device_mac
    ).distinct().all()

    return jsonify([
        {
            "username": d.username,
            "device_id": d.device_id,
            "ip": d.device_ip,
            "mac": d.device_mac
        } for d in devices
    ])

# ✅ Network type usage summary (global)
@admin_routes.route('/admin/network_type_summary', methods=['GET'])
def admin_network_type_summary():
    verify_admin_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Start and end dates required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(CellRecord.timestamp.between(start_dt, end_dt)).all()
    total = len(records)
    stats = {}

    for rec in records:
        stats[rec.network_type] = stats.get(rec.network_type, 0) + 1

    network_types = ["2G", "3G", "4G"]
    for nt in network_types:
        count = stats.get(nt, 0)
        stats[nt] = f"{(count / total) * 100:.2f}%" if total > 0 else "0.00%"

    return jsonify(stats)

# ✅ Average signal power summary (global)
@admin_routes.route('/admin/signal_power_summary', methods=['GET'])
def admin_signal_power_summary():
    verify_admin_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Start and end dates required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(CellRecord.timestamp.between(start_dt, end_dt)).all()
    stats = {}

    for rec in records:
        stats.setdefault(rec.network_type, []).append(rec.signal_power)

    network_types = ["2G", "3G", "4G"]
    avg_stats = {nt: (sum(stats[nt]) / len(stats[nt]) if nt in stats else 0.0) for nt in network_types}
    return jsonify(avg_stats)

# ✅ SINR summary (global)
@admin_routes.route('/admin/sinr_summary', methods=['GET'])
def admin_sinr_summary():
    verify_admin_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Start and end dates required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(CellRecord.timestamp.between(start_dt, end_dt)).all()
    stats = {}

    for rec in records:
        stats.setdefault(rec.network_type, []).append(rec.sinr)

    network_types = ["2G", "3G", "4G"]
    avg_stats = {nt: (sum(stats[nt]) / len(stats[nt]) if nt in stats else 0.0) for nt in network_types}
    return jsonify(avg_stats)

# ✅ Device activity trend (global)
@admin_routes.route('/admin/device_activity_trend', methods=['GET'])
def device_activity_trend():
    verify_admin_token()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date or not end_date:
        return jsonify({"error": "Start and end dates required"}), 400

    start_dt = datetime.fromisoformat(start_date)
    end_dt = datetime.fromisoformat(end_date)

    records = CellRecord.query.filter(CellRecord.timestamp.between(start_dt, end_dt)).all()
    trend = {}

    for rec in records:
        time_slot = rec.timestamp.strftime('%Y-%m-%d %H:00')
        trend[time_slot] = trend.get(time_slot, 0) + 1

    timestamps = sorted(trend.keys())
    counts = [trend[ts] for ts in timestamps]

    return jsonify({
        "timestamps": timestamps,
        "counts": counts
    })

# ✅ Device statistics by username & device_id
@admin_routes.route('/admin/device_statistics', methods=['GET'])
def device_statistics():
    verify_admin_token()
    username = request.args.get('username')
    device_id = request.args.get('device_id')

    if not username or not device_id:
        return jsonify({"error": "Username and Device ID are required"}), 400

    records = CellRecord.query.filter_by(username=username, device_id=device_id).all()
    if not records:
        return jsonify({"error": "No data found for this user/device"}), 404

    count = len(records)
    avg_signal_power = sum(r.signal_power for r in records) / count
    avg_sinr = sum(r.sinr for r in records) / count
    network_types = list(set(r.network_type for r in records))
    last_seen = max(r.timestamp for r in records)

    return jsonify({
        "username": username,
        "device_id": device_id,
        "records_count": count,
        "average_signal_power": avg_signal_power,
        "average_sinr": avg_sinr,
        "connected_network_types": network_types,
        "last_seen": last_seen.isoformat()
    })

# ✅ Currently connected devices (show username, device_id, IP, MAC)
@admin_routes.route('/admin/currently_connected_devices', methods=['GET'])
def currently_connected_devices():
    verify_admin_token()
    time_threshold = datetime.utcnow() - timedelta(minutes=5)

    devices = db.session.query(
        CellRecord.username,
        CellRecord.device_id,
        CellRecord.device_ip,
        CellRecord.device_mac
    ).filter(CellRecord.timestamp >= time_threshold).distinct().all()

    return jsonify([
        {
            "username": d.username,
            "device_id": d.device_id,
            "ip": d.device_ip,
            "mac": d.device_mac
        } for d in devices
    ])
