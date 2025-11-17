# -*- coding: utf-8 -*-
"""
Export zakázek - PROFESIONÁLNÍ VERZE
Zakázkový list, proforma, faktura
"""

from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtCore import QStandardPaths
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os
import config
from database_manager import db


class OrderExporter:
    """Třída pro export zakázek do PDF"""

    def __init__(self):
        # Registrace fontu pro češtinu
        try:
            # Pokus o registraci DejaVu fontu
            pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', 'DejaVuSans-Bold.ttf'))
            self.font_name = 'DejaVu'
            self.font_bold = 'DejaVu-Bold'
        except:
            # Fallback na standardní font
            self.font_name = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def export_work_order(self, order_id, parent=None):
        """Export zakázkového listu"""
        try:
            # Načtení dat
            order_data = self.get_order_data(order_id)
            if not order_data:
                QMessageBox.warning(parent, "Chyba", "Zakázka nenalezena!")
                return False

            # Dialog pro uložení
            default_filename = f"zakazkovy_list_{order_data['order_number']}.pdf"
            default_dir = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )

            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Uložit zakázkový list jako PDF",
                os.path.join(default_dir, default_filename),
                "PDF soubory (*.pdf)"
            )

            if not file_path:
                return False

            # Vytvoření PDF
            self.create_work_order_pdf(file_path, order_data)

            QMessageBox.information(
                parent,
                "Úspěch",
                f"Zakázkový list byl vyexportován do:\n{file_path}"
            )

            # Otevření souboru
            try:
                os.startfile(file_path)  # Windows
            except:
                pass

            return True

        except Exception as e:
            QMessageBox.critical(parent, "Chyba", f"Chyba při exportu:\n{str(e)}")
            return False

    def export_proforma(self, order_id, parent=None):
        """Export proformy"""
        try:
            order_data = self.get_order_data(order_id)
            if not order_data:
                QMessageBox.warning(parent, "Chyba", "Zakázka nenalezena!")
                return False

            default_filename = f"proforma_{order_data['order_number']}.pdf"
            default_dir = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )

            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Uložit proformu jako PDF",
                os.path.join(default_dir, default_filename),
                "PDF soubory (*.pdf)"
            )

            if not file_path:
                return False

            self.create_proforma_pdf(file_path, order_data)

            QMessageBox.information(
                parent,
                "Úspěch",
                f"Proforma byla vyexportována do:\n{file_path}"
            )

            try:
                os.startfile(file_path)
            except:
                pass

            return True

        except Exception as e:
            QMessageBox.critical(parent, "Chyba", f"Chyba:\n{str(e)}")
            return False

    def export_invoice(self, order_id, parent=None):
        """Export faktury"""
        try:
            order_data = self.get_order_data(order_id)
            if not order_data:
                QMessageBox.warning(parent, "Chyba", "Zakázka nenalezena!")
                return False

            # Generování čísla faktury
            invoice_number = self.generate_invoice_number()

            default_filename = f"faktura_{invoice_number}.pdf"
            default_dir = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )

            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Uložit fakturu jako PDF",
                os.path.join(default_dir, default_filename),
                "PDF soubory (*.pdf)"
            )

            if not file_path:
                return False

            self.create_invoice_pdf(file_path, order_data, invoice_number)

            QMessageBox.information(
                parent,
                "Úspěch",
                f"Faktura č. {invoice_number} byla vyexportována do:\n{file_path}"
            )

            try:
                os.startfile(file_path)
            except:
                pass

            return True

        except Exception as e:
            QMessageBox.critical(parent, "Chyba", f"Chyba:\n{str(e)}")
            return False

    def get_order_data(self, order_id):
        """Načtení kompletních dat zakázky"""
        try:
            # Základní info o zakázce
            order = db.execute_query(
                """SELECT
                    o.order_number, o.order_type, o.status,
                    o.created_date, o.completed_date, o.note, o.total_price,
                    c.first_name, c.last_name, c.phone, c.email,
                    c.address, c.city, c.postal_code, c.ico, c.dic, c.company,
                    v.brand, v.model, v.license_plate, v.vin,
                    v.year, v.color, v.engine_type, v.mileage
                FROM orders o
                LEFT JOIN customers c ON o.customer_id = c.id
                LEFT JOIN vehicles v ON o.vehicle_id = v.id
                WHERE o.id = ?""",
                [order_id]
            )

            if not order or len(order) == 0:
                return None

            order = order[0]

            # Položky zakázky
            items = db.execute_query(
                """SELECT item_type, name, quantity, unit, unit_price, vat_rate, total_price
                   FROM order_items WHERE order_id = ? ORDER BY item_type, id""",
                [order_id]
            )

            # Nastavení firmy
            settings = self.get_company_settings()

            return {
                'order_number': order[0],
                'order_type': order[1],
                'status': order[2],
                'created_date': order[3] or datetime.now().strftime('%Y-%m-%d'),
                'completed_date': order[4] or '',
                'note': order[5] or '',
                'total_price': order[6] or 0,
                'customer': {
                    'first_name': order[7] or '',
                    'last_name': order[8] or '',
                    'name': f"{order[7] or ''} {order[8] or ''}".strip(),
                    'phone': order[9] or '',
                    'email': order[10] or '',
                    'address': order[11] or '',
                    'city': order[12] or '',
                    'postal_code': order[13] or '',
                    'full_address': self._format_address(order[11], order[12], order[13]),
                    'ico': order[14] or '',
                    'dic': order[15] or '',
                    'company': order[16] or ''
                },
                'vehicle': {
                    'brand': order[17] or '',
                    'model': order[18] or '',
                    'license_plate': order[19] or '',
                    'vin': order[20] or '',
                    'year': order[21] or '',
                    'color': order[22] or '',
                    'engine_type': order[23] or '',
                    'mileage': order[24] or 0,
                    'full_name': f"{order[17] or ''} {order[18] or ''}".strip()
                },
                'items': items or [],
                'settings': settings
            }

        except Exception as e:
            print(f"Chyba při načítání dat: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_company_settings(self):
        """Načtení nastavení firmy"""
        try:
            settings_data = db.execute_query("SELECT key, value FROM settings")
            settings = {}

            if settings_data:
                for s in settings_data:
                    settings[s[0]] = s[1] or ''

            # Výchozí hodnoty
            return {
                'company_name': settings.get('company_name', 'Motoservis DMS'),
                'company_address': settings.get('company_address', ''),
                'company_phone': settings.get('company_phone', ''),
                'company_email': settings.get('company_email', ''),
                'company_ico': settings.get('company_ico', ''),
                'company_dic': settings.get('company_dic', ''),
            }
        except:
            return {
                'company_name': 'Motoservis DMS',
                'company_address': '',
                'company_phone': '',
                'company_email': '',
                'company_ico': '',
                'company_dic': ''
            }

    def _format_address(self, address, city, postal_code):
        """Formátování adresy"""
        parts = []
        if address:
            parts.append(address)
        if postal_code and city:
            parts.append(f"{postal_code} {city}")
        elif city:
            parts.append(city)
        return ', '.join(parts) if parts else ''

    def create_work_order_pdf(self, file_path, data):
        """Vytvoření zakázkového listu - PROFESIONÁLNÍ"""
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # === HLAVIČKA ===
        c.setFont(self.font_bold, 18)
        c.drawString(30, height - 40, "ZAKÁZKOVÝ LIST")

        c.setFont(self.font_name, 10)
        c.drawString(30, height - 58, f"Zakázka č.: {data['order_number']}")

        # Datum a čas
        c.setFont(self.font_name, 9)
        c.drawString(width - 150, height - 40, f"Datum: {data['created_date']}")
        c.drawString(width - 150, height - 54, f"Stav: {data['status']}")

        # Linka pod hlavičkou
        c.setLineWidth(2)
        c.line(30, height - 70, width - 30, height - 70)

        # === INFORMACE O SERVISU ===
        y = height - 100
        c.setFont(self.font_bold, 11)
        c.drawString(30, y, "SERVIS:")

        c.setFont(self.font_name, 9)
        y -= 15
        c.drawString(30, y, data['settings']['company_name'])

        if data['settings']['company_address']:
            y -= 12
            c.drawString(30, y, data['settings']['company_address'])

        if data['settings']['company_phone']:
            y -= 12
            c.drawString(30, y, f"Tel.: {data['settings']['company_phone']}")

        if data['settings']['company_ico']:
            y -= 12
            c.drawString(30, y, f"IČO: {data['settings']['company_ico']}")

        # === ZÁKAZNÍK ===
        y = height - 100
        c.setFont(self.font_bold, 11)
        c.drawString(300, y, "ZÁKAZNÍK:")

        c.setFont(self.font_name, 9)
        y -= 15

        if data['customer']['company']:
            c.drawString(300, y, data['customer']['company'])
            y -= 12

        c.drawString(300, y, data['customer']['name'])
        y -= 12

        if data['customer']['full_address']:
            c.drawString(300, y, data['customer']['full_address'])
            y -= 12

        if data['customer']['phone']:
            c.drawString(300, y, f"Tel.: {data['customer']['phone']}")
            y -= 12

        if data['customer']['ico']:
            c.drawString(300, y, f"IČO: {data['customer']['ico']}")

        # === VOZIDLO ===
        y = height - 240
        c.setLineWidth(1)
        c.rect(30, y - 60, width - 60, 80)

        c.setFont(self.font_bold, 11)
        c.drawString(40, y + 10, "VOZIDLO")

        c.setFont(self.font_name, 9)
        y -= 5

        c.drawString(40, y, f"Model: {data['vehicle']['full_name']}")
        c.drawString(300, y, f"SPZ: {data['vehicle']['license_plate']}")

        y -= 15
        c.drawString(40, y, f"VIN: {data['vehicle']['vin']}")
        c.drawString(300, y, f"Rok: {data['vehicle']['year']}")

        y -= 15
        c.drawString(40, y, f"Barva: {data['vehicle']['color']}")
        c.drawString(300, y, f"Stav km: {data['vehicle']['mileage']}")

        y -= 15
        c.drawString(40, y, f"Motor: {data['vehicle']['engine_type']}")

        # === POLOŽKY ZAKÁZKY ===
        y -= 50
        c.setFont(self.font_bold, 11)
        c.drawString(30, y, "POPIS PRACÍ A MATERIÁLU:")

        y -= 20

        # Tabulka
        table_data = [['Č.', 'Typ', 'Popis', 'Množ.', 'Jedn.', 'Cena/j', 'Celkem']]

        for idx, item in enumerate(data['items'], 1):
            table_data.append([
                str(idx),
                item[0][:10],  # item_type
                item[1][:40],   # name
                f"{item[2]:.2f}",  # quantity
                item[3],  # unit
                f"{item[4]:.2f}",  # unit_price
                f"{item[6]:.2f}"  # total_price
            ])

        # Prázdné řádky pokud je položek méně než 10
        while len(table_data) < 12:
            table_data.append(['', '', '', '', '', '', ''])

        table = Table(table_data, colWidths=[25, 50, 200, 45, 35, 60, 70])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 0), (6, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        table.wrapOn(c, width, height)
        table_height = len(table_data) * 18
        table.drawOn(c, 30, y - table_height)

        # === CELKOVÁ CENA ===
        y = y - table_height - 30
        c.setFont(self.font_bold, 14)
        c.drawString(width - 200, y, f"CELKEM: {data['total_price']:.2f} Kč")

        # === POZNÁMKA ===
        if data['note']:
            y -= 30
            c.setFont(self.font_bold, 10)
            c.drawString(30, y, "Poznámka:")

            c.setFont(self.font_name, 9)
            y -= 15

            # Zalamování textu
            note_lines = self._wrap_text(data['note'], 90)
            for line in note_lines[:3]:  # Max 3 řádky
                c.drawString(30, y, line)
                y -= 12

        # === TERMÍN A PODPISY ===
        y = 120
        c.setFont(self.font_bold, 9)
        c.drawString(30, y, "Předpokládaný termín dokončení:")
        c.setFont(self.font_name, 9)
        c.drawString(190, y, data['completed_date'] if data['completed_date'] else '_______________')

        # Podpisy
        y = 70
        c.setFont(self.font_name, 8)
        c.line(30, y, 150, y)
        c.drawString(30, y - 12, "Servisní poradce")

        c.line(width - 180, y, width - 30, y)
        c.drawString(width - 180, y - 12, "Podpis zákazníka")

        # === PATIČKA ===
        c.setFont(self.font_name, 7)
        c.setFillColor(colors.grey)
        c.drawString(30, 35, f"Vytištěno: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        c.drawString(30, 25, "Zakázkový list uschovejte do vydání vozidla!")
        c.drawString(width - 150, 25, config.APP_NAME)

        c.save()

    def create_proforma_pdf(self, file_path, data):
        """Vytvoření proformy"""
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Hlavička
        c.setFont(self.font_bold, 20)
        c.drawString(30, height - 40, "PROFORMA")

        c.setFont(self.font_name, 10)
        c.drawString(30, height - 60, f"K zakázce č.: {data['order_number']}")
        c.drawString(width - 150, height - 40, f"Datum: {datetime.now().strftime('%d.%m.%Y')}")

        # Linka
        c.setLineWidth(2)
        c.line(30, height - 75, width - 30, height - 75)

        # Dodavatel
        y = height - 105
        c.setFont(self.font_bold, 11)
        c.drawString(30, y, "Dodavatel:")
        c.setFont(self.font_name, 9)
        y -= 15
        c.drawString(30, y, data['settings']['company_name'])
        y -= 12
        if data['settings']['company_address']:
            c.drawString(30, y, data['settings']['company_address'])
            y -= 12
        if data['settings']['company_ico']:
            c.drawString(30, y, f"IČO: {data['settings']['company_ico']}")

        # Odběratel
        y = height - 105
        c.setFont(self.font_bold, 11)
        c.drawString(300, y, "Odběratel:")
        c.setFont(self.font_name, 9)
        y -= 15
        c.drawString(300, y, data['customer']['name'])
        y -= 12
        if data['customer']['full_address']:
            c.drawString(300, y, data['customer']['full_address'])

        # Položky
        y = height - 220
        table_data = [['Popis', 'Množ.', 'Jedn.', 'Cena', 'Celkem']]

        total_without_vat = 0
        total_vat = 0

        for item in data['items']:
            price_without_vat = item[6] / (1 + (item[5] or 21) / 100)
            vat_amount = item[6] - price_without_vat

            total_without_vat += price_without_vat
            total_vat += vat_amount

            table_data.append([
                item[1][:50],
                f"{item[2]:.2f}",
                item[3],
                f"{item[4]:.2f} Kč",
                f"{item[6]:.2f} Kč"
            ])

        table = Table(table_data, colWidths=[280, 60, 50, 80, 90])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), self.font_bold),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        table.wrapOn(c, width, height)
        table_height = len(table_data) * 22
        table.drawOn(c, 30, y - table_height)

        # Rekapitulace
        y = y - table_height - 40
        c.setFont(self.font_bold, 10)
        c.drawString(width - 250, y, f"Cena bez DPH:")
        c.drawString(width - 120, y, f"{total_without_vat:.2f} Kč")

        y -= 15
        c.drawString(width - 250, y, f"DPH:")
        c.drawString(width - 120, y, f"{total_vat:.2f} Kč")

        y -= 20
        c.setFont(self.font_bold, 14)
        c.drawString(width - 250, y, f"CELKEM:")
        c.drawString(width - 120, y, f"{data['total_price']:.2f} Kč")

        # Patička
        c.setFont(self.font_name, 8)
        c.drawString(30, 30, f"Toto je nezávazná cenová nabídka.")

        c.save()

    def create_invoice_pdf(self, file_path, data, invoice_number):
        """Vytvoření faktury"""
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # Hlavička
        c.setFont(self.font_bold, 22)
        c.drawString(30, height - 40, "FAKTURA")

        c.setFont(self.font_bold, 12)
        c.drawString(30, height - 60, f"č. {invoice_number}")

        c.setFont(self.font_name, 9)
        c.drawString(width - 180, height - 40, f"Datum vystavení: {datetime.now().strftime('%d.%m.%Y')}")
        c.drawString(width - 180, height - 54, f"Datum splatnosti: ___________")

        # Zbytek podobný jako proforma, ale s bankovním spojením, atd.

        c.save()

    def generate_invoice_number(self):
        """Generování čísla faktury"""
        year = datetime.now().year

        # Počet faktur v roce (toto by mělo být v samostatné tabulce invoices)
        # Pro jednoduchost použijeme zakázky
        count = db.execute_query(
            "SELECT COUNT(*) FROM orders WHERE created_date LIKE ?",
            [f"{year}%"]
        )

        next_num = count[0][0] + 1 if count and len(count) > 0 else 1
        return f"FAK{year}{next_num:04d}"

    def _wrap_text(self, text, max_length):
        """Zalamování textu"""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for word in words:
            if current_length + len(word) + 1 <= max_length:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def export_work_order_with_data(self, order_id, form_data, parent=None):
        """Export zakázkového listu s daty z editoru"""
        try:
            # Načtení základních dat ze zakázky
            order_data = self.get_order_data(order_id)

            if not order_data:
                QMessageBox.warning(parent, "Chyba", "Zakázka nenalezena!")
                return False

            # Spojení dat ze zakázky a z formuláře
            merged_data = {**order_data, **form_data}

            # Dialog pro uložení
            default_filename = f"zakazkovy_list_{order_data['order_number']}.pdf"
            default_dir = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )

            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Uložit zakázkový list jako PDF",
                os.path.join(default_dir, default_filename),
                "PDF soubory (*.pdf)"
            )

            if not file_path:
                return False

            # Vytvoření PDF s daty z formuláře
            self.create_work_order_pdf_with_form_data(file_path, merged_data, form_data)

            QMessageBox.information(
                parent,
                "Úspěch",
                f"Zakázkový list byl vyexportován do:\n{file_path}"
            )

            # Otevření souboru
            try:
                os.startfile(file_path)
            except:
                pass

            return True

        except Exception as e:
            QMessageBox.critical(parent, "Chyba", f"Chyba při exportu:\n{str(e)}")
            return False

    def create_work_order_pdf_with_form_data(self, file_path, order_data, form_data):
        """Vytvoření zakázkového listu s daty z formuláře"""
        c = canvas.Canvas(file_path, pagesize=A4)
        width, height = A4

        # === HLAVIČKA ===
        c.setFont(self.font_bold, 18)
        c.drawString(30, height - 40, "ZAKÁZKOVÝ LIST")

        c.setFont(self.font_name, 10)
        c.drawString(30, height - 58, f"Zakázka č.: {form_data.get('order_number', order_data['order_number'])}")

        # Datum
        c.setFont(self.font_name, 9)
        c.drawString(width - 150, height - 40, f"Datum: {form_data.get('date_received', '')}")

        # Linka
        c.setLineWidth(2)
        c.line(30, height - 70, width - 30, height - 70)

        # === SERVIS ===
        y = height - 100
        c.setFont(self.font_bold, 11)
        c.drawString(30, y, "SERVIS:")

        c.setFont(self.font_name, 9)
        y -= 15
        c.drawString(30, y, order_data['settings']['company_name'])

        if order_data['settings']['company_address']:
            y -= 12
            c.drawString(30, y, order_data['settings']['company_address'])

        # === ZÁKAZNÍK ===
        y = height - 100
        c.setFont(self.font_bold, 11)
        c.drawString(300, y, "ZÁKAZNÍK:")

        c.setFont(self.font_name, 9)
        y -= 15
        c.drawString(300, y, form_data.get('customer', '---'))

        # === VOZIDLO ===
        y = height - 180
        c.setLineWidth(1)
        c.rect(30, y - 60, width - 60, 80)

        c.setFont(self.font_bold, 11)
        c.drawString(40, y + 10, "VOZIDLO")

        c.setFont(self.font_name, 9)
        y -= 5
        c.drawString(40, y, form_data.get('vehicle', '---'))

        y -= 15
        c.drawString(40, y, f"Stav PHM: {form_data.get('fuel_level', '---')}")
        c.drawString(300, y, f"Stav km: {form_data.get('mileage', '---')}")

        # === VÝBAVA ===
        y -= 30
        c.setFont(self.font_bold, 10)
        c.drawString(30, y, "Výbava vozidla / viditelná poškození:")

        y -= 15
        c.setFont(self.font_name, 8)
        equipment = form_data.get('equipment', '')
        if equipment:
            lines = self._wrap_text(equipment, 100)
            for line in lines[:2]:
                c.drawString(30, y, line)
                y -= 10

        # === POPIS PRACÍ ===
        y -= 30
        c.setFont(self.font_bold, 11)
        c.drawString(30, y, "POPIS PRACÍ / POŽADAVKY ZÁKAZNÍKA:")

        y -= 20
        c.setFont(self.font_name, 8)
        work_desc = form_data.get('work_description', '')
        if work_desc:
            lines = self._wrap_text(work_desc, 100)
            for line in lines[:15]:
                if y < 300:
                    break
                c.drawString(30, y, line)
                y -= 12

        # === ROZŠÍŘENÍ ZAKÁZKY ===
        y = 280
        c.setFont(self.font_bold, 10)
        c.drawString(30, y, "ROZŠÍŘENÍ ZAKÁZKY / VYJÁDŘENÍ OPRAVNY:")

        y -= 15
        c.setFont(self.font_name, 8)
        extension = form_data.get('extension', '')
        if extension:
            lines = self._wrap_text(extension, 100)
            for line in lines[:8]:
                c.drawString(30, y, line)
                y -= 10
        else:
            for i in range(5):
                c.line(30, y, width - 30, y)
                y -= 15

        # === PŘEDBĚŽNÁ CENA ===
        y = 150
        c.setFont(self.font_bold, 11)
        c.drawString(30, y, "Předběžný termín dokončení:")
        c.drawString(300, y, form_data.get('date_estimated', '---'))

        y -= 20
        c.setFont(self.font_bold, 11)
        c.drawString(30, y, "Odhad ceny vč. DPH:")
        c.drawString(300, y, f"{form_data.get('estimated_price', '---')} Kč")

        # === PODPISY ===
        y = 80
        c.setFont(self.font_name, 8)
        c.line(30, y, 150, y)
        c.drawString(30, y - 12, "Servisní poradce")

        c.line(width - 180, y, width - 30, y)
        c.drawString(width - 180, y - 12, "Podpis zákazníka")

        # === PATIČKA ===
        c.setFont(self.font_name, 7)
        c.setFillColor(colors.grey)
        c.drawString(30, 35, f"Vytištěno: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        c.drawString(30, 25, "Zakázkový list uschovejte do vydání vozidla!")

        c.save()

# Globální instance exportéru
exporter = OrderExporter()

def export_work_order_with_data(self, order_id, form_data, parent=None):
        """Export zakázkového listu s daty z editoru"""
        try:
            # Načtení základních dat ze zakázky
            order_data = self.get_order_data(order_id)

            if not order_data:
                QMessageBox.warning(parent, "Chyba", "Zakázka nenalezena!")
                return False

            # Spojení dat ze zakázky a z formuláře
            merged_data = {**order_data, **form_data}

            # Dialog pro uložení
            default_filename = f"zakazkovy_list_{order_data['order_number']}.pdf"
            default_dir = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.DocumentsLocation
            )

            from PyQt6.QtWidgets import QFileDialog
            file_path, _ = QFileDialog.getSaveFileName(
                parent,
                "Uložit zakázkový list jako PDF",
                os.path.join(default_dir, default_filename),
                "PDF soubory (*.pdf)"
            )

            if not file_path:
                return False

            # Vytvoření PDF s daty z formuláře
            self.create_work_order_pdf_with_form_data(file_path, merged_data, form_data)

            QMessageBox.information(
                parent,
                "Úspěch",
                f"Zakázkový list byl vyexportován do:\n{file_path}"
            )

            # Otevření souboru
            try:
                os.startfile(file_path)
            except:
                pass

            return True

        except Exception as e:
            QMessageBox.critical(parent, "Chyba", f"Chyba při exportu:\n{str(e)}")
            return False
