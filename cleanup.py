import sqlite3, json

DB_PATH = 'data/supplysense.db'

def cleanup_duplicate_actions():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM pending_actions WHERE status = 'pending_approval' ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    seen = set()
    to_delete = []
    
    for r in rows:
        action_id = r['action_id']
        try:
            details = json.loads(r['details'])
        except:
            continue
            
        key = None
        if r['action_type'] == 'reorder':
            key = ('reorder', details.get('sku_id'), details.get('warehouse_id'))
        elif r['action_type'] == 'switch_supplier':
            key = ('switch_supplier', details.get('failing_supplier_id'))
        
        if key:
            if key in seen:
                to_delete.append(action_id)
            else:
                seen.add(key)
                
    print(f"Found {len(rows)} pending actions. Keeping {len(seen)} unique. Deleting {len(to_delete)} duplicates.")
    
    for aid in to_delete:
        cursor.execute("DELETE FROM pending_actions WHERE action_id = ?", (aid,))
        
    conn.commit()
    conn.close()

cleanup_duplicate_actions()
