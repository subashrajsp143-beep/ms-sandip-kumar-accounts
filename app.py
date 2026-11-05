import os
import shutil
from datetime import datetime, date, timedelta
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, send_file, send_from_directory, abort
)
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash

import models
import excel_exporter
import num_to_words

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ms_sandip_kumar_jjm_bihar_secret_key_2026_safe')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize database on startup
models.init_db()

def auto_backup_database():
    """Keeps an automatic daily timestamped backup of the database"""
    try:
        backup_dir = os.path.join(BASE_DIR, 'database', 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        today_str = date.today().strftime('%Y-%m-%d')
        dest = os.path.join(backup_dir, f"sandip_accounts_{today_str}.db")
        if not os.path.exists(dest) and os.path.exists(models.DB_PATH):
            shutil.copy2(models.DB_PATH, dest)
    except Exception as e:
        print(f"Auto backup notice: {e}")

auto_backup_database()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Pass-through decorators — All mode restrictions removed as requested
login_required = lambda f: f
owner_required = lambda f: f

# Session lifetime (stays logged in for 30 days)
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)

# Context processor: Available everywhere with global data
@app.context_processor
def inject_global_data():
    firm_settings = models.get_firm_settings()
    return {
        'firm_settings': firm_settings,
        'firm_name': firm_settings.get('firm_name', 'MS SANDIP KUMAR'),
        'firm_subtitle': firm_settings.get('firm_subtitle', 'Jal Jeevan Mission, Bihar Contractor'),
        'logo_initials': firm_settings.get('logo_initials', 'SK'),
        'all_sites': models.get_all_sites(),
        'all_categories': models.get_all_categories(),
        'all_parties': models.get_unique_parties(),
        'today_date': date.today().strftime('%Y-%m-%d'),
        'current_user': {
            'id': session.get('user_id'),
            'username': session.get('username', 'sandip'),
            'full_name': session.get('full_name', firm_settings.get('firm_name', 'MS Sandip Kumar')),
            'role': session.get('role', 'OWNER')
        }
    }

# Authentication Barrier — Protected by Password
@app.before_request
def check_authentication():
    # Public endpoints that do not require login
    if request.endpoint in ['login', 'static'] or request.path.startswith('/static/'):
        return
    # Require login for all other pages & APIs
    if 'user_id' not in session:
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'message': 'कृपया पहले लॉगिन करें / Please login first'}), 401
        return redirect(url_for('login', next=request.path))

# --- Secure Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = models.authenticate_user(username, password)
        if user:
            session.permanent = True
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            session['phone'] = user.get('phone', '')
            
            models.log_activity(
                user['id'],
                user['username'],
                'LOGIN',
                'User logged in successfully',
                request.remote_addr
            )
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard'))
        else:
            error = "गलत पासवर्ड! कृपया सही पासवर्ड दर्ज करें। (डिफ़ॉल्ट पासवर्ड: 123456)"
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    uid = session.get('user_id')
    uname = session.get('username', 'Anonymous')
    if uid:
        models.log_activity(uid, uname, 'LOGOUT', 'User logged out', request.remote_addr)
    session.clear()
    flash('आप सफलतापूर्वक पोर्टल से बाहर निकल गए हैं।', 'info')
    return redirect(url_for('login'))

@app.route('/change-password', methods=['GET', 'POST'])
def change_password_view():
    if 'user_id' not in session:
        return redirect(url_for('login', next='/change-password'))
        
    error = None
    if request.method == 'POST':
        old_password = request.form.get('old_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        if not new_password:
            error = "कृपया नया पासवर्ड दर्ज करें!"
        elif new_password != confirm_password:
            error = "नया पासवर्ड और कन्फर्म पासवर्ड मैच नहीं हो रहे हैं!"
        elif len(new_password) < 4:
            error = "नया पासवर्ड कम से कम 4 अक्षरों का होना चाहिए!"
        else:
            user = models.get_user_by_id(session['user_id'])
            if old_password and user:
                valid_old = check_password_hash(user['password_hash'], old_password) or (old_password in ['123456', 'Sandip@@12', 'sandip123', 'admin123', 'admin'])
                if not valid_old:
                    error = "पुराना पासवर्ड मैच नहीं हुआ! डिफ़ॉल्ट पासवर्ड 123456 है (या इसे खाली छोड़ दें)।"
            
            if not error:
                models.update_user_password(session['user_id'], new_password)
                models.log_activity(
                    session['user_id'],
                    session.get('username', 'user'),
                    'PASSWORD_CHANGED',
                    'User successfully changed password via full page',
                    request.remote_addr
                )
                flash('✅ पासवर्ड सफलतापूर्वक बदल दिया गया है! अगली बार लॉगिन के लिए नया पासवर्ड याद रखें।', 'success')
                return redirect(url_for('dashboard'))
                
    return render_template('change_password.html', error=error, active_page='security')

@app.route('/api/change-password', methods=['POST'])
def api_change_password():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'सत्र समाप्त हो गया है। कृपया दोबारा लॉगिन करें।'}), 401
        
    user_id = session['user_id']
    old_password = request.form.get('old_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()
    
    if not new_password:
        return jsonify({'success': False, 'message': 'कृपया नया पासवर्ड दर्ज करें!'}), 400
        
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'नया पासवर्ड और कन्फर्म पासवर्ड मैच नहीं कर रहे हैं!'}), 400
        
    if len(new_password) < 4:
        return jsonify({'success': False, 'message': 'नया पासवर्ड कम से कम 4 अक्षरों का होना चाहिए!'}), 400
        
    user = models.get_user_by_id(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'यूजर खाता नहीं मिला!'}), 404
        
    # Check old password if provided
    # Accept: correct hash OR 123456/Sandip@@12/admin etc. OR if blank (user is already authenticated in session)
    if old_password:
        valid_old = check_password_hash(user['password_hash'], old_password) or (old_password in ['123456', 'Sandip@@12', 'sandip123', 'admin123', 'admin'])
        if not valid_old:
            return jsonify({'success': False, 'message': 'पुराना पासवर्ड मैच नहीं हुआ! डिफ़ॉल्ट पासवर्ड 123456 है (या इसे खाली छोड़ दें)।'}), 400
            
    models.update_user_password(user_id, new_password)
    models.log_activity(
        user_id,
        session.get('username', 'user'),
        'PASSWORD_CHANGED',
        'User successfully changed their access password',
        request.remote_addr
    )
    
    return jsonify({
        'success': True,
        'message': 'पासवर्ड सफलतापूर्वक बदल दिया गया है! अगली बार लॉगिन के लिए नया पासवर्ड याद रखें।'
    })

@app.route('/api/firm-settings/update', methods=['POST'])
def api_update_firm_settings():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'सत्र समाप्त हो गया है। कृपया दोबारा लॉगिन करें।'}), 401
        
    firm_name = request.form.get('firm_name', '').strip()
    firm_subtitle = request.form.get('firm_subtitle', '').strip()
    logo_initials = request.form.get('logo_initials', '').strip()
    
    if not firm_name:
        return jsonify({'success': False, 'message': 'फ़र्म का नाम खाली नहीं हो सकता!'}), 400
        
    models.update_firm_settings(
        firm_name=firm_name,
        firm_subtitle=firm_subtitle,
        logo_initials=logo_initials
    )
    models.log_activity(
        session.get('user_id', 1),
        session.get('username', 'sandip'),
        'UPDATE_FIRM_SETTINGS',
        f'Firm details updated to: {firm_name}',
        request.remote_addr
    )
    return jsonify({
        'success': True,
        'message': 'फ़र्म का नाम और विवरण सफलतापूर्वक अपडेट कर दिया गया है!',
        'firm_name': firm_name
    })

@app.route('/reset-data', methods=['POST'])
def reset_all_data():
    """Wipes all transactions to clean ₹ 0.00 zero balance on demand"""
    models.reset_all_balances_to_zero()
    models.log_activity(
        session.get('user_id', 1),
        'sandip',
        'RESET_ZERO_BALANCE',
        'All transactions deleted. Balance reset to ₹ 0.00',
        request.remote_addr
    )
    flash('Sabhi transactions aur balances safaltapoorvak ZERO kar diye gaye hain! Fresh entries ke liye taiyar hai.', 'success')
    return redirect(url_for('dashboard'))

# --- Dashboard Overview ---
@app.route('/')
@app.route('/dashboard')
@login_required
def dashboard():
    selected_fy = request.args.get('fy', 'all')
    selected_month = request.args.get('month', 'all')
    selected_site = request.args.get('site_id', 'all')

    summary = models.get_financial_summary(fy=selected_fy, month=selected_month, site_id=selected_site)
    site_chart_data = models.get_site_wise_summary(fy=selected_fy)
    cat_chart_data = summary.get('category_expenses', [])

    # Fetch recent transactions
    conn = models.get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, s.name AS site_name, s.code AS site_code
        FROM transactions t
        LEFT JOIN sites s ON t.site_id = s.id
        WHERE t.status = 'APPROVED'
        ORDER BY t.tx_date DESC, t.id DESC
        LIMIT 10
    ''')
    recent_txs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template(
        'dashboard.html',
        active_page='dashboard',
        summary=summary,
        site_chart_data=site_chart_data,
        cat_chart_data=cat_chart_data,
        recent_transactions=recent_txs,
        selected_fy=selected_fy,
        selected_month=selected_month,
        selected_site=selected_site
    )

# --- All Transactions (Master Ledger) ---
@app.route('/transactions')
@login_required
def transactions_view():
    current_type = request.args.get('tx_type', 'all')
    current_site = request.args.get('site_id', 'all')
    current_category = request.args.get('category', 'all')
    date_filter = request.args.get('date_filter', 'all')

    conn = models.get_db()
    cursor = conn.cursor()

    where_clauses = ["t.status = 'APPROVED'"]
    params = []

    if current_type != 'all':
        where_clauses.append("t.tx_type = ?")
        params.append(current_type)
    if current_site != 'all':
        where_clauses.append("t.site_id = ?")
        params.append(int(current_site))
    if current_category != 'all':
        where_clauses.append("t.category = ?")
        params.append(current_category)

    today = date.today()
    if date_filter == 'today':
        where_clauses.append("t.tx_date = ?")
        params.append(today.strftime('%Y-%m-%d'))
    elif date_filter == 'yesterday':
        yest = today - timedelta(days=1)
        where_clauses.append("t.tx_date = ?")
        params.append(yest.strftime('%Y-%m-%d'))
    elif date_filter == 'this_week':
        start_week = today - timedelta(days=today.weekday())
        where_clauses.append("t.tx_date >= ? AND t.tx_date <= ?")
        params.extend([start_week.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')])
    elif date_filter == 'this_month':
        start_month = today.replace(day=1)
        where_clauses.append("t.tx_date >= ? AND t.tx_date <= ?")
        params.extend([start_month.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')])

    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    if start_date:
        where_clauses.append("t.tx_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("t.tx_date <= ?")
        params.append(end_date)

    where_sql = " AND ".join(where_clauses)
    query = f'''
        SELECT t.*, s.name AS site_name, s.code AS site_code
        FROM transactions t
        LEFT JOIN sites s ON t.site_id = s.id
        WHERE {where_sql}
        ORDER BY t.tx_date DESC, t.id DESC
    '''
    cursor.execute(query, params)
    tx_list = [dict(r) for r in cursor.fetchall()]
    conn.close()

    total_credit = sum(t['amount'] for t in tx_list if t['tx_type'] == 'CREDIT')
    total_debit = sum(t['amount'] for t in tx_list if t['tx_type'] == 'DEBIT')

    return render_template(
        'transactions.html',
        active_page='transactions',
        transactions=tx_list,
        total_credit=total_credit,
        total_debit=total_debit,
        current_type=current_type,
        current_site=current_site,
        current_category=current_category,
        date_filter=date_filter,
        start_date=start_date,
        end_date=end_date
    )

# --- Site Ledger View ---
@app.route('/site-ledger')
@login_required
def site_ledger_view():
    all_sites = models.get_all_sites()
    selected_site_id = request.args.get('site_id')
    if not selected_site_id and all_sites:
        selected_site_id = all_sites[1]['id'] if len(all_sites) > 1 else all_sites[0]['id'] # default to SITE-01
    else:
        selected_site_id = int(selected_site_id)

    ledger_data = models.get_site_ledger(selected_site_id)

    return render_template(
        'site_ledger.html',
        active_page='site_ledger',
        all_sites=all_sites,
        selected_site_id=selected_site_id,
        ledger_data=ledger_data
    )

# --- Party / Vendor Khata View ---
@app.route('/party-khata')
@login_required
def party_khata_view():
    all_parties = models.get_unique_parties()
    selected_party = request.args.get('party_name', '').strip()

    party_data = None
    if selected_party:
        party_data = models.get_party_ledger(selected_party)

    return render_template(
        'party_khata.html',
        active_page='party_khata',
        all_parties=all_parties,
        selected_party=selected_party,
        party_data=party_data
    )

# --- Daybook (Daily Cashflow) View ---
@app.route('/daybook')
@login_required
def daybook_view():
    selected_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    daybook_data = models.get_daybook(selected_date)

    return render_template(
        'daybook.html',
        active_page='daybook',
        selected_date=selected_date,
        daybook=daybook_data
    )

# --- Printable Official Voucher View ---
@app.route('/voucher/<int:tx_id>')
@login_required
def voucher_view(tx_id):
    tx = models.get_transaction_by_id(tx_id)
    if not tx:
        flash('Voucher not found.', 'error')
        return redirect(url_for('transactions_view'))

    words = num_to_words.number_to_indian_words(tx['amount'])
    return render_template(
        'voucher.html',
        active_page='transactions',
        tx=tx,
        amount_in_words=words
    )

# --- Treasury & Backup (Owner View) ---
@app.route('/treasury-backup')
@owner_required
def treasury_backup_view():
    summary = models.get_financial_summary()
    site_stats = models.get_site_wise_summary()

    conn = models.get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM audit_logs ORDER BY id DESC LIMIT 20')
    audit_logs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    return render_template(
        'backup.html',
        active_page='backup',
        summary=summary,
        site_stats=site_stats,
        audit_logs=audit_logs
    )

# --- JSON API Endpoints for Modals & Dynamic UI ---
@app.route('/api/next_site_code')
@login_required
def api_next_site_code():
    return jsonify({'code': models.get_next_site_code()})

@app.route('/api/site/create', methods=['POST'])
@login_required
def api_create_site():
    try:
        name = request.form.get('name', '').strip()
        district = request.form.get('district', '').strip()
        description = request.form.get('description', '').strip()
        code = request.form.get('code', '').strip().upper()

        if not name:
            return jsonify({'success': False, 'message': 'Site Name is required.'}), 400

        new_id, code = models.add_new_site(name, district, description, code=code if code else None)
        models.log_activity(
            session.get('user_id', 1),
            'sandip',
            'ADD_SITE',
            f"Created new site {code} - {name} ({district})",
            request.remote_addr
        )

        return jsonify({
            'success': True,
            'message': f'New Site {code} — {name} added successfully!',
            'site_id': new_id,
            'code': code,
            'name': name,
            'district': district
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/category/create', methods=['POST'])
@login_required
def api_create_category():
    try:
        name = request.form.get('name', '').strip()
        cat_type = request.form.get('type', 'DEBIT').strip().upper()

        if not name:
            return jsonify({'success': False, 'message': 'Purpose / Category Name is required.'}), 400

        if cat_type not in ('DEBIT', 'CREDIT', 'BOTH'):
            cat_type = 'DEBIT'

        cat_id, cat_name, cat_type, is_new = models.add_new_category(name, cat_type)
        models.log_activity(
            session.get('user_id', 1),
            'sandip',
            'ADD_CATEGORY',
            f"Added Purpose/Category: {cat_name} ({cat_type})",
            request.remote_addr
        )

        msg = f'Purpose "{cat_name}" added successfully!' if is_new else f'Purpose "{cat_name}" already exists.'

        return jsonify({
            'success': True,
            'message': msg,
            'category_id': cat_id,
            'name': cat_name,
            'type': cat_type,
            'is_new': is_new
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/cloud-backup', methods=['POST'])
@login_required
def api_cloud_backup():
    try:
        import cloud_backup
        result = cloud_backup.run_cloud_backup()
        models.log_activity(
            session.get('user_id', 1),
            'sandip',
            'CLOUD_BACKUP',
            "Triggered cloud backup to GitHub and OneDrive",
            request.remote_addr
        )
        return jsonify({
            'success': True,
            'message': 'Cloud Backup successful! Synced to GitHub & OneDrive.',
            'details': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/next_voucher')
@login_required
def api_next_voucher():
    return jsonify({'voucher_no': models.generate_voucher_no()})

@app.route('/api/transaction/<int:tx_id>')
@login_required
def api_get_transaction(tx_id):
    tx = models.get_transaction_by_id(tx_id)
    if tx:
        return jsonify({'success': True, 'transaction': tx})
    return jsonify({'success': False, 'message': 'Not found'}), 404

@app.route('/api/transaction/create', methods=['POST'])
@login_required
def api_create_transaction():
    try:
        tx_type = request.form.get('tx_type', 'DEBIT').upper()
        raw_site = request.form.get('site_id')
        # Credit is from an Individual Person, so site defaults to Central Pool (1)
        if tx_type == 'CREDIT':
            site_id = int(raw_site) if raw_site and str(raw_site).isdigit() else 1
        else:
            site_id = int(raw_site) if raw_site and str(raw_site).isdigit() else 1

        tx_date = request.form.get('tx_date') or date.today().strftime('%Y-%m-%d')
        party_name = request.form.get('party_name', '').strip()
        category = request.form.get('category', '').strip()
        amount = float(request.form.get('amount', 0))
        payment_mode = request.form.get('payment_mode', 'Bank Transfer')
        reference_no = request.form.get('reference_no', '').strip()
        narration = request.form.get('narration', '').strip()

        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than zero.'}), 400
        if not party_name:
            return jsonify({'success': False, 'message': 'Party Name is required.'}), 400

        voucher_no = models.generate_voucher_no()

        # Handle file upload if present
        attachment_path = None
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                timestamp_prefix = datetime.now().strftime('%Y%m%d%H%M%S_')
                saved_name = f"{timestamp_prefix}{fname}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_name))
                attachment_path = saved_name

        conn = models.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO transactions (
                voucher_no, tx_type, site_id, tx_date, party_name, category,
                amount, payment_mode, reference_no, narration, attachment_path, status, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'APPROVED', ?)
        ''', (voucher_no, tx_type, site_id, tx_date, party_name, category, amount, payment_mode, reference_no, narration, attachment_path, session.get('user_id')))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        models.log_activity(
            session.get('user_id'),
            session.get('username'),
            'ADD_TRANSACTION',
            f"Created {tx_type} voucher {voucher_no} of Rs. {amount} for {party_name}",
            request.remote_addr
        )

        return jsonify({
            'success': True,
            'message': f"Transaction {voucher_no} successfully saved!",
            'voucher_no': voucher_no,
            'id': new_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/transaction/<int:tx_id>/update', methods=['POST'])
@login_required
def api_update_transaction(tx_id):
    try:
        conn = models.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM transactions WHERE id = ?', (tx_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Transaction not found.'}), 404

        tx_type = request.form.get('tx_type', existing['tx_type']).upper()
        raw_site = request.form.get('site_id')
        if tx_type == 'CREDIT':
            site_id = int(raw_site) if raw_site and str(raw_site).isdigit() else 1
        else:
            site_id = int(raw_site) if raw_site and str(raw_site).isdigit() else existing['site_id']
        tx_date = request.form.get('tx_date', existing['tx_date'])
        party_name = request.form.get('party_name', existing['party_name']).strip()
        category = request.form.get('category', existing['category']).strip()
        amount = float(request.form.get('amount', existing['amount']))
        payment_mode = request.form.get('payment_mode', existing['payment_mode'])
        reference_no = request.form.get('reference_no', existing['reference_no'] or '').strip()
        narration = request.form.get('narration', existing['narration'] or '').strip()

        attachment_path = existing['attachment_path']
        if 'attachment' in request.files:
            file = request.files['attachment']
            if file and file.filename and allowed_file(file.filename):
                fname = secure_filename(file.filename)
                timestamp_prefix = datetime.now().strftime('%Y%m%d%H%M%S_')
                saved_name = f"{timestamp_prefix}{fname}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], saved_name))
                attachment_path = saved_name

        cursor.execute('''
            UPDATE transactions SET
                tx_type = ?, site_id = ?, tx_date = ?, party_name = ?,
                category = ?, amount = ?, payment_mode = ?, reference_no = ?,
                narration = ?, attachment_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (tx_type, site_id, tx_date, party_name, category, amount, payment_mode, reference_no, narration, attachment_path, tx_id))
        conn.commit()
        conn.close()

        models.log_activity(
            session.get('user_id'),
            session.get('username'),
            'UPDATE_TRANSACTION',
            f"Updated voucher {existing['voucher_no']} - New amount Rs. {amount}",
            request.remote_addr
        )

        return jsonify({'success': True, 'message': 'Transaction updated successfully!'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/transaction/<int:tx_id>/delete', methods=['POST'])
@owner_required
def api_delete_transaction(tx_id):
    try:
        conn = models.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT voucher_no, amount, party_name FROM transactions WHERE id = ?', (tx_id,))
        existing = cursor.fetchone()
        if not existing:
            conn.close()
            return jsonify({'success': False, 'message': 'Transaction not found.'}), 404

        v_no = existing['voucher_no']
        amt = existing['amount']
        p_name = existing['party_name']

        cursor.execute('DELETE FROM transactions WHERE id = ?', (tx_id,))
        conn.commit()
        conn.close()

        models.log_activity(
            session.get('user_id'),
            session.get('username'),
            'DELETE_TRANSACTION',
            f"Proprietor deleted voucher {v_no} (Rs. {amt} - {p_name})",
            request.remote_addr
        )

        return jsonify({'success': True, 'message': f"Voucher {v_no} permanently deleted."})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# --- File Uploads View Route ---
@app.route('/uploads/<filename>')
@login_required
def view_upload(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- 1-Click Excel Exports ---
@app.route('/export/site-ledger')
@login_required
def export_site_ledger_view():
    site_id = request.args.get('site_id', 1)
    ledger_data = models.get_site_ledger(int(site_id))
    if not ledger_data:
        flash('Site not found', 'error')
        return redirect(url_for('site_ledger_view'))

    excel_buf = excel_exporter.export_site_ledger_to_excel(ledger_data)
    site_code = ledger_data['site']['code']
    filename = f"Ledger_{site_code}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return send_file(
        excel_buf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/export/party-ledger')
@login_required
def export_party_ledger_view():
    party_name = request.args.get('party_name', '').strip()
    if not party_name:
        flash('Please select a party first', 'error')
        return redirect(url_for('party_khata_view'))

    party_data = models.get_party_ledger(party_name)
    excel_buf = excel_exporter.export_party_ledger_to_excel(party_data)
    safe_name = "".join(c for c in party_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    filename = f"Khata_{safe_name}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return send_file(
        excel_buf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/export/daybook')
@login_required
def export_daybook_view():
    date_str = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    daybook_data = models.get_daybook(date_str)
    excel_buf = excel_exporter.export_daybook_to_excel(daybook_data)
    filename = f"Daybook_{date_str}.xlsx"
    return send_file(
        excel_buf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.route('/export/transactions')
@login_required
def export_all_transactions_view():
    # Filtered transactions export
    tx_type = request.args.get('tx_type', 'all')
    site_id = request.args.get('site_id', 'all')
    category = request.args.get('category', 'all')

    conn = models.get_db()
    cursor = conn.cursor()
    where_clauses = ["t.status = 'APPROVED'"]
    params = []

    if tx_type != 'all':
        where_clauses.append("t.tx_type = ?")
        params.append(tx_type)
    if site_id != 'all':
        where_clauses.append("t.site_id = ?")
        params.append(int(site_id))
    if category != 'all':
        where_clauses.append("t.category = ?")
        params.append(category)

    where_sql = " AND ".join(where_clauses)
    query = f'''
        SELECT t.*, s.name AS site_name, s.code AS site_code
        FROM transactions t
        LEFT JOIN sites s ON t.site_id = s.id
        WHERE {where_sql}
        ORDER BY t.tx_date ASC, t.id ASC
    '''
    cursor.execute(query, params)
    tx_list = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Reuse daybook-like format with all txs
    mock_day = {
        'date': f"All_Txs_{datetime.now().strftime('%Y%m%d')}",
        'transactions': tx_list,
        'total_credit': sum(t['amount'] for t in tx_list if t['tx_type'] == 'CREDIT'),
        'total_debit': sum(t['amount'] for t in tx_list if t['tx_type'] == 'DEBIT'),
        'net_day_change': sum(t['amount'] if t['tx_type'] == 'CREDIT' else -t['amount'] for t in tx_list),
        'day_cash_in': sum(t['amount'] for t in tx_list if t['tx_type'] == 'CREDIT' and t['payment_mode'] == 'Cash'),
        'day_cash_out': sum(t['amount'] for t in tx_list if t['tx_type'] == 'DEBIT' and t['payment_mode'] == 'Cash'),
        'day_bank_in': sum(t['amount'] for t in tx_list if t['tx_type'] == 'CREDIT' and t['payment_mode'] != 'Cash'),
        'day_bank_out': sum(t['amount'] for t in tx_list if t['tx_type'] == 'DEBIT' and t['payment_mode'] != 'Cash'),
    }
    excel_buf = excel_exporter.export_daybook_to_excel(mock_day)
    return send_file(
        excel_buf,
        as_attachment=True,
        download_name=f"Master_Ledger_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- Database Backup & Restore Routes (Owner Only) ---
@app.route('/backup/download')
@owner_required
def download_raw_db():
    models.log_activity(
        session.get('user_id'),
        session.get('username'),
        'BACKUP_DOWNLOAD',
        'Owner downloaded full SQLite database backup',
        request.remote_addr
    )
    return send_file(
        models.DB_PATH,
        as_attachment=True,
        download_name=f"sandip_accounts_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
        mimetype='application/x-sqlite3'
    )

@app.route('/backup/restore', methods=['POST'])
@owner_required
def restore_database():
    if 'db_file' not in request.files:
        flash('No file selected for restoration.', 'error')
        return redirect(url_for('treasury_backup_view'))

    file = request.files['db_file']
    if not file or not file.filename:
        flash('Invalid backup file.', 'error')
        return redirect(url_for('treasury_backup_view'))

    try:
        # Create safety copy of existing DB
        backup_stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safety_path = f"{models.DB_PATH}.safety_backup_{backup_stamp}"
        if os.path.exists(models.DB_PATH):
            shutil.copy2(models.DB_PATH, safety_path)

        # Replace database
        file.save(models.DB_PATH)

        models.log_activity(
            session.get('user_id'),
            session.get('username'),
            'BACKUP_RESTORE',
            f'Owner restored database from {file.filename}',
            request.remote_addr
        )

        flash('Database successfully restored! All records have been updated.', 'success')
    except Exception as e:
        flash(f'Restoration failed: {str(e)}', 'error')

    return redirect(url_for('treasury_backup_view'))

if __name__ == '__main__':
    # Running on local port 5050 for testing and daily use
    print("=" * 60)
    print("M/S SANDIP KUMAR — JJM BIHAR ACCOUNTS PORTAL")
    print("Running on: http://127.0.0.1:5050")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5050, debug=False)
