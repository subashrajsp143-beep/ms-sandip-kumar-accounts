import io
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Color constants (Executive Deep Pine Palette)
PINE_DARK = "163F37"
PINE_LIGHT = "EAF5EF"
ACCENT_AMBER = "D97706"
GRAY_LIGHT = "F3F4F6"
BORDER_GRAY = "D1D5DB"

def get_current_firm_name():
    try:
        import models
        return models.get_firm_settings().get('firm_name', 'MS SANDIP KUMAR')
    except Exception:
        return 'MS SANDIP KUMAR'

def apply_header_style(cell, text, bg_color=PINE_DARK, text_color="FFFFFF", font_size=11, bold=True):
    cell.value = text
    cell.font = Font(name="Calibri", size=font_size, bold=bold, color=text_color)
    cell.fill = PatternFill(start_color=bg_color, end_color=bg_color, fill_type="solid")
    cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

def apply_cell_border(cell):
    thin = Side(border_style="thin", color=BORDER_GRAY)
    cell.border = Border(top=thin, left=thin, right=thin, bottom=thin)

def auto_fit_columns(ws, max_widths=None):
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        max_len = 0
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len and "\n" not in val_str:
                max_len = len(val_str)
        width = max(max_len + 3, 11)
        if max_widths and col_letter in max_widths:
            width = min(width, max_widths[col_letter])
        ws.column_dimensions[col_letter].width = width

def export_site_ledger_to_excel(site_ledger_data):
    """Generates an Excel workbook for a Site's detailed ledger."""
    wb = openpyxl.Workbook()
    ws = wb.active
    site = site_ledger_data['site']
    ws.title = f"{site['code']}_Ledger"
    ws.views.sheetView[0].showGridLines = True

    # 1. Main Title
    ws.merge_cells("A1:J1")
    title_cell = ws["A1"]
    title_cell.value = f"{get_current_firm_name()} — JAL JEEVAN MISSION BIHAR"
    title_cell.font = Font(name="Calibri", size=15, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # 2. Subtitle: Site Info
    ws.merge_cells("A2:J2")
    sub_cell = ws["A2"]
    sub_cell.value = f"SITE STATEMENT OF ACCOUNT: {site['code']} - {site['name']} ({site['district']} District)"
    sub_cell.font = Font(name="Calibri", size=12, bold=True, color="163F37")
    sub_cell.fill = PatternFill(start_color=PINE_LIGHT, end_color=PINE_LIGHT, fill_type="solid")
    sub_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 24

    # 3. Meta Row
    ws.merge_cells("A3:J3")
    meta_cell = ws["A3"]
    now_str = datetime.now().strftime("%d-%b-%Y %I:%M %p")
    meta_cell.value = f"Generated On: {now_str} | Opening Balance: ₹ {site_ledger_data['opening_balance']:,.2f} | Closing Balance: ₹ {site_ledger_data['closing_balance']:,.2f}"
    meta_cell.font = Font(name="Calibri", size=10, italic=True, color="4B5563")
    meta_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[3].height = 18

    # Blank Row 4
    ws.row_dimensions[4].height = 10

    # 4. Table Headers
    headers = [
        "S.No", "Date", "Voucher No", "Category / Head", "Party / Description",
        "Ref / UTR / Cheque", "Mode", "Credit (₹) [Amdani]", "Debit (₹) [Kharcha]", "Running Balance (₹)"
    ]
    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=5, column=col_idx)
        apply_header_style(cell, header, bg_color="1F2937", text_color="FFFFFF", font_size=10, bold=True)
        apply_cell_border(cell)
    ws.row_dimensions[5].height = 26

    # 5. Opening Balance Row
    ws.cell(row=6, column=1, value="—")
    ws.cell(row=6, column=2, value="—")
    ws.cell(row=6, column=3, value="OP-BAL")
    ws.cell(row=6, column=4, value="Opening Balance B/F")
    ws.cell(row=6, column=5, value="Site Ledger Initial Balance")
    ws.cell(row=6, column=6, value="—")
    ws.cell(row=6, column=7, value="—")
    ws.cell(row=6, column=8, value=0.0).number_format = "#,##0.00"
    ws.cell(row=6, column=9, value=0.0).number_format = "#,##0.00"
    bal_cell = ws.cell(row=6, column=10, value=site_ledger_data['opening_balance'])
    bal_cell.number_format = "#,##0.00"
    bal_cell.font = Font(bold=True)
    for c in range(1, 11):
        cell = ws.cell(row=6, column=c)
        cell.fill = PatternFill(start_color=GRAY_LIGHT, end_color=GRAY_LIGHT, fill_type="solid")
        apply_cell_border(cell)
    ws.row_dimensions[6].height = 20

    current_row = 7
    s_no = 1
    for tx in site_ledger_data['transactions']:
        ws.cell(row=current_row, column=1, value=s_no).alignment = Alignment(horizontal="center")
        ws.cell(row=current_row, column=2, value=tx['tx_date']).alignment = Alignment(horizontal="center")
        ws.cell(row=current_row, column=3, value=tx['voucher_no']).alignment = Alignment(horizontal="center")
        ws.cell(row=current_row, column=4, value=tx['category'])
        ws.cell(row=current_row, column=5, value=f"{tx['party_name']} - {tx['narration'] or ''}".strip(" -"))
        ws.cell(row=current_row, column=6, value=tx['reference_no'] or "—").alignment = Alignment(horizontal="center")
        ws.cell(row=current_row, column=7, value=tx['payment_mode']).alignment = Alignment(horizontal="center")

        cr_cell = ws.cell(row=current_row, column=8, value=tx['credit_amt'])
        cr_cell.number_format = "#,##0.00"
        if tx['credit_amt'] > 0:
            cr_cell.font = Font(color="059669", bold=True)

        dr_cell = ws.cell(row=current_row, column=9, value=tx['debit_amt'])
        dr_cell.number_format = "#,##0.00"
        if tx['debit_amt'] > 0:
            dr_cell.font = Font(color="DC2626", bold=True)

        run_cell = ws.cell(row=current_row, column=10, value=tx['running_balance'])
        run_cell.number_format = "#,##0.00"
        run_cell.font = Font(bold=True)

        for c in range(1, 11):
            apply_cell_border(ws.cell(row=current_row, column=c))

        ws.row_dimensions[current_row].height = 20
        current_row += 1
        s_no += 1

    # Total Row
    total_row = current_row
    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=7)
    tot_label = ws.cell(row=total_row, column=1, value="TOTAL & CLOSING BALANCE")
    tot_label.font = Font(bold=True, color="FFFFFF")
    tot_label.alignment = Alignment(horizontal="right", vertical="center")
    tot_label.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")

    tot_cr = ws.cell(row=total_row, column=8, value=site_ledger_data['total_credit'])
    tot_cr.number_format = "#,##0.00"
    tot_cr.font = Font(bold=True, color="FFFFFF")
    tot_cr.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")

    tot_dr = ws.cell(row=total_row, column=9, value=site_ledger_data['total_debit'])
    tot_dr.number_format = "#,##0.00"
    tot_dr.font = Font(bold=True, color="FFFFFF")
    tot_dr.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")

    tot_bal = ws.cell(row=total_row, column=10, value=site_ledger_data['closing_balance'])
    tot_bal.number_format = "#,##0.00"
    tot_bal.font = Font(bold=True, color="FFFFFF")
    tot_bal.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")

    for c in range(1, 11):
        apply_cell_border(ws.cell(row=total_row, column=c))
    ws.row_dimensions[total_row].height = 24

    auto_fit_columns(ws, max_widths={'D': 25, 'E': 38})
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def export_party_ledger_to_excel(party_data):
    """Generates an Excel workbook for a Vendor / Party ledger."""
    wb = openpyxl.Workbook()
    ws = wb.active
    p_name = party_data['party_name']
    ws.title = "Party_Khata"
    ws.views.sheetView[0].showGridLines = True

    # Main Title
    ws.merge_cells("A1:I1")
    t = ws["A1"]
    t.value = f"{get_current_firm_name()} — VENDOR & PARTY KHATA STATEMENT"
    t.font = Font(name="Calibri", size=14, bold=True, color="FFFFFF")
    t.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # Subtitle
    ws.merge_cells("A2:I2")
    s = ws["A2"]
    s.value = f"PARTY / VENDOR: {p_name} | Net Settlement / Balance: ₹ {party_data['net_balance']:,.2f}"
    s.font = Font(name="Calibri", size=11, bold=True, color="163F37")
    s.fill = PatternFill(start_color=PINE_LIGHT, end_color=PINE_LIGHT, fill_type="solid")
    s.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    headers = [
        "S.No", "Date", "Voucher No", "Site", "Category / Head",
        "Payment Mode", "Ref / UTR", "Credit / Inflow (₹)", "Debit / Outflow (₹)"
    ]
    for col_idx, h in enumerate(headers, start=1):
        c = ws.cell(row=4, column=col_idx)
        apply_header_style(c, h, bg_color="1F2937", text_color="FFFFFF", font_size=10, bold=True)
        apply_cell_border(c)
    ws.row_dimensions[4].height = 24

    row = 5
    for idx, tx in enumerate(party_data['transactions'], start=1):
        ws.cell(row=row, column=1, value=idx).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=2, value=tx['tx_date']).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=3, value=tx['voucher_no']).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=4, value=f"{tx['site_code']} - {tx['site_name']}")
        ws.cell(row=row, column=5, value=tx['category'])
        ws.cell(row=row, column=6, value=tx['payment_mode']).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=7, value=tx['reference_no'] or "—").alignment = Alignment(horizontal="center")

        cr = tx['amount'] if tx['tx_type'] == 'CREDIT' else 0.0
        dr = tx['amount'] if tx['tx_type'] == 'DEBIT' else 0.0

        c_cr = ws.cell(row=row, column=8, value=cr)
        c_cr.number_format = "#,##0.00"
        if cr > 0:
            c_cr.font = Font(color="059669", bold=True)

        c_dr = ws.cell(row=row, column=9, value=dr)
        c_dr.number_format = "#,##0.00"
        if dr > 0:
            c_dr.font = Font(color="DC2626", bold=True)

        for col_idx in range(1, 10):
            apply_cell_border(ws.cell(row=row, column=col_idx))
        ws.row_dimensions[row].height = 20
        row += 1

    # Total Row
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=7)
    tot = ws.cell(row=row, column=1, value="TOTAL")
    tot.font = Font(bold=True, color="FFFFFF")
    tot.alignment = Alignment(horizontal="right", vertical="center")
    tot.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")

    tot_cr = ws.cell(row=row, column=8, value=party_data['total_credit'])
    tot_cr.number_format = "#,##0.00"
    tot_cr.font = Font(bold=True, color="FFFFFF")
    tot_cr.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")

    tot_dr = ws.cell(row=row, column=9, value=party_data['total_debit'])
    tot_dr.number_format = "#,##0.00"
    tot_dr.font = Font(bold=True, color="FFFFFF")
    tot_dr.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")

    for col_idx in range(1, 10):
        apply_cell_border(ws.cell(row=row, column=col_idx))
    ws.row_dimensions[row].height = 24

    auto_fit_columns(ws, max_widths={'D': 24, 'E': 26})
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf

def export_daybook_to_excel(daybook_data):
    """Generates an Excel workbook for the Daybook (Daily Cashflow)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Daybook"
    ws.views.sheetView[0].showGridLines = True

    # Main Title
    ws.merge_cells("A1:H1")
    t = ws["A1"]
    t.value = f"{get_current_firm_name()} — DAILY CASH & BANK DAYBOOK ({daybook_data['date']})"
    t.font = Font(name="Calibri", size=13, bold=True, color="FFFFFF")
    t.fill = PatternFill(start_color=PINE_DARK, end_color=PINE_DARK, fill_type="solid")
    t.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 28

    # Summary row
    ws.merge_cells("A2:H2")
    s = ws["A2"]
    s.value = (f"Day Total Credit: ₹ {daybook_data['total_credit']:,.2f} | "
               f"Day Total Debit: ₹ {daybook_data['total_debit']:,.2f} | "
               f"Net Day Cashflow: ₹ {daybook_data['net_day_change']:,.2f} "
               f"(Cash In: ₹ {daybook_data['day_cash_in']:,.2f}, Cash Out: ₹ {daybook_data['day_cash_out']:,.2f})")
    s.font = Font(name="Calibri", size=10, bold=True, color="163F37")
    s.fill = PatternFill(start_color=PINE_LIGHT, end_color=PINE_LIGHT, fill_type="solid")
    s.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 22

    headers = [
        "S.No", "Voucher No", "Type", "Site", "Party / Narration",
        "Category", "Mode / Ref", "Amount (₹)"
    ]
    for col_idx, h in enumerate(headers, start=1):
        c = ws.cell(row=4, column=col_idx)
        apply_header_style(c, h, bg_color="1F2937", text_color="FFFFFF", font_size=10, bold=True)
        apply_cell_border(c)
    ws.row_dimensions[4].height = 24

    row = 5
    for idx, tx in enumerate(daybook_data['transactions'], start=1):
        ws.cell(row=row, column=1, value=idx).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=2, value=tx['voucher_no']).alignment = Alignment(horizontal="center")

        t_type = ws.cell(row=row, column=3, value=tx['tx_type'])
        t_type.alignment = Alignment(horizontal="center")
        t_type.font = Font(bold=True, color="059669" if tx['tx_type'] == 'CREDIT' else "DC2626")

        ws.cell(row=row, column=4, value=f"{tx['site_code']} - {tx['site_name']}")
        ws.cell(row=row, column=5, value=f"{tx['party_name']} ({tx['narration'] or ''})".strip(" ()"))
        ws.cell(row=row, column=6, value=tx['category'])
        ws.cell(row=row, column=7, value=f"{tx['payment_mode']} {tx['reference_no'] or ''}".strip())

        amt_cell = ws.cell(row=row, column=8, value=tx['amount'])
        amt_cell.number_format = "#,##0.00"
        amt_cell.font = Font(bold=True, color="059669" if tx['tx_type'] == 'CREDIT' else "DC2626")

        for col_idx in range(1, 9):
            apply_cell_border(ws.cell(row=row, column=col_idx))
        ws.row_dimensions[row].height = 20
        row += 1

    auto_fit_columns(ws, max_widths={'E': 38, 'F': 25})
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
