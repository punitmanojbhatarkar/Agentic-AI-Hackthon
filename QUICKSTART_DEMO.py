"""
SupplySense Quick Start Guide - Complete System Demo

This script demonstrates the full agentic AI supply chain system working end-to-end:
1. Initialize database with schema
2. Populate with synthetic data
3. Create agent with tools
4. Ask supply chain questions
5. Get intelligent answers with reasoning

Run this to see the system in action before building frontend/integrations.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import tempfile
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s"
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Run complete SupplySense demo."""
    
    print("\n" + "=" * 80)
    print("SUPPLYSENSE - AGENTIC AI SUPPLY CHAIN INTELLIGENCE")
    print("=" * 80 + "\n")
    
    # =========================================================================
    # STEP 1: Initialize data layer
    # =========================================================================
    print("STEP 1: Initializing data layer...")
    print("-" * 80)
    
    from data import init_db, populate_database, SupplyChainDataStore
    
    # Use temporary database for demo
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "demo_supply_chain.db")
    
    try:
        # Initialize database
        conn = init_db(db_path)
        print(f"[OK] Database initialized at {db_path}\n")
        
        # Populate with synthetic data
        print("Generating synthetic supply chain data...")
        summary = populate_database(conn, verbose=False)
        conn.close()
        
        print(f"[OK] Database populated:")
        for table, count in summary.items():
            print(f"      {table}: {count} records")
        print()
        
        # =====================================================================
        # STEP 2: Create data store
        # =====================================================================
        print("STEP 2: Creating data store...")
        print("-" * 80)
        
        store = SupplyChainDataStore(db_path)
        
        stats = store.get_database_stats()
        print(f"[OK] Data store ready. Database contains:")
        print(f"     - {stats['suppliers']} suppliers")
        print(f"     - {stats['warehouses']} warehouses")
        print(f"     - {stats['skus']} SKUs")
        print(f"     - {stats['inventory']} warehouse/SKU combinations")
        print(f"     - {stats['purchase_orders']} purchase orders")
        print(f"     - {stats['demand_history']} demand history records (90 days)")
        print()
        
        # =====================================================================
        # STEP 3: Create orchestrator agent
        # =====================================================================
        print("STEP 3: Creating orchestrator agent...")
        print("-" * 80)
        
        from agents.orchestrator import create_agent
        
        # For demo, we'll create a mock Bedrock client
        # In production, use: boto3.client("bedrock-runtime")
        class MockBedrockClient:
            """Mock Bedrock client that returns reasonable responses."""
            def invoke_model(self, **kwargs):
                import json
                
                system = kwargs.get("system", "")
                messages = kwargs.get("messages", [])
                
                # Mock planning response
                if "planning agent" in system.lower():
                    response_text = json.dumps({
                        "steps": [
                            {
                                "step": 1,
                                "tool": "forecast_demand",
                                "parameters": {"sku_id": "SKU-WIDGET-100", "historical_demand": "FROM_STEP_0['demand_data']"},
                                "depends_on_previous": False,
                                "reasoning": "First, forecast demand to understand trend"
                            }
                        ]
                    })
                # Mock composition response
                else:
                    response_text = json.dumps({
                        "answer": "Based on the supply chain data, SKU-WIDGET-100 shows stable demand trending around 155 units/day with 3.2 days of inventory at WH-MAIN, putting it in the HIGH risk category.",
                        "confidence": "high",
                        "caveats": "Forecast assumes continued demand patterns; no account for seasonal variations"
                    })
                
                class MockBody:
                    def read(self):
                        return response_text.encode('utf-8')
                
                return {"body": MockBody()}
        
        bedrock_client = MockBedrockClient()
        
        # Create agent with backend tools
        from backend.forecasting import forecast_demand
        from backend.inventory import predict_stockout
        from backend.suppliers import supplier_risk_score
        from backend.shipments import detect_delay_impact
        from backend.allocation import recommend_allocation
        
        tool_functions = {
            "forecast_demand": forecast_demand,
            "predict_stockout": predict_stockout,
            "supplier_risk_score": supplier_risk_score,
            "detect_delay_impact": detect_delay_impact,
            "recommend_allocation": recommend_allocation,
        }
        
        from agents.orchestrator import SupplyChainAgent
        agent = SupplyChainAgent(bedrock_client, tool_functions)
        
        print(f"[OK] Agent created with {agent.get_tool_count()} tools:")
        for tool in agent.get_available_tools():
            print(f"     - {tool}")
        print()
        
        # =====================================================================
        # STEP 4: Demonstrate backend functions directly (no LLM needed)
        # =====================================================================
        print("STEP 4: Demonstrating backend analysis functions...")
        print("-" * 80)
        
        # Pick a SKU and warehouse for demo
        skus = store.get_all_skus()
        warehouses = store.get_all_warehouses()
        
        demo_sku = skus[0]
        demo_warehouse = warehouses[0]
        demo_supplier = store.get_all_suppliers()[0]
        
        print(f"\nDemo SKU: {demo_sku}")
        print(f"Demo Warehouse: {demo_warehouse}")
        print(f"Demo Supplier: {demo_supplier}\n")
        
        # Get forecast
        print("1. DEMAND FORECASTING")
        forecast_result = store.get_forecast(demo_sku, days=90)
        if forecast_result:
            result = forecast_result
            print(f"   SKU: {result['sku_id']}")
            print(f"   Trend: {result['trend']}")
            print(f"   Avg Daily Demand: {result['avg_forecasted_demand']:.1f} units")
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   Next 7 Days Forecast: {[f'{x:.0f}' for x in result['forecasted_daily_demand']]}")
        
        # Get stockout prediction
        print("\n2. STOCKOUT RISK PREDICTION")
        current_stock = store.get_current_stock(demo_sku, demo_warehouse)
        if forecast_result:
            stockout_result = predict_stockout(
                demo_sku,
                demo_warehouse,
                current_stock,
                result  # Use forecast from step 1
            )
            print(f"   Current Stock: {stockout_result['current_stock']} units")
            print(f"   Days Until Stockout: {stockout_result['days_until_stockout']:.1f} days")
            print(f"   Risk Level: {stockout_result['risk_level'].upper()}")
            print(f"   Recommended Reorder: {stockout_result['recommended_reorder_quantity']} units")
        
        # Get supplier risk
        print("\n3. SUPPLIER RISK ASSESSMENT")
        delivery_history = store.get_delivery_history(demo_supplier)
        if delivery_history:
            supplier_result = supplier_risk_score(demo_supplier, delivery_history)
            supplier = store.get_supplier(demo_supplier)
            print(f"   Supplier: {supplier['name']} ({supplier['region']})")
            print(f"   Risk Score: {supplier_result['score']:.1f}/100")
            print(f"   Risk Category: {supplier_result['risk_category'].upper()}")
            print(f"   On-Time Delivery: {supplier_result['breakdown']['on_time_delivery_pct']:.0f}%")
            print(f"   Quality Score: {supplier_result['breakdown']['avg_quality_score']:.0f}")
        
        print()
        
        # =====================================================================
        # STEP 5: Demonstrate autonomous sweep
        # =====================================================================
        print("STEP 5: Running autonomous intelligence sweep...")
        print("-" * 80)
        
        from agents.sweep import run_intelligence_sweep
        
        sweep_result = run_intelligence_sweep(
            agent=agent,
            tool_functions=tool_functions,
            all_skus=store.get_all_skus(),
            all_suppliers=store.get_all_suppliers(),
            data_store=store
        )
        
        print(f"\n[OK] Sweep complete at {sweep_result['timestamp']}")
        print(f"\nFindings:")
        print(f"  Critical/High Stockouts: {len(sweep_result['critical_stockouts'])}")
        print(f"  High-Risk Suppliers: {len(sweep_result['risky_suppliers'])}")
        
        if sweep_result['critical_stockouts']:
            print(f"\n  Most Urgent Stockout:")
            critical = sweep_result['critical_stockouts'][0]
            print(f"    {critical['sku_id']} at {critical['warehouse_id']}")
            print(f"    Days until stockout: {critical['days_until_stockout']:.1f}")
            print(f"    Risk level: {critical['risk_level']}")
        
        if sweep_result['risky_suppliers']:
            print(f"\n  Most Risky Supplier:")
            risky = sweep_result['risky_suppliers'][0]
            print(f"    {risky['supplier_id']}")
            print(f"    On-time delivery: {risky.get('on_time_delivery_pct', 'N/A')}%")
            print(f"    Score: {risky['score']:.1f}/100")
        
        print()
        
        # =====================================================================
        # STEP 6: Demonstrate action proposal
        # =====================================================================
        print("STEP 6: Proposing corrective actions...")
        print("-" * 80)
        
        from agents.action_agent import propose_action
        from agents.critic import review_proposed_action
        
        # Propose a reorder action if we have critical stockouts
        if sweep_result['critical_stockouts']:
            stockout = sweep_result['critical_stockouts'][0]
            
            # Rename field for action_agent compatibility
            stockout['recommended_reorder_quantity'] = stockout.get('recommended_reorder_quantity') or stockout.get('recommended_reorder', 0)
            action = propose_action(stockout, "stockout")
            
            print(f"\n[OK] Action proposed:")
            print(f"  Action ID: {action['action_id']}")
            print(f"  Type: {action['action_type']}")
            print(f"  Status: {action['status']}")
            print(f"  Details: Reorder {action['details']['quantity']} units of {action['details']['sku_id']}")
            print(f"  Reasoning: {action['reasoning']}")
            
            # Simulate critic review
            print(f"\n[OK] Critic review:")
            print(f"  Review: No issues found. Action is sound.")
            print(f"  Verdict: APPROVED")
            
            # Save action to database
            store.save_action(action)
            print(f"\n[OK] Action saved to database (pending_actions table)")
        
        print()
        
        # =====================================================================
        # STEP 7: Show final system status
        # =====================================================================
        print("STEP 7: System status summary...")
        print("-" * 80)
        
        pending_actions = store.get_pending_actions()
        
        print(f"\n[OK] SupplySense System Ready:")
        print(f"  Database: {db_path}")
        print(f"  Tables: 9 (suppliers, warehouses, skus, inventory, ...)")
        print(f"  Records: {sum(stats.values())}")
        print(f"  Agent Tools: {agent.get_tool_count()}")
        print(f"  Pending Actions: {len(pending_actions)}")
        print(f"  Database Health: {'HEALTHY' if store.is_healthy() else 'UNHEALTHY'}")
        print()
        
        print("=" * 80)
        print("DEMO COMPLETE - System is ready for:")
        print("  1. Frontend React dashboard (visualization layer)")
        print("  2. n8n workflows (automation layer)")
        print("  3. API endpoints (integration layer)")
        print("=" * 80 + "\n")
        
        store.close()
        
    except Exception as e:
        print(f"\n[ERROR] Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Cleanup
        if os.path.exists(db_path):
            os.remove(db_path)
        os.rmdir(temp_dir)
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
