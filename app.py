from flask import Flask, render_template, redirect, url_for, request, session, jsonify, make_response
from io import BytesIO
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Dummy data for demonstration
users = {
    'warehouse': {'password': 'warehouse123', 'role': 'warehouse'},
    'purchasing': {'password': 'purchasing123', 'role': 'purchasing'},
    'ppic': {'password': 'ppic123', 'role': 'ppic'}
}

inventory_items = [
    {
        'id': 1,
        'incoming_date': '2023-05-01',
        'expiry_date': '2024-05-01',
        'po_number': 'PO-001',
        'material_code': 'MAT-001',
        'description': 'Steel Plate 10mm',
        'weight': 500,
        'quantity': 10,
        'status': 'rack',
        'location': 'A1-01'
    },
    {
        'id': 2,
        'incoming_date': '2023-05-10',
        'expiry_date': '2024-05-10',
        'po_number': 'PO-002',
        'material_code': 'MAT-002',
        'description': 'Aluminum Bar 5mm',
        'weight': 300,
        'quantity': 20,
        'status': 'rack',
        'location': 'B2-05'
    }
]

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = users[username]['role']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', role=session['role'])

@app.route('/inventory')
def inventory():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('inventory.html', items=inventory_items, role=session['role'])

@app.route('/incoming', methods=['GET', 'POST'])
def incoming():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # In a real app, this would save to database
        new_item = {
            'id': len(inventory_items) + 1,
            'incoming_date': request.form['incoming_date'],
            'expiry_date': request.form['expiry_date'],
            'po_number': request.form['po_number'],
            'material_code': request.form['material_code'],
            'description': request.form['description'],
            'weight': float(request.form['weight']),
            'quantity': int(request.form['quantity']),
            'status': 'rack',
            'location': request.form['location']
        }
        inventory_items.append(new_item)
        return redirect(url_for('inventory'))
    
    return render_template('incoming.html', role=session['role'])

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    item = next((item for item in inventory_items if item['id'] == item_id), None)
    
    if not item:
        return redirect(url_for('inventory'))
    
    if request.method == 'POST':
        item['quantity'] = int(request.form['quantity'])
        item['status'] = request.form['status']
        item['location'] = request.form['location']
        return redirect(url_for('inventory'))
    
    return render_template('edit_item.html', item=item, role=session['role'])

@app.route('/generate_barcode/<int:item_id>')
def generate_barcode(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    item = next((item for item in inventory_items if item['id'] == item_id), None)
    
    if not item:
        return redirect(url_for('inventory'))
    
    return render_template('barcode.html', item=item, role=session['role'])

@app.route('/report')
def report():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('report.html', items=inventory_items, role=session['role'])

@app.route('/out_item/<int:item_id>', methods=['GET', 'POST'])
def out_item(item_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    item = next((item for item in inventory_items if item['id'] == item_id), None)
    
    if not item:
        return redirect(url_for('inventory'))
    
    if request.method == 'POST':
        out_quantity = int(request.form['out_quantity'])
        
        # Implement FIFO - Reduce quantity of oldest stock first
        if out_quantity <= item['quantity']:
            item['quantity'] -= out_quantity
            if item['quantity'] == 0:
                item['status'] = 'out'
            return redirect(url_for('inventory'))
        else:
            return render_template('out_item.html', 
                               item=item, 
                               error="Quantity not available")
    
    return render_template('out_item.html', item=item)

@app.route('/export_excel')
def export_excel():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    try:
        # Ambil parameter filter dari URL
        status_filter = request.args.get('status', '')
        from_date = request.args.get('from_date', '')
        to_date = request.args.get('to_date', '')
        
        # Filter data berdasarkan parameter
        filtered_items = inventory_items.copy()
        
        if status_filter:
            filtered_items = [item for item in filtered_items if item.get('status') == status_filter]
        
        if from_date:
            filtered_items = [item for item in filtered_items if item.get('incoming_date', '') >= from_date]
        
        if to_date:
            filtered_items = [item for item in filtered_items if item.get('incoming_date', '') <= to_date]
        
        # Pastikan ada data yang akan diexport
        if not filtered_items:
            return "No data to export", 400
        
        # Buat DataFrame dengan handling error
        df = pd.DataFrame(filtered_items)
        
        # Daftar kolom yang diharapkan
        expected_columns = [
            'incoming_date',
            'expiry_date',
            'po_number',
            'material_code',
            'description',
            'weight',
            'quantity',
            'status',
            'location'
        ]
        
        # Cek kolom yang tersedia
        available_columns = [col for col in expected_columns if col in df.columns]
        
        # Filter kolom yang ada saja
        df = df[available_columns]
        
        # Rename kolom untuk tampilan lebih baik
        column_names = {
            'incoming_date': 'Incoming Date',
            'expiry_date': 'Expiry Date',
            'po_number': 'PO Number',
            'material_code': 'Material Code',
            'description': 'Description',
            'weight': 'Weight (kg)',
            'quantity': 'Quantity',
            'status': 'Status',
            'location': 'Location'
        }
        
        df.rename(columns=column_names, inplace=True)
        
        # Buat output Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Inventory', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Inventory']
            for i, col in enumerate(df.columns):
                column_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + i)].width = column_len
        
        output.seek(0)
        
        # Buat response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = 'attachment; filename=inventory_report.xlsx'
        response.headers['Content-type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        return response
    
    except Exception as e:
        app.logger.error(f"Error exporting Excel: {str(e)}")
        return f"Error generating Excel file: {str(e)}", 500
        response.headers['Content-Disposition'] = 'attachment; filename=inventory_report.xlsx'
        response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        return response


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)