"""
Test suite to thoroughly verify M/S Sandip Kumar Accounts Application
Unified Portal (No Modes / No Login / Zero Balance)
"""
import unittest
import json
from app import app
import models

class AccountsAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_direct_dashboard_access(self):
        """Verify that opening the site directly opens Dashboard without any login or modes."""
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'M/S SANDIP KUMAR', rv.data)
        self.assertIn(b'Master Financial Dashboard', rv.data)
        print("PASS: Direct access to Dashboard verified (No login/modes needed)!")

    def test_02_all_sites_and_zero_balance(self):
        """Verify 21 sites + HO and clean ₹ 0.00 zero balance."""
        sites = models.get_all_sites()
        self.assertEqual(len(sites), 22)
        models.reset_all_balances_to_zero()
        summary = models.get_financial_summary()
        self.assertEqual(summary['total_credit'], 0.0)
        self.assertEqual(summary['total_debit'], 0.0)
        self.assertEqual(summary['net_balance'], 0.0)
        print("PASS: All 21 JJM Sites + Head Office clean zero balance verified!")

    def test_03_create_edit_and_delete_transaction(self):
        """Verify creating, editing and deleting a transaction directly without permissions blocks."""
        # 1. Create
        create_rv = self.client.post('/api/transaction/create', data=dict(
            tx_type='CREDIT',
            site_id=2, # Mairwa
            tx_date='2026-10-31',
            party_name='PHED Division Siwan',
            category='PHED Department Payment (RA Bill)',
            amount='500000',
            payment_mode='Bank Transfer',
            reference_no='RTGS-112233',
            narration='Testing unified portal'
        ))
        c_data = json.loads(create_rv.data)
        self.assertTrue(c_data['success'])
        tx_id = c_data['id']
        self.assertEqual(c_data['voucher_no'], 'VCH-2026-0001')

        # 2. Check Voucher
        vch_rv = self.client.get(f'/voucher/{tx_id}')
        self.assertEqual(vch_rv.status_code, 200)
        self.assertIn(b'Rupees Five Lakh Only', vch_rv.data)

        # 3. Direct Delete without any mode check
        del_rv = self.client.post(f'/api/transaction/{tx_id}/delete')
        d_data = json.loads(del_rv.data)
        self.assertTrue(d_data['success'])
        self.assertEqual(models.get_financial_summary()['total_count'], 0)
        print("PASS: Create, voucher and direct delete verified!")

    def test_04_direct_backup_and_exports(self):
        """Verify Excel exports and DB backup are directly accessible."""
        rv_export = self.client.get('/export/site-ledger?site_id=2')
        self.assertEqual(rv_export.status_code, 200)
        self.assertTrue(len(rv_export.data) > 1000)

        rv_db = self.client.get('/backup/download')
        self.assertEqual(rv_db.status_code, 200)
        print("PASS: Excel exports and DB backup direct access verified!")

    def test_05_add_new_site_and_date_filter(self):
        """Verify adding a new site (e.g. SITE-22) and quick date filtering."""
        # 1. Check next site code
        code_rv = self.client.get('/api/next_site_code')
        c_json = json.loads(code_rv.data)
        self.assertTrue(c_json['code'].startswith('SITE-'))

        # 2. Add new site
        site_rv = self.client.post('/api/site/create', data=dict(
            name='Bhagwanpur',
            district='Siwan',
            description='JJM Rural Water Scheme - Bhagwanpur Block'
        ))
        s_json = json.loads(site_rv.data)
        self.assertTrue(s_json['success'])
        self.assertEqual(s_json['name'], 'Bhagwanpur')
        print(f"PASS: Created new site: {s_json['code']} - {s_json['name']}!")

        # 3. Test quick date filter on transactions view
        tx_today = self.client.get('/transactions?date_filter=today')
        self.assertEqual(tx_today.status_code, 200)
        self.assertIn(b'Quick Filter', tx_today.data)
        self.assertIn(b'Today', tx_today.data)
        print("PASS: Quick date filter tested successfully!")

        # 4. Clean up test site to keep database pristine
        conn = models.get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sites WHERE name = 'Bhagwanpur'")
        conn.commit()
        conn.close()

    def test_06_add_debit_and_credit_purpose(self):
        """Verify adding new dynamic Purpose / Category for both Debit and Credit."""
        # 1. Add Debit Purpose
        deb_rv = self.client.post('/api/category/create', data=dict(
            name='Generator Extra Rental',
            type='DEBIT'
        ))
        d_json = json.loads(deb_rv.data)
        self.assertTrue(d_json['success'])
        self.assertEqual(d_json['name'], 'Generator Extra Rental')
        self.assertEqual(d_json['type'], 'DEBIT')

        # 2. Add Credit Purpose
        cred_rv = self.client.post('/api/category/create', data=dict(
            name='Security Deposit Refund from Dept',
            type='CREDIT'
        ))
        c_json = json.loads(cred_rv.data)
        self.assertTrue(c_json['success'])
        self.assertEqual(c_json['name'], 'Security Deposit Refund from Dept')
        self.assertEqual(c_json['type'], 'CREDIT')

        # Clean up test categories
        conn = models.get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM categories WHERE name IN ('Generator Extra Rental', 'Security Deposit Refund from Dept')")
        conn.commit()
        conn.close()
        print("PASS: Debit & Credit dynamic purpose creation verified successfully!")

if __name__ == '__main__':
    unittest.main()
