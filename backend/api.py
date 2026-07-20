"""
SupplySense Backend API Server

Exposes endpoints for the React dashboard to interact with the agent layer.
Includes management endpoints for inventory, suppliers, and action history.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

# Import agent and data components
try:
    from agents.orchestrator import create_agent
    from agents.sweep import run_intelligence_sweep
    import data.queries as queries
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from agents.orchestrator import create_agent
    from agents.sweep import run_intelligence_sweep
    import data.queries as queries

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Initialize Agent
try:
    agent = create_agent(None)
    logger.info(f"Agent initialized with tools: {agent.get_available_tools()}")
except Exception as e:
    logger.error(f"Failed to initialize agent: {e}")
    agent = None

print("[OK] Flask app initialized successfully")


# ============================================================================
# HEALTH
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "message": "SupplySense Backend API is running",
        "agent_ready": agent is not None
    })

@app.route('/api/test', methods=['GET'])
def test():
    return jsonify({"message": "[OK] API is working!", "timestamp": datetime.now().isoformat()})


# ============================================================================
# DASHBOARD PANEL DATA ENDPOINTS
# ============================================================================

@app.route('/api/shipment-delays', methods=['GET'])
def shipment_delays():
    """Get all active delayed shipments with delay_days and severity."""
    try:
        return jsonify(queries.get_delayed_shipments())
    except Exception as e:
        logger.error(f"Failed to fetch shipment delays: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/warehouse-utilization', methods=['GET'])
def warehouse_utilization():
    """Get capacity vs stock for all warehouses."""
    try:
        return jsonify(queries.get_warehouse_utilization())
    except Exception as e:
        logger.error(f"Failed to fetch warehouse utilization: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/demand-forecast', methods=['GET'])
def demand_forecast():
    """Get 7-day demand forecast for the top 5 highest-risk SKUs."""
    try:
        top_n = int(request.args.get('top_n', 5))
        return jsonify(queries.get_demand_forecast_for_risky_skus(top_n=top_n))
    except Exception as e:
        logger.error(f"Failed to fetch demand forecast: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# AGENT ENDPOINTS
# ============================================================================

@app.route('/api/sweep', methods=['GET'])
def run_sweep():
    """Run full intelligence sweep and return dashboard data."""
    if not agent:
        return jsonify({"error": "Agent not initialized"}), 500
    try:
        data_store = type('DataStore', (), {})()
        data_store.get_warehouse_ids = queries.get_all_warehouse_ids
        data_store.get_all_skus = queries.get_all_sku_ids
        data_store.get_all_suppliers = queries.get_all_supplier_ids
        data_store.get_current_stock = queries.get_current_stock
        data_store.get_delivery_history = queries.get_supplier_delivery_history
        data_store.save_pending_action = queries.save_pending_action

        def mock_get_forecast(sku_id):
            return {"sku_id": sku_id, "avg_forecasted_demand": 100.0, "trend": "stable", "confidence": 0.85}
        data_store.get_forecast = mock_get_forecast

        all_skus = queries.get_all_sku_ids()
        all_suppliers = queries.get_all_supplier_ids()

        result = run_intelligence_sweep(
            agent=agent,
            tool_functions=agent.tool_functions,
            all_skus=all_skus,
            all_suppliers=all_suppliers,
            data_store=data_store
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Sweep failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/query', methods=['POST'])
def query_agent():
    """Handle natural language supply chain questions."""
    if not agent:
        return jsonify({"error": "Agent not initialized"}), 500
    data = request.json
    question = data.get('question')
    if not question:
        return jsonify({"error": "No question provided"}), 400
    try:
        result = agent.answer_query(question)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# PENDING ACTIONS & ACTION HISTORY
# ============================================================================

@app.route('/api/pending-actions', methods=['GET'])
def pending_actions():
    """Get all pending actions awaiting approval."""
    try:
        actions = queries.get_pending_actions("pending_approval")
        return jsonify(actions)
    except Exception as e:
        logger.error(f"Failed to fetch pending actions: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/pending-actions/<action_id>/status', methods=['POST'])
def update_action_status(action_id):
    """Update the status of a pending action."""
    data = request.json
    status = data.get('status')
    if not status:
        return jsonify({"error": "No status provided"}), 400
    try:
        success = queries.update_action_status(action_id, status)
        if success:
            return jsonify({"message": "Status updated", "action_id": action_id, "status": status})
        return jsonify({"error": "Action not found or update failed"}), 404
    except Exception as e:
        logger.error(f"Failed to update action status: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/actions/history', methods=['GET'])
def action_history():
    """Get all actions (all statuses), newest first."""
    try:
        actions = queries.get_all_actions()
        return jsonify(actions)
    except Exception as e:
        logger.error(f"Failed to fetch action history: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# INVENTORY MANAGEMENT
# ============================================================================

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get all SKUs with total stock across warehouses."""
    try:
        return jsonify(queries.get_all_skus_with_stock())
    except Exception as e:
        logger.error(f"Failed to fetch inventory: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/inventory', methods=['POST'])
def create_sku():
    """Add a new SKU."""
    data = request.json
    sku_id = data.get('sku_id', '').strip()
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    if not sku_id or not name:
        return jsonify({"error": "sku_id and name are required"}), 400
    try:
        success = queries.add_sku(sku_id, name, category)
        if success:
            return jsonify({"message": "SKU created", "sku_id": sku_id}), 201
        return jsonify({"error": f"SKU {sku_id} already exists"}), 409
    except Exception as e:
        logger.error(f"Failed to create SKU: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/inventory/<sku_id>', methods=['PUT'])
def update_sku(sku_id):
    """Update SKU metadata."""
    data = request.json
    try:
        # Update metadata
        meta_updated = queries.update_sku(
            sku_id,
            name=data.get('name'),
            category=data.get('category')
        )
        # Update stock if warehouse + stock provided
        stock_updated = False
        if data.get('warehouse_id') is not None and data.get('current_stock') is not None:
            stock_updated = queries.update_sku_stock(
                sku_id, data['warehouse_id'], int(data['current_stock'])
            )
        if meta_updated or stock_updated:
            return jsonify({"message": "SKU updated", "sku_id": sku_id})
        return jsonify({"error": "SKU not found or nothing to update"}), 404
    except Exception as e:
        logger.error(f"Failed to update SKU {sku_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/inventory/<sku_id>', methods=['DELETE'])
def remove_sku(sku_id):
    """Remove a SKU and all its inventory."""
    try:
        success = queries.delete_sku(sku_id)
        if success:
            return jsonify({"message": "SKU deleted", "sku_id": sku_id})
        return jsonify({"error": "SKU not found"}), 404
    except Exception as e:
        logger.error(f"Failed to delete SKU {sku_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# SUPPLIER MANAGEMENT
# ============================================================================

@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    """Get all suppliers with full detail."""
    try:
        return jsonify(queries.get_all_suppliers_detail())
    except Exception as e:
        logger.error(f"Failed to fetch suppliers: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/suppliers', methods=['POST'])
def create_supplier():
    """Add a new supplier."""
    data = request.json
    supplier_id = data.get('supplier_id', '').strip()
    name = data.get('name', '').strip()
    region = data.get('region', '').strip()
    if not supplier_id or not name:
        return jsonify({"error": "supplier_id and name are required"}), 400
    try:
        success = queries.add_supplier(
            supplier_id, name, region,
            avg_lead_time_days=float(data.get('avg_lead_time_days', 0)),
            on_time_delivery_pct=float(data.get('on_time_delivery_pct', 100)),
            quality_score=float(data.get('quality_score', 8.0))
        )
        if success:
            return jsonify({"message": "Supplier created", "supplier_id": supplier_id}), 201
        return jsonify({"error": f"Supplier {supplier_id} already exists"}), 409
    except Exception as e:
        logger.error(f"Failed to create supplier: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/suppliers/<supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Update supplier record."""
    data = request.json
    try:
        success = queries.update_supplier(
            supplier_id,
            name=data.get('name'),
            region=data.get('region'),
            avg_lead_time_days=float(data['avg_lead_time_days']) if 'avg_lead_time_days' in data else None,
            on_time_delivery_pct=float(data['on_time_delivery_pct']) if 'on_time_delivery_pct' in data else None,
            quality_score=float(data['quality_score']) if 'quality_score' in data else None
        )
        if success:
            return jsonify({"message": "Supplier updated", "supplier_id": supplier_id})
        return jsonify({"error": "Supplier not found or nothing to update"}), 404
    except Exception as e:
        logger.error(f"Failed to update supplier {supplier_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/suppliers/<supplier_id>', methods=['DELETE'])
def remove_supplier(supplier_id):
    """Remove a supplier."""
    try:
        success = queries.delete_supplier(supplier_id)
        if success:
            return jsonify({"message": "Supplier deleted", "supplier_id": supplier_id})
        return jsonify({"error": "Supplier not found"}), 404
    except Exception as e:
        logger.error(f"Failed to delete supplier {supplier_id}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


# ============================================================================
# WHAT-IF SIMULATION ENGINE
# ============================================================================

@app.route('/api/simulate', methods=['POST'])
def simulate():
    """
    Run a What-If scenario simulation.
    Accepts: { type: 'demand_spike'|'supplier_delay', sku_id|supplier_id, multiplier }
    Returns: before/after comparison with projected impact.
    """
    import os
    data = request.json
    scenario_type = data.get('type')

    try:
        if scenario_type == 'demand_spike':
            sku_id = data.get('sku_id')
            multiplier = float(data.get('multiplier', 1.5))
            if not sku_id:
                return jsonify({'error': 'sku_id required'}), 400

            # Get real historical demand
            demand_history = queries.get_demand_history(sku_id)
            if not demand_history:
                return jsonify({'error': f'No demand history for {sku_id}'}), 404

            current_stock = 0
            warehouse_ids = queries.get_all_warehouse_ids()
            for wh in warehouse_ids:
                current_stock += queries.get_current_stock(sku_id, wh)

            from backend.forecasting import forecast_demand

            # Current forecast (baseline)
            before = forecast_demand(sku_id, demand_history)

            # Simulated forecast (demand spike: multiply units_sold)
            spiked_history = [
                {'date': d['date'], 'units_sold': int(d['units_sold'] * multiplier)}
                for d in demand_history
            ]
            after = forecast_demand(sku_id, spiked_history)

            before_days = round(current_stock / before['avg_forecasted_demand']) if before['avg_forecasted_demand'] > 0 else 999
            after_days = round(current_stock / after['avg_forecasted_demand']) if after['avg_forecasted_demand'] > 0 else 999

            return jsonify({
                'scenario': 'demand_spike',
                'sku_id': sku_id,
                'multiplier': multiplier,
                'current_stock': current_stock,
                'before': {
                    'avg_daily_demand': round(before['avg_forecasted_demand'], 1),
                    'trend': before['trend'],
                    'days_until_stockout': before_days,
                    'confidence': before['confidence'],
                },
                'after': {
                    'avg_daily_demand': round(after['avg_forecasted_demand'], 1),
                    'trend': after['trend'],
                    'days_until_stockout': after_days,
                    'confidence': after['confidence'],
                },
                'impact': {
                    'demand_increase_units': round(after['avg_forecasted_demand'] - before['avg_forecasted_demand'], 1),
                    'stockout_days_lost': before_days - after_days,
                    'severity': 'critical' if after_days < 7 else 'high' if after_days < 14 else 'medium',
                }
            })

        elif scenario_type == 'supplier_delay':
            supplier_id = data.get('supplier_id')
            lead_time_multiplier = float(data.get('multiplier', 2.0))
            if not supplier_id:
                return jsonify({'error': 'supplier_id required'}), 400

            delivery_history = queries.get_supplier_delivery_history(supplier_id)
            if not delivery_history:
                return jsonify({'error': f'No delivery history for {supplier_id}'}), 404

            from backend.suppliers import supplier_risk_score

            # Current risk (baseline)
            before = supplier_risk_score(supplier_id, delivery_history)

            # Simulate worsened delivery: shift all actual_dates later by multiplier
            from datetime import datetime, timedelta
            simulated_history = []
            for record in delivery_history:
                new_record = dict(record)
                if new_record.get('actual_date'):
                    try:
                        promised = datetime.strptime(new_record['promised_date'], '%Y-%m-%d')
                        actual = datetime.strptime(new_record['actual_date'], '%Y-%m-%d')
                        current_delay = max(0, (actual - promised).days)
                        extra_delay = int(current_delay * (lead_time_multiplier - 1)) + int(lead_time_multiplier * 3)
                        new_actual = actual + timedelta(days=extra_delay)
                        new_record['actual_date'] = new_actual.strftime('%Y-%m-%d')
                    except Exception:
                        pass
                simulated_history.append(new_record)

            after = supplier_risk_score(supplier_id, simulated_history)

            return jsonify({
                'scenario': 'supplier_delay',
                'supplier_id': supplier_id,
                'multiplier': lead_time_multiplier,
                'before': {
                    'score': round(before['score'], 1) if before['score'] else None,
                    'risk_category': before['risk_category'],
                    'on_time_pct': round(before['breakdown']['on_time_delivery_pct'] or 0, 1),
                },
                'after': {
                    'score': round(after['score'], 1) if after['score'] else None,
                    'risk_category': after['risk_category'],
                    'on_time_pct': round(after['breakdown']['on_time_delivery_pct'] or 0, 1),
                },
                'impact': {
                    'score_drop': round((before['score'] or 0) - (after['score'] or 0), 1),
                    'risk_escalated': before['risk_category'] != after['risk_category'],
                    'new_risk_level': after['risk_category'],
                    'severity': 'critical' if (after['score'] or 100) < 30 else 'high' if (after['score'] or 100) < 50 else 'medium',
                }
            })

        else:
            return jsonify({'error': f'Unknown scenario type: {scenario_type}'}), 400

    except Exception as e:
        logger.error(f'Simulation failed: {e}', exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# WAREHOUSES (read-only, used for dropdowns)
# ============================================================================

@app.route('/api/warehouses', methods=['GET'])
def get_warehouses():
    """Get all warehouse IDs."""
    try:
        return jsonify(queries.get_all_warehouse_ids())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Not found", "message": str(error)}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error", "message": str(error)}), 500


import os

if __name__ == '__main__':
    print("\n" + "="*60)
    print("[START] SupplySense Backend API Server")
    print("="*60)
    port = int(os.environ.get("PORT", 5000))
    print(f"[INFO] Running on http://0.0.0.0:{port}")
    print("[OK] Dashboard available on frontend")
    print("\n   Press Ctrl+C to stop")
    print("="*60 + "\n")
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
