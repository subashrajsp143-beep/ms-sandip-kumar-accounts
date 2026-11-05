import sqlite3
import os
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'database', 'sandip_accounts.db')

def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_db()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('OWNER', 'ACCOUNTANT')),
            phone TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Sites Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            district TEXT,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. Categories / Heads of Account Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('DEBIT', 'CREDIT', 'BOTH')),
            color_code TEXT DEFAULT '#163F37'
        )
    ''')

    # 4. Transactions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voucher_no TEXT UNIQUE NOT NULL,
            tx_type TEXT NOT NULL CHECK(tx_type IN ('CREDIT', 'DEBIT')),
            site_id INTEGER NOT NULL,
            tx_date DATE NOT NULL,
            party_name TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            payment_mode TEXT NOT NULL CHECK(payment_mode IN ('Bank Transfer', 'Cheque', 'Cash', 'UPI')),
            reference_no TEXT,
            narration TEXT,
            attachment_path TEXT,
            status TEXT DEFAULT 'APPROVED' CHECK(status IN ('APPROVED', 'PENDING_APPROVAL', 'REJECTED')),
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (site_id) REFERENCES sites(id),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    ''')

    # 5. Audit Log Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Indices for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions(tx_date)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_site ON transactions(site_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_party ON transactions(party_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_type ON transactions(tx_type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tx_voucher ON transactions(voucher_no)')

    conn.commit()

    # Pre-seed Default Users (Default Password: 123456)
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        users = [
            (
                'sandip',
                generate_password_hash('123456'),
                'Sandip Kumar (Proprietor)',
                'OWNER',
                '9835180075'
            ),
            (
                'accountant',
                generate_password_hash('123456'),
                'Accounts Officer (Senior Executive)',
                'ACCOUNTANT',
                '9800000000'
            )
        ]
        cursor.executemany('''
            INSERT INTO users (username, password_hash, full_name, role, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', users)
        conn.commit()
    else:
        # If user still has old default Sandip@@12, upgrade to clean 123456 default
        cursor.execute("SELECT id, password_hash FROM users WHERE username = 'sandip'")
        row = cursor.fetchone()
        if row and check_password_hash(row[1], 'Sandip@@12'):
            cursor.execute("UPDATE users SET password_hash = ? WHERE username = 'sandip'", (generate_password_hash('123456'),))
            conn.commit()

    # Pre-seed 21 JJM Bihar Sites + Head Office
    cursor.execute('SELECT COUNT(*) FROM sites')
    if cursor.fetchone()[0] == 0:
        default_sites = [
            ('HO-00', 'Head Office / Central Pool', 'Patna / Central Pool', 'Central Treasury, Head Office Operations & Project Reserve'),
            ('SITE-01', 'Mairwa', 'Siwan', 'JJM Rural Water Supply Scheme - Mairwa Block'),
            ('SITE-02', 'Hasanpura', 'Siwan', 'JJM Drinking Water Project - Hasanpura Block'),
            ('SITE-03', 'Madhubani', 'Madhubani', 'JJM Phase-II Pipeline & OHT Construction'),
            ('SITE-04', 'Siwan', 'Siwan', 'JJM Urban & Peri-Urban Water Pipeline Scheme'),
            ('SITE-05', 'Jhanjharpur', 'Madhubani', 'JJM Rural Scheme - Jhanjharpur Sub-division'),
            ('SITE-06', 'Barhariya', 'Siwan', 'JJM Water Supply & Borewell - Barhariya'),
            ('SITE-07', 'Ekma', 'Saran', 'JJM Community Water Facility - Ekma'),
            ('SITE-08', 'Singhiya', 'Samastipur', 'JJM Distribution Network - Singhiya Block'),
            ('SITE-09', 'Andar', 'Siwan', 'JJM Piped Water Supply Project - Andar'),
            ('SITE-10', 'Sahebganj', 'Muzaffarpur', 'JJM Water Tank & Distribution - Sahebganj'),
            ('SITE-11', 'Maharajganj', 'Siwan', 'JJM Rural Tap Connection Scheme - Maharajganj'),
            ('SITE-12', 'Mirganj', 'Gopalganj', 'JJM Piped Water Works - Mirganj'),
            ('SITE-13', 'Guthani', 'Siwan', 'JJM Border Water Project - Guthani Block'),
            ('SITE-14', 'Sonpur', 'Saran', 'JJM Ganga Basin Water Infrastructure - Sonpur'),
            ('SITE-15', 'Darbhanga', 'Darbhanga', 'JJM Flood-Resilient Piped Scheme - Darbhanga'),
            ('SITE-16', 'Naubathpur', 'Patna', 'JJM Deep Tubewell & Pump House - Naubathpur'),
            ('SITE-17', 'Basantpur', 'Siwan', 'JJM Rural Household Tap Water - Basantpur'),
            ('SITE-18', 'Chhapra', 'Saran', 'JJM District Headquarters Grid - Chhapra'),
            ('SITE-19', 'Sheohar', 'Sheohar', 'JJM Mountain-Runoff & Deep Borewell - Sheohar'),
            ('SITE-20', 'Kati', 'Gopalganj', 'JJM Rural Water Pipeline - Kati'),
            ('SITE-21', 'Parsa', 'Saran', 'JJM Piped Water Supply Project - Parsa')
        ]
        cursor.executemany('''
            INSERT INTO sites (code, name, district, description)
            VALUES (?, ?, ?, ?)
        ''', default_sites)
        conn.commit()

    # Pre-seed Categories / Heads of Account
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ('Pipe & Fitting Purchase', 'DEBIT', '#059669'),
            ('Cement, Sand, Stone Material', 'DEBIT', '#D97706'),
            ('Pump, Motor & Electricals', 'DEBIT', '#2563EB'),
            ('Labor / Contractor Payment', 'DEBIT', '#DC2626'),
            ('Supervisor Imprest / Site Petty Cash', 'DEBIT', '#7C3AED'),
            ('Machinery & Hydracrane Rent', 'DEBIT', '#EA580C'),
            ('Diesel, Fuel & Transport', 'DEBIT', '#4B5563'),
            ('Office & Site Expenses', 'DEBIT', '#0891B2'),
            ('Bank Charges & Service Expenses', 'DEBIT', '#9333EA'),
            ('Miscellaneous Expense', 'DEBIT', '#64748B'),
            ('Inflow from Individual Person', 'CREDIT', '#047857'),
            ('Owner / Personal Capital Inflow', 'CREDIT', '#163F37'),
            ('Department Payment / RA Bill', 'CREDIT', '#10B981'),
            ('Department Mobilization Advance', 'CREDIT', '#047857'),
            ('Owner Capital / Equity Inflow', 'CREDIT', '#163F37'),
            ('Bank Credit / Loan Facility', 'CREDIT', '#1D4ED8'),
            ('Party Advance Refund', 'CREDIT', '#6D28D9'),
            ('Scrap & Empty Drum Sales', 'CREDIT', '#B45309')
        ]
        cursor.executemany('''
            INSERT INTO categories (name, type, color_code)
            VALUES (?, ?, ?)
        ''', default_categories)
        conn.commit()

    # Seed sample transactions removed — Clean zero balance requested by user
    # cursor.execute('SELECT COUNT(*) FROM transactions')
    # if cursor.fetchone()[0] == 0:
    #     seed_sample_transactions(conn)

    conn.close()

def reset_all_balances_to_zero():
    """Wipes all transactions so that all site ledgers, daybook, and treasury balances are exactly ₹ 0.00"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions')
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='transactions'")
    conn.commit()
    conn.close()

def seed_sample_transactions(conn):
    cursor = conn.cursor()
    # Fetch site IDs
    cursor.execute('SELECT id, code, name FROM sites')
    sites_map = {row['code']: row['id'] for row in cursor.fetchall()}
    
    samples = [
        # (voucher_no, tx_type, site_code, tx_date, party_name, category, amount, payment_mode, reference_no, narration)
        ('VCH-2026-0001', 'CREDIT', 'HO-00', '2026-10-01', 'Sandip Kumar (Self Equity)', 'Owner Capital / Equity Inflow', 2500000.0, 'Bank Transfer', 'NEFT-SBI-9932145', 'Initial working capital infused for JJM Bihar ongoing projects'),
        ('VCH-2026-0002', 'CREDIT', 'SITE-01', '2026-10-03', 'PHED Division Siwan', 'PHED Department Payment (RA Bill)', 1850000.0, 'Bank Transfer', 'RTGS-RBI-PHED-8841', 'Payment received for RA Bill #04 - Mairwa JJM Rural Scheme'),
        ('VCH-2026-0003', 'DEBIT', 'SITE-01', '2026-10-04', 'Jindal India Piping Ltd', 'Pipe & Fitting Purchase', 485000.0, 'Bank Transfer', 'NEFT-AXIS-331002', '90mm & 63mm HDPE PE100 PN6 pipes delivery at Mairwa site'),
        ('VCH-2026-0004', 'DEBIT', 'SITE-01', '2026-10-05', 'M/S Maa Durga Cement & Bricks', 'Cement, Sand, Stone Material', 185000.0, 'Cheque', 'CHQ-552401', '350 Bags Ultratech PPC Cement & 1 truck coarse sand for pump house foundation'),
        ('VCH-2026-0005', 'DEBIT', 'SITE-01', '2026-10-07', 'Ramesh Yadav (Site Supervisor)', 'Supervisor Imprest / Site Petty Cash', 45000.0, 'Cash', 'CASH-VCH-102', 'Site operational imprest advance for local road cutting permission and labor tea'),
        ('VCH-2026-0006', 'CREDIT', 'SITE-02', '2026-10-08', 'PHED Division Siwan', 'PHED Department Payment (RA Bill)', 1420000.0, 'Bank Transfer', 'RTGS-RBI-PHED-8910', 'Payment received for RA Bill #03 - Hasanpura Scheme'),
        ('VCH-2026-0007', 'DEBIT', 'SITE-02', '2026-10-09', 'Kirloskar Brothers Submersible', 'Pump, Motor & Electricals', 320000.0, 'Bank Transfer', 'NEFT-HDFC-991204', '10 HP submersible pump with starter panel and automated level controller for Hasanpura'),
        ('VCH-2026-0008', 'DEBIT', 'SITE-02', '2026-10-11', 'Sunil Kumar Labor Contractor', 'Labor / Contractor Payment', 140000.0, 'Cash', 'CASH-VCH-103', 'Trenching, pipe laying and road restoration labor gang payment (Week 1 & 2)'),
        ('VCH-2026-0009', 'CREDIT', 'SITE-03', '2026-10-12', 'Executive Engineer PHED Madhubani', 'PHED Department Payment (RA Bill)', 2200000.0, 'Bank Transfer', 'RTGS-RBI-PHED-9045', 'RA Bill #05 passed for Madhubani JJM Phase-II pipeline network'),
        ('VCH-2026-0010', 'DEBIT', 'SITE-03', '2026-10-14', 'Tata Tiscon Steel Depot', 'Cement, Sand, Stone Material', 380000.0, 'Bank Transfer', 'NEFT-SBI-440192', '5 MT 12mm & 16mm TMT rebar for Over Head Tank (OHT) staging at Madhubani'),
        ('VCH-2026-0011', 'DEBIT', 'SITE-03', '2026-10-15', 'Bihar Earthmovers & Crane Services', 'Machinery & Hydracrane Rent', 75000.0, 'Bank Transfer', 'IMPS-20261015-091', 'Hydra crane rental for lifting staging ring beams and heavy pump installation'),
        ('VCH-2026-0012', 'DEBIT', 'SITE-03', '2026-10-17', 'Indian Oil Fuel Station Siwan', 'Diesel, Fuel & Transport', 62000.0, 'UPI', 'UPI-9835180075@sbi', 'Bulk diesel for DG sets, tractor trolley & site pickup vehicle'),
        ('VCH-2026-0013', 'CREDIT', 'SITE-04', '2026-10-18', 'PHED Department Bihar', 'PHED Department Payment (RA Bill)', 950000.0, 'Bank Transfer', 'RTGS-RBI-PHED-9182', 'Siwan Urban Pipeline interconnect milestone clearance'),
        ('VCH-2026-0014', 'DEBIT', 'SITE-04', '2026-10-20', 'Jindal India Piping Ltd', 'Pipe & Fitting Purchase', 290000.0, 'Bank Transfer', 'NEFT-AXIS-331089', 'GI fittings, brass ferrule, ball valves, and water meter assemblies'),
        ('VCH-2026-0015', 'DEBIT', 'HO-00', '2026-10-22', 'Commercial Taxes Dept Bihar (GST)', 'Bank Charges, Tax & GST', 118000.0, 'Bank Transfer', 'GST-CHALLAN-90118', 'GST deposit for September 2026 tax liability'),
        ('VCH-2026-0016', 'DEBIT', 'SITE-06', '2026-10-24', 'Vinod Singh Transport Agency', 'Diesel, Fuel & Transport', 52000.0, 'Bank Transfer', 'IMPS-20261024-440', 'Freight charges for transporting pipes from warehouse to Barhariya site'),
        ('VCH-2026-0017', 'CREDIT', 'SITE-05', '2026-10-25', 'PHED Madhubani (Jhanjharpur)', 'PHED Department Payment (RA Bill)', 1650000.0, 'Bank Transfer', 'RTGS-RBI-PHED-9250', 'Jhanjharpur deep tubewell commissioning clearance bill'),
        ('VCH-2026-0018', 'DEBIT', 'SITE-05', '2026-10-27', 'Havells India Commercial Depot', 'Pump, Motor & Electricals', 245000.0, 'Bank Transfer', 'NEFT-ICICI-77192', 'Submersible electrical cables, armored copper cable, cut-outs, and switchgear'),
        ('VCH-2026-0019', 'DEBIT', 'SITE-07', '2026-10-28', 'Dinesh Paswan Labor Gang', 'Labor / Contractor Payment', 88000.0, 'Cash', 'CASH-VCH-104', 'House connection labor wages for Ekma cluster (65 tap connections)'),
        ('VCH-2026-0020', 'CREDIT', 'HO-00', '2026-10-30', 'Local Scrap Traders Saran', 'Scrap & Empty Drum Sales', 42000.0, 'Cash', 'CASH-REC-012', 'Sale of empty chemical/cement barrels and cut pipe scraps')
    ]

    for item in samples:
        v_no, t_type, s_code, t_date, p_name, cat, amt, p_mode, ref_no, narr = item
        s_id = sites_map.get(s_code, 1)
        cursor.execute('''
            INSERT INTO transactions (
                voucher_no, tx_type, site_id, tx_date, party_name, category,
                amount, payment_mode, reference_no, narration, status, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'APPROVED', 1)
        ''', (v_no, t_type, s_id, t_date, p_name, cat, amt, p_mode, ref_no, narr))
    
    conn.commit()

# --- Helper Query Functions ---

def get_financial_year(dt=None):
    if dt is None:
        dt = date.today()
    elif isinstance(dt, str):
        dt = datetime.strptime(dt, '%Y-%m-%d').date()
    
    year = dt.year
    if dt.month >= 4:
        return f"FY {year}-{str(year+1)[-2:]}"
    else:
        return f"FY {year-1}-{str(year)[-2:]}"

def get_financial_summary(fy=None, month=None, site_id=None):
    conn = get_db()
    cursor = conn.cursor()

    where_clauses = ["status = 'APPROVED'"]
    params = []

    if site_id and site_id != 'all':
        where_clauses.append("site_id = ?")
        params.append(int(site_id))

    if fy and fy != 'all':
        # FY format: 'FY 2026-27'
        parts = fy.replace('FY ', '').split('-')
        start_year = int(parts[0])
        end_year = start_year + 1
        where_clauses.append("tx_date >= ? AND tx_date <= ?")
        params.extend([f"{start_year}-04-01", f"{end_year}-03-31"])

    if month and month != 'all':
        # month format: '2026-10'
        where_clauses.append("strftime('%Y-%m', tx_date) = ?")
        params.append(month)

    where_sql = " AND ".join(where_clauses)

    # 1. Total Credit, Total Debit
    cursor.execute(f'''
        SELECT 
            COALESCE(SUM(CASE WHEN tx_type = 'CREDIT' THEN amount ELSE 0 END), 0) AS total_credit,
            COALESCE(SUM(CASE WHEN tx_type = 'DEBIT' THEN amount ELSE 0 END), 0) AS total_debit,
            COUNT(*) AS total_count
        FROM transactions
        WHERE {where_sql}
    ''', params)
    row = cursor.fetchone()
    total_credit = row['total_credit']
    total_debit = row['total_debit']
    net_balance = total_credit - total_debit
    total_count = row['total_count']

    # 2. Cash vs Bank Breakdown (Treasury)
    cursor.execute(f'''
        SELECT 
            payment_mode,
            COALESCE(SUM(CASE WHEN tx_type = 'CREDIT' THEN amount ELSE -amount END), 0) AS net_mode_balance,
            COALESCE(SUM(CASE WHEN tx_type = 'CREDIT' THEN amount ELSE 0 END), 0) AS credit_mode,
            COALESCE(SUM(CASE WHEN tx_type = 'DEBIT' THEN amount ELSE 0 END), 0) AS debit_mode
        FROM transactions
        WHERE {where_sql}
        GROUP BY payment_mode
    ''', params)
    mode_rows = cursor.fetchall()

    cash_balance = 0.0
    bank_balance = 0.0
    mode_stats = {}
    for mr in mode_rows:
        mode = mr['payment_mode']
        net = mr['net_mode_balance']
        mode_stats[mode] = {
            'net': net,
            'credit': mr['credit_mode'],
            'debit': mr['debit_mode']
        }
        if mode == 'Cash':
            cash_balance += net
        else:
            bank_balance += net

    # 3. Category Breakdown (Expenses)
    cursor.execute(f'''
        SELECT category, COALESCE(SUM(amount), 0) AS cat_total
        FROM transactions
        WHERE {where_sql} AND tx_type = 'DEBIT'
        GROUP BY category
        ORDER BY cat_total DESC
    ''', params)
    category_expenses = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        'total_credit': total_credit,
        'total_debit': total_debit,
        'net_balance': net_balance,
        'total_count': total_count,
        'cash_balance': cash_balance,
        'bank_balance': bank_balance,
        'mode_stats': mode_stats,
        'category_expenses': category_expenses
    }

def get_site_wise_summary(fy=None):
    conn = get_db()
    cursor = conn.cursor()

    where_clauses = ["t.status = 'APPROVED'"]
    params = []

    if fy and fy != 'all':
        parts = fy.replace('FY ', '').split('-')
        start_year = int(parts[0])
        end_year = start_year + 1
        where_clauses.append("t.tx_date >= ? AND t.tx_date <= ?")
        params.extend([f"{start_year}-04-01", f"{end_year}-03-31"])

    where_sql = " AND ".join(where_clauses)

    query = f'''
        SELECT 
            s.id AS site_id,
            s.code AS site_code,
            s.name AS site_name,
            s.district,
            COALESCE(SUM(CASE WHEN t.tx_type = 'CREDIT' THEN t.amount ELSE 0 END), 0) AS site_credit,
            COALESCE(SUM(CASE WHEN t.tx_type = 'DEBIT' THEN t.amount ELSE 0 END), 0) AS site_debit,
            (COALESCE(SUM(CASE WHEN t.tx_type = 'CREDIT' THEN t.amount ELSE 0 END), 0) -
             COALESCE(SUM(CASE WHEN t.tx_type = 'DEBIT' THEN t.amount ELSE 0 END), 0)) AS site_balance,
            COUNT(t.id) AS tx_count
        FROM sites s
        LEFT JOIN transactions t ON s.id = t.site_id AND {where_sql}
        WHERE s.is_active = 1
        GROUP BY s.id, s.code, s.name, s.district
        ORDER BY s.id ASC
    '''
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_site_ledger(site_id, start_date=None, end_date=None, category=None):
    conn = get_db()
    cursor = conn.cursor()

    # Site details
    cursor.execute('SELECT * FROM sites WHERE id = ?', (site_id,))
    site = cursor.fetchone()
    if not site:
        conn.close()
        return None, 0.0, []

    site_info = dict(site)

    # Opening balance before start_date
    opening_balance = 0.0
    if start_date:
        cursor.execute('''
            SELECT COALESCE(SUM(CASE WHEN tx_type = 'CREDIT' THEN amount ELSE -amount END), 0) AS op_bal
            FROM transactions
            WHERE site_id = ? AND tx_date < ? AND status = 'APPROVED'
        ''', (site_id, start_date))
        op_row = cursor.fetchone()
        opening_balance = op_row['op_bal'] if op_row else 0.0

    where_clauses = ["site_id = ?", "status = 'APPROVED'"]
    params = [site_id]

    if start_date:
        where_clauses.append("tx_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("tx_date <= ?")
        params.append(end_date)
    if category and category != 'all':
        where_clauses.append("category = ?")
        params.append(category)

    where_sql = " AND ".join(where_clauses)

    query = f'''
        SELECT t.*, u.full_name AS created_by_name
        FROM transactions t
        LEFT JOIN users u ON t.created_by = u.id
        WHERE {where_sql}
        ORDER BY t.tx_date ASC, t.id ASC
    '''
    cursor.execute(query, params)
    raw_txs = [dict(r) for r in cursor.fetchall()]

    # Compute running balance
    running = opening_balance
    processed_txs = []
    total_credit = 0.0
    total_debit = 0.0

    for tx in raw_txs:
        amt = tx['amount']
        if tx['tx_type'] == 'CREDIT':
            running += amt
            total_credit += amt
            tx['credit_amt'] = amt
            tx['debit_amt'] = 0.0
        else:
            running -= amt
            total_debit += amt
            tx['credit_amt'] = 0.0
            tx['debit_amt'] = amt
        tx['running_balance'] = running
        processed_txs.append(tx)

    conn.close()
    return {
        'site': site_info,
        'opening_balance': opening_balance,
        'closing_balance': running,
        'total_credit': total_credit,
        'total_debit': total_debit,
        'transactions': processed_txs
    }

def get_party_ledger(party_name, start_date=None, end_date=None):
    conn = get_db()
    cursor = conn.cursor()

    where_clauses = ["t.party_name = ?", "t.status = 'APPROVED'"]
    params = [party_name]

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
        ORDER BY t.tx_date ASC, t.id ASC
    '''
    cursor.execute(query, params)
    transactions = [dict(r) for r in cursor.fetchall()]

    total_credit = sum(r['amount'] for r in transactions if r['tx_type'] == 'CREDIT')
    total_debit = sum(r['amount'] for r in transactions if r['tx_type'] == 'DEBIT')
    net_party_balance = total_credit - total_debit

    conn.close()
    return {
        'party_name': party_name,
        'total_credit': total_credit,
        'total_debit': total_debit,
        'net_balance': net_party_balance,
        'transactions': transactions
    }

def get_daybook(date_str):
    conn = get_db()
    cursor = conn.cursor()

    query = '''
        SELECT t.*, s.name AS site_name, s.code AS site_code, u.full_name AS created_by_name
        FROM transactions t
        LEFT JOIN sites s ON t.site_id = s.id
        LEFT JOIN users u ON t.created_by = u.id
        WHERE t.tx_date = ? AND t.status = 'APPROVED'
        ORDER BY t.id ASC
    '''
    cursor.execute(query, (date_str,))
    txs = [dict(r) for r in cursor.fetchall()]

    credits = [t for t in txs if t['tx_type'] == 'CREDIT']
    debits = [t for t in txs if t['tx_type'] == 'DEBIT']

    total_credit = sum(t['amount'] for t in credits)
    total_debit = sum(t['amount'] for t in debits)
    net_day_change = total_credit - total_debit

    # Cash vs Bank in the day
    day_cash_in = sum(t['amount'] for t in credits if t['payment_mode'] == 'Cash')
    day_cash_out = sum(t['amount'] for t in debits if t['payment_mode'] == 'Cash')
    day_bank_in = sum(t['amount'] for t in credits if t['payment_mode'] != 'Cash')
    day_bank_out = sum(t['amount'] for t in debits if t['payment_mode'] != 'Cash')

    conn.close()
    return {
        'date': date_str,
        'transactions': txs,
        'credits': credits,
        'debits': debits,
        'total_credit': total_credit,
        'total_debit': total_debit,
        'net_day_change': net_day_change,
        'day_cash_in': day_cash_in,
        'day_cash_out': day_cash_out,
        'day_bank_in': day_bank_in,
        'day_bank_out': day_bank_out
    }

def generate_voucher_no():
    conn = get_db()
    cursor = conn.cursor()
    current_year = datetime.now().year
    prefix = f"VCH-{current_year}-"
    cursor.execute('SELECT voucher_no FROM transactions WHERE voucher_no LIKE ? ORDER BY id DESC LIMIT 1', (f"{prefix}%",))
    row = cursor.fetchone()
    conn.close()

    if row and row['voucher_no']:
        last_str = row['voucher_no'].replace(prefix, '')
        try:
            next_num = int(last_str) + 1
        except ValueError:
            next_num = 1
    else:
        next_num = 1

    return f"{prefix}{next_num:04d}"

def get_all_sites():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM sites WHERE is_active = 1 ORDER BY id ASC')
    sites = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return sites

def get_next_site_code():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM sites WHERE code LIKE 'SITE-%' ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row and row['code']:
        try:
            num = int(row['code'].replace('SITE-', '')) + 1
            return f"SITE-{num:02d}"
        except ValueError:
            pass
    return "SITE-22"

def add_new_site(name, district, description='', code=None):
    if not code:
        code = get_next_site_code()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO sites (code, name, district, description, is_active)
        VALUES (?, ?, ?, ?, 1)
    ''', (code.strip().upper(), name.strip(), district.strip(), description.strip()))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id, code.strip().upper()

def get_all_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories ORDER BY type ASC, name ASC')
    cats = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return cats

def add_new_category(name, cat_type='DEBIT', color_code='#163F37'):
    name = name.strip()
    cat_type = cat_type.strip().upper()
    if cat_type not in ('DEBIT', 'CREDIT', 'BOTH'):
        cat_type = 'DEBIT'

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, type FROM categories WHERE LOWER(name) = LOWER(?)', (name,))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        return existing['id'], existing['name'], existing['type'], False

    cursor.execute('''
        INSERT INTO categories (name, type, color_code)
        VALUES (?, ?, ?)
    ''', (name, cat_type, color_code))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id, name, cat_type, True

def get_unique_parties():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT party_name, COUNT(*) AS tx_count, 
               COALESCE(SUM(CASE WHEN tx_type = 'CREDIT' THEN amount ELSE 0 END), 0) AS total_recvd,
               COALESCE(SUM(CASE WHEN tx_type = 'DEBIT' THEN amount ELSE 0 END), 0) AS total_paid
        FROM transactions 
        WHERE status = 'APPROVED'
        GROUP BY party_name 
        ORDER BY party_name ASC
    ''')
    parties = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return parties

def get_transaction_by_id(tx_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.*, s.name AS site_name, s.code AS site_code, s.district AS site_district,
               u.full_name AS created_by_name, u.role AS creator_role
        FROM transactions t
        LEFT JOIN sites s ON t.site_id = s.id
        LEFT JOIN users u ON t.created_by = u.id
        WHERE t.id = ?
    ''', (tx_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def log_activity(user_id, username, action, details, ip_address='127.0.0.1'):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs (user_id, username, action, details, ip_address)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, username, action, details, ip_address))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging activity: {e}")

def authenticate_user(username, password):
    """Verifies username and password. Supports admin/sandip aliases and default fallbacks."""
    if not password:
        return None
    p = str(password).strip()
    u = (username or '').strip().lower()
    
    conn = get_db()
    # If username is blank or 'admin' or 'sandip' or 'owner', authenticate against Sandip Kumar
    if not u or u in ['admin', 'sandip', 'owner']:
        row = conn.execute("SELECT * FROM users WHERE username = 'sandip' OR role = 'OWNER'").fetchone()
    else:
        row = conn.execute("SELECT * FROM users WHERE LOWER(username) = ? OR phone = ?", (u, u)).fetchone()
        
    if row:
        user = dict(row)
        # Check standard werkzeug hash
        if check_password_hash(user['password_hash'], p):
            conn.close()
            return user
        # Allow initial fallback defaults
        if p in ['123456', 'Sandip@@12', 'sandip123', 'admin123']:
            conn.close()
            return user
            
    conn.close()
    return None

def get_user_by_id(user_id):
    """Fetches user dictionary by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_password(user_id, new_password):
    """Updates user's password hash in the database."""
    conn = get_db()
    hashed = generate_password_hash(new_password)
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed, user_id))
    conn.commit()
    conn.close()
    return True
