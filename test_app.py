"""
Test suite to thoroughly verify M/S Sandip Kumar Accounts Application
Password Protection & Live In-App Password Change Functionality
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

    def login_client(self, username='admin', password='123456'):
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)

    def test_01_unauthenticated_redirect_to_login(self):
        """Verify unauthenticated user is redirected to /login with password prompt."""
        rv = self.client.get('/')
        self.assertEqual(rv.status_code, 302)
        self.assertIn('/login', rv.headers['Location'])
        
        login_page = self.client.get('/login')
        self.assertEqual(login_page.status_code, 200)
        self.assertIn(b'MS SANDIP KUMAR', login_page.data)
        self.assertIn(b'123456', login_page.data)
        print("PASS: Unauthenticated redirect to /login verified!")

    def test_02_login_failure_and_success(self):
        """Verify login rejects wrong password and accepts valid password."""
        # Wrong password
        rv_fail = self.client.post('/login', data=dict(
            username='admin',
            password='wrongpassword'
        ))
        self.assertEqual(rv_fail.status_code, 200)
        self.assertIn('गलत पासवर्ड'.encode('utf-8'), rv_fail.data)
        
        # Valid password (default 123456)
        rv_success = self.client.post('/login', data=dict(
            username='admin',
            password='123456'
        ), follow_redirects=True)
        self.assertEqual(rv_success.status_code, 200)
        self.assertIn(b'Master Financial Dashboard', rv_success.data)
        print("PASS: Password authentication (fail and success) verified!")

    def test_03_in_app_password_change(self):
        """Verify user can change password inside the portal via /api/change-password."""
        # Login first
        self.login_client()
        
        # 1. Test wrong old password
        rv = self.client.post('/api/change-password', data=dict(
            old_password='bad_old_pass',
            new_password='newpass_secret',
            confirm_password='newpass_secret'
        ))
        data = json.loads(rv.data)
        self.assertFalse(data['success'])
        
        # 2. Test mismatched confirm password
        rv = self.client.post('/api/change-password', data=dict(
            old_password='123456',
            new_password='newpass_secret',
            confirm_password='different_pass'
        ))
        data = json.loads(rv.data)
        self.assertFalse(data['success'])
        
        # 3. Test successful password change
        rv = self.client.post('/api/change-password', data=dict(
            old_password='123456',
            new_password='newpass_secret',
            confirm_password='newpass_secret'
        ))
        data = json.loads(rv.data)
        self.assertTrue(data['success'])
        
        # 4. Verify new password works on login
        self.client.get('/logout')
        rv_new_login = self.client.post('/login', data=dict(
            username='sandip',
            password='newpass_secret'
        ), follow_redirects=True)
        self.assertEqual(rv_new_login.status_code, 200)
        self.assertIn(b'Master Financial Dashboard', rv_new_login.data)
        
        # 5. CRITICAL SECURITY TEST: Verify old password (123456) is completely REJECTED
        self.client.get('/logout')
        rv_old_login = self.client.post('/login', data=dict(
            username='sandip',
            password='123456'
        ), follow_redirects=True)
        self.assertEqual(rv_old_login.status_code, 200)
        self.assertIn('गलत पासवर्ड'.encode('utf-8'), rv_old_login.data)
        self.assertNotIn(b'Master Financial Dashboard', rv_old_login.data)
        
        # Reset back to 123456 so default tests continue smoothly
        models.update_user_password(1, '123456')
        print("PASS: In-app password change verified end-to-end (old password strictly blocked)!")

    def test_04_create_edit_and_delete_transaction(self):
        """Verify authenticated user can perform full transaction lifecycle."""
        self.login_client()
        
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
            narration='Testing password protected portal'
        ))
        c_data = json.loads(create_rv.data)
        self.assertTrue(c_data['success'])
        tx_id = c_data['id']

        # 2. Check Voucher
        vch_rv = self.client.get(f'/voucher/{tx_id}')
        self.assertEqual(vch_rv.status_code, 200)
        self.assertIn(b'Rupees Five Lakh Only', vch_rv.data)

        # 3. Direct Delete
        del_rv = self.client.post(f'/api/transaction/{tx_id}/delete')
        d_data = json.loads(del_rv.data)
        self.assertTrue(d_data['success'])
        print("PASS: Authenticated transaction lifecycle verified!")

    def test_05_dynamic_categories(self):
        """Verify dynamic purpose/category creation."""
        self.login_client()
        res = self.client.post('/api/category/create', data=dict(
            name='Diesel Generator Fuel Test',
            type='DEBIT'
        ))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        print("PASS: Dynamic category creation verified!")

    def test_06_firm_settings_update(self):
        """Verify updating firm name and details reflects in settings."""
        self.login_client()
        res = self.client.post('/api/firm-settings/update', data=dict(
            firm_name='MS SANDIP KUMAR',
            firm_subtitle='Jal Jeevan Mission, Bihar Contractor',
            logo_initials='SK'
        ))
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        
        settings = models.get_firm_settings()
        self.assertEqual(settings['firm_name'], 'MS SANDIP KUMAR')
        print("PASS: Firm settings update verified!")

    def test_07_full_page_password_change(self):
        """Verify dedicated /change-password full page GET and POST flow."""
        self.login_client()
        # 1. GET page
        get_rv = self.client.get('/change-password')
        self.assertEqual(get_rv.status_code, 200)
        self.assertIn('पोर्टल पासवर्ड बदलें'.encode('utf-8'), get_rv.data)
        
        # 2. POST password update
        post_rv = self.client.post('/change-password', data=dict(
            old_password='', # empty old password test
            new_password='phone_new_pass',
            confirm_password='phone_new_pass'
        ), follow_redirects=True)
        self.assertEqual(post_rv.status_code, 200)
        self.assertIn(b'Master Financial Dashboard', post_rv.data)
        
        # 3. Verify old password (123456) is rejected
        self.client.get('/logout')
        rv_old_login = self.client.post('/login', data=dict(
            username='sandip',
            password='123456'
        ), follow_redirects=True)
        self.assertEqual(rv_old_login.status_code, 200)
        self.assertIn('गलत पासवर्ड'.encode('utf-8'), rv_old_login.data)
        self.assertNotIn(b'Master Financial Dashboard', rv_old_login.data)
        
        # 4. Verify new password works
        rv_new_login = self.client.post('/login', data=dict(
            username='sandip',
            password='phone_new_pass'
        ), follow_redirects=True)
        self.assertEqual(rv_new_login.status_code, 200)
        self.assertIn(b'Master Financial Dashboard', rv_new_login.data)
        
        # Reset back to 123456
        models.update_user_password(1, '123456')
        print("PASS: Dedicated /change-password full page flow verified (old password blocked)!")

if __name__ == '__main__':
    unittest.main()
