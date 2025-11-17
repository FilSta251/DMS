# -*- coding: utf-8 -*-
"""
Detail vozidla - komplexní zobrazení s historií servisů a statistikami
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem, QPushButton,
    QHeaderView, QFrame, QGridLayout, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QBrush
from datetime import datetime, date, timedelta
import config
from database_manager import db


class VehicleDetailWindow(QDialog):
    """Okno s detailním zobrazením vozidla"""

    def __init__(self, parent=None, vehicle_id=None):
        super().__init__(parent)
        self.vehicle_id = vehicle_id
        self.vehicle_data = None
        self.load_vehicle_data()
        self.init_ui()

    def load_vehicle_data(self):
        """Načtení kompletních dat vozidla"""
        try:
            self.vehicle_data = db.fetch_one("""
                SELECT v.*,
                       c.first_name || ' ' || c.last_name as customer_name,
                       c.phone as customer_phone,
                       c.email as customer_email,
                       c.company as customer_company,
                       c.address as customer_address,
                       c.city as customer_city,
                       c.id as cust_id
                FROM vehicles v
                LEFT JOIN customers c ON v.customer_id = c.id
                WHERE v.id = ?
            """, (self.vehicle_id,))
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se načíst data vozidla:\n{e}")

    def init_ui(self):
        """Inicializace uživatelského rozhraní"""
        if not self.vehicle_data:
            self.reject()
            return

        self.setWindowTitle(f"🏍️ Detail vozidla - {self.vehicle_data['license_plate']}")
        self.setMinimumWidth(900)
        self.setMinimumHeight(700)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTabWidget::pane {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3498db;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Hlavička s SPZ a rychlými akcemi
        header = self.create_header()
        layout.addWidget(header)

        # Tabs
        tabs = QTabWidget()

        # Tab 1: Základní údaje
        tab_basic = self.create_basic_tab()
        tabs.addTab(tab_basic, "📋 Základní údaje")

        # Tab 2: Historie servisů
        tab_history = self.create_history_tab()
        tabs.addTab(tab_history, "🔧 Historie servisů")

        # Tab 3: Statistiky
        tab_stats = self.create_stats_tab()
        tabs.addTab(tab_stats, "📊 Statistiky")

        # Tab 4: Dokumenty
        tab_docs = self.create_documents_tab()
        tabs.addTab(tab_docs, "📄 Dokumenty")

        layout.addWidget(tabs)

        # Spodní tlačítka
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        btn_edit = QPushButton("✏️ Upravit vozidlo")
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SECONDARY};
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #2980b9;
            }}
        """)
        btn_edit.clicked.connect(self.edit_vehicle)
        buttons_layout.addWidget(btn_edit)

        btn_close = QPushButton("✅ Zavřít")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_close.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_close)

        layout.addLayout(buttons_layout)

    def create_header(self):
        """Vytvoření hlavičky s SPZ a rychlými akcemi"""
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                padding: 15px;
            }
        """)

        layout = QHBoxLayout(header)

        # SPZ velký
        spz_label = QLabel(self.vehicle_data['license_plate'])
        spz_font = QFont()
        spz_font.setPointSize(24)
        spz_font.setBold(True)
        spz_label.setFont(spz_font)
        spz_label.setStyleSheet("color: #2c3e50;")
        layout.addWidget(spz_label)

        # Značka a model
        brand_model = QLabel(f"{self.vehicle_data['brand']} {self.vehicle_data['model']}")
        brand_model_font = QFont()
        brand_model_font.setPointSize(16)
        brand_model.setFont(brand_model_font)
        brand_model.setStyleSheet("color: #7f8c8d; margin-left: 20px;")
        layout.addWidget(brand_model)

        layout.addStretch()

        # Rychlé akce
        btn_new_order = QPushButton("📋 Nová zakázka")
        btn_new_order.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_SUCCESS};
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #219a52;
            }}
        """)
        btn_new_order.clicked.connect(self.create_order)
        layout.addWidget(btn_new_order)

        btn_schedule = QPushButton("🗓️ Naplánovat servis")
        btn_schedule.setStyleSheet(f"""
            QPushButton {{
                background-color: {config.COLOR_WARNING};
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #e67e22;
            }}
        """)
        btn_schedule.clicked.connect(self.schedule_service)
        layout.addWidget(btn_schedule)

        return header

    def create_basic_tab(self):
        """Tab se základními údaji"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Horní část - dva sloupce
        top_layout = QHBoxLayout()

        # Levý sloupec - údaje o vozidle
        vehicle_group = QGroupBox("🏍️ Údaje o vozidle")
        vehicle_layout = QFormLayout(vehicle_group)
        vehicle_layout.setSpacing(10)

        vehicle_layout.addRow("SPZ:", self.create_value_label(self.vehicle_data['license_plate']))
        vehicle_layout.addRow("Značka:", self.create_value_label(self.vehicle_data['brand']))
        vehicle_layout.addRow("Model:", self.create_value_label(self.vehicle_data['model']))
        vehicle_layout.addRow("Rok výroby:", self.create_value_label(
            str(self.vehicle_data['year']) if self.vehicle_data['year'] else 'Neuvedeno'
        ))
        vehicle_layout.addRow("VIN:", self.create_value_label(self.vehicle_data['vin'] or 'Neuvedeno'))
        vehicle_layout.addRow("Barva:", self.create_value_label(self.vehicle_data['color'] or 'Neuvedeno'))
        vehicle_layout.addRow("Typ motoru:", self.create_value_label(self.vehicle_data['engine_type'] or 'Neuvedeno'))
        vehicle_layout.addRow("Palivo:", self.create_value_label(self.vehicle_data['fuel_type'] or 'Neuvedeno'))

        # Stav km
        if self.vehicle_data['mileage']:
            mileage_text = f"{self.vehicle_data['mileage']:,} km".replace(",", " ")
        else:
            mileage_text = "Neuvedeno"
        vehicle_layout.addRow("Stav km:", self.create_value_label(mileage_text))

        # STK s barevným pozadím
        stk_label = self.create_stk_label()
        vehicle_layout.addRow("STK platná do:", stk_label)

        top_layout.addWidget(vehicle_group)

        # Pravý sloupec - údaje o zákazníkovi
        customer_group = QGroupBox("👤 Majitel vozidla")
        customer_layout = QFormLayout(customer_group)
        customer_layout.setSpacing(10)

        if self.vehicle_data['customer_id']:
            customer_layout.addRow("Jméno:", self.create_value_label(self.vehicle_data['customer_name'] or ''))
            customer_layout.addRow("Firma:", self.create_value_label(self.vehicle_data['customer_company'] or 'Neuvedeno'))
            customer_layout.addRow("Telefon:", self.create_value_label(self.vehicle_data['customer_phone'] or 'Neuvedeno'))
            customer_layout.addRow("Email:", self.create_value_label(self.vehicle_data['customer_email'] or 'Neuvedeno'))
            customer_layout.addRow("Adresa:", self.create_value_label(
                f"{self.vehicle_data['customer_address'] or ''}, {self.vehicle_data['customer_city'] or ''}".strip(', ')
            ))

            # Tlačítko pro přechod na zákazníka
            btn_customer = QPushButton("👁️ Zobrazit zákazníka")
            btn_customer.setStyleSheet(f"""
                QPushButton {{
                    background-color: {config.COLOR_SECONDARY};
                    color: white;
                    padding: 8px 15px;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: #2980b9;
                }}
            """)
            btn_customer.clicked.connect(self.show_customer)
            customer_layout.addRow("", btn_customer)
        else:
            no_customer = QLabel("Vozidlo nemá přiřazeného zákazníka")
            no_customer.setStyleSheet("color: #e74c3c; font-style: italic; padding: 20px;")
            no_customer.setAlignment(Qt.AlignmentFlag.AlignCenter)
            customer_layout.addRow(no_customer)

        top_layout.addWidget(customer_group)
        layout.addLayout(top_layout)

        # Poznámky
        if self.vehicle_data['notes']:
            notes_group = QGroupBox("📝 Poznámky")
            notes_layout = QVBoxLayout(notes_group)

            notes_text = QTextEdit()
            notes_text.setPlainText(self.vehicle_data['notes'])
            notes_text.setReadOnly(True)
            notes_text.setMaximumHeight(100)
            notes_text.setStyleSheet("""
                QTextEdit {
                    background-color: #fafafa;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)
            notes_layout.addWidget(notes_text)

            layout.addWidget(notes_group)

        layout.addStretch()
        return tab

    def create_value_label(self, text):
        """Vytvoření labelu s hodnotou"""
        label = QLabel(str(text))
        label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                padding: 5px;
                background-color: #fafafa;
                border-radius: 3px;
            }
        """)
        return label

    def create_stk_label(self):
        """Vytvoření labelu pro STK s barevným pozadím"""
        label = QLabel()

        if self.vehicle_data['stk_valid_until']:
            try:
                stk_date = datetime.strptime(str(self.vehicle_data['stk_valid_until']), "%Y-%m-%d").date()
                label.setText(stk_date.strftime("%d.%m.%Y"))

                today = date.today()
                warning_date = today + timedelta(days=30)

                if stk_date < today:
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #e74c3c;
                            color: white;
                            padding: 8px;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                    """)
                    label.setText(f"⚠️ NEPLATNÁ - {stk_date.strftime('%d.%m.%Y')}")
                elif stk_date <= warning_date:
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #f39c12;
                            color: white;
                            padding: 8px;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                    """)
                    days_left = (stk_date - today).days
                    label.setText(f"⚠️ Expiruje za {days_left} dní - {stk_date.strftime('%d.%m.%Y')}")
                else:
                    label.setStyleSheet("""
                        QLabel {
                            background-color: #27ae60;
                            color: white;
                            padding: 8px;
                            border-radius: 5px;
                            font-weight: bold;
                        }
                    """)
                    label.setText(f"✅ Platná do {stk_date.strftime('%d.%m.%Y')}")
            except:
                label.setText("Neplatné datum")
        else:
            label.setText("Neuvedeno")
            label.setStyleSheet("""
                QLabel {
                    font-size: 13px;
                    padding: 5px;
                    background-color: #fafafa;
                    border-radius: 3px;
                    color: #95a5a6;
                }
            """)

        return label

    def create_history_tab(self):
        """Tab s historií servisů"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)

        # Načtení historie zakázek
        orders = db.fetch_all("""
            SELECT
                o.order_number,
                o.order_type,
                o.status,
                o.created_date,
                o.completed_date,
                o.total_price,
                o.note
            FROM orders o
            WHERE o.vehicle_id = ?
            ORDER BY o.created_date DESC
        """, (self.vehicle_id,))

        if orders:
            # Statistiky
            stats_frame = QFrame()
            stats_frame.setStyleSheet("""
                QFrame {
                    background-color: #ecf0f1;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            stats_layout = QHBoxLayout(stats_frame)

            total_orders = len(orders)
            total_spent = sum(o['total_price'] or 0 for o in orders)

            stats_layout.addWidget(QLabel(f"<b>Celkem zakázek:</b> {total_orders}"))
            stats_layout.addWidget(QLabel(f"<b>Celková útrata:</b> {total_spent:,.0f} Kč".replace(",", " ")))
            stats_layout.addStretch()

            layout.addWidget(stats_frame)

            # Tabulka
            table = QTableWidget()
            table.setColumnCount(7)
            table.setHorizontalHeaderLabels([
                "Číslo zakázky", "Typ", "Stav", "Vytvořeno", "Dokončeno", "Cena", "Poznámka"
            ])
            table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            table.setAlternatingRowColors(True)

            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)

            for order in orders:
                row = table.rowCount()
                table.insertRow(row)

                table.setItem(row, 0, QTableWidgetItem(order['order_number'] or ''))
                table.setItem(row, 1, QTableWidgetItem(order['order_type'] or ''))

                # Stav s barvou
                status_item = QTableWidgetItem(order['status'] or '')
                status_color = config.ORDER_STATUS_COLORS.get(order['status'], '#95a5a6')
                status_item.setBackground(QBrush(QColor(status_color)))
                status_item.setForeground(QBrush(QColor("white")))
                table.setItem(row, 2, status_item)

                # Datum vytvoření
                if order['created_date']:
                    try:
                        created = datetime.strptime(str(order['created_date']), "%Y-%m-%d").strftime("%d.%m.%Y")
                    except:
                        created = str(order['created_date'])
                else:
                    created = ''
                table.setItem(row, 3, QTableWidgetItem(created))

                # Datum dokončení
                if order['completed_date']:
                    try:
                        completed = datetime.strptime(str(order['completed_date']), "%Y-%m-%d").strftime("%d.%m.%Y")
                    except:
                        completed = str(order['completed_date'])
                else:
                    completed = ''
                table.setItem(row, 4, QTableWidgetItem(completed))

                # Cena
                price = order['total_price'] or 0
                table.setItem(row, 5, QTableWidgetItem(f"{price:,.0f} Kč".replace(",", " ")))

                # Poznámka
                note = order['note'] or ''
                if len(note) > 50:
                    note = note[:47] + "..."
                table.setItem(row, 6, QTableWidgetItem(note))

            layout.addWidget(table)
        else:
            no_history = QLabel("Vozidlo zatím nemá žádnou historii servisů.")
            no_history.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_history.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 14px;
                    padding: 50px;
                }
            """)
            layout.addWidget(no_history)

        layout.addStretch()
        return tab

    def create_stats_tab(self):
        """Tab se statistikami"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Načtení statistik
        orders = db.fetch_all("""
            SELECT
                o.total_price,
                o.created_date,
                o.completed_date,
                o.order_type
            FROM orders o
            WHERE o.vehicle_id = ?
            ORDER BY o.created_date
        """, (self.vehicle_id,))

        if orders:
            # Grid se statistikami
            stats_grid = QGridLayout()
            stats_grid.setSpacing(15)

            # Celkový počet zakázek
            total_orders = len(orders)
            stats_grid.addWidget(self.create_stat_card("📋 Celkem zakázek", str(total_orders), "#3498db"), 0, 0)

            # Celková útrata
            total_spent = sum(o['total_price'] or 0 for o in orders)
            stats_grid.addWidget(self.create_stat_card("💰 Celková útrata", f"{total_spent:,.0f} Kč".replace(",", " "), "#27ae60"), 0, 1)

            # Průměrná cena zakázky
            avg_price = total_spent / total_orders if total_orders > 0 else 0
            stats_grid.addWidget(self.create_stat_card("📊 Průměrná zakázka", f"{avg_price:,.0f} Kč".replace(",", " "), "#f39c12"), 0, 2)

            # Poslední servis
            last_service = "Nikdy"
            for o in reversed(orders):
                if o['completed_date']:
                    try:
                        last_date = datetime.strptime(str(o['completed_date']), "%Y-%m-%d")
                        last_service = last_date.strftime("%d.%m.%Y")
                        break
                    except:
                        pass
            stats_grid.addWidget(self.create_stat_card("🔧 Poslední servis", last_service, "#9b59b6"), 0, 3)

            # Typ zakázek
            order_types = {}
            for o in orders:
                otype = o['order_type'] or 'Jiný'
                order_types[otype] = order_types.get(otype, 0) + 1

            most_common = max(order_types.items(), key=lambda x: x[1]) if order_types else ('Žádný', 0)
            stats_grid.addWidget(self.create_stat_card("📈 Nejčastější typ", f"{most_common[0]} ({most_common[1]}x)", "#e74c3c"), 1, 0)

            # Roční útrata
            current_year = datetime.now().year
            yearly_spent = sum(
                o['total_price'] or 0 for o in orders
                if o['created_date'] and str(o['created_date']).startswith(str(current_year))
            )
            stats_grid.addWidget(self.create_stat_card(f"📅 Útrata {current_year}", f"{yearly_spent:,.0f} Kč".replace(",", " "), "#1abc9c"), 1, 1)

            layout.addLayout(stats_grid)

            # Info o vozidle
            vehicle_age = ""
            if self.vehicle_data['year']:
                age = datetime.now().year - self.vehicle_data['year']
                vehicle_age = f"Stáří vozidla: {age} let"

            if vehicle_age:
                age_label = QLabel(vehicle_age)
                age_label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        color: #7f8c8d;
                        padding: 10px;
                    }
                """)
                layout.addWidget(age_label)
        else:
            no_stats = QLabel("Zatím nejsou k dispozici žádné statistiky.\nVozidlo nemá žádnou historii zakázek.")
            no_stats.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_stats.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 14px;
                    padding: 50px;
                }
            """)
            layout.addWidget(no_stats)

        layout.addStretch()
        return tab

    def create_stat_card(self, label, value, color):
        """Vytvoření karty se statistikou"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(5)

        value_label = QLabel(value)
        value_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(label)
        text_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 11px;
            }
        """)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(text_label)

        return card

    def create_documents_tab(self):
        """Tab s dokumenty"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        placeholder = QLabel(
            "📄 Správa dokumentů bude k dispozici v příští verzi.\n\n"
            "Budete moci ukládat:\n"
            "• Technický průkaz\n"
            "• Protokoly STK\n"
            "• Pojistné smlouvy\n"
            "• Fotografie vozidla\n"
            "• Servisní knížky"
        )
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet("""
            QLabel {
                color: #7f8c8d;
                font-size: 14px;
                padding: 50px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(placeholder)

        return tab

    def edit_vehicle(self):
        """Editace vozidla"""
        from .vehicle_form import VehicleFormDialog

        dialog = VehicleFormDialog(self, vehicle_id=self.vehicle_id)
        if dialog.exec():
            self.load_vehicle_data()
            # Refresh UI - zjednodušená verze
            QMessageBox.information(
                self,
                "Úspěch",
                "Vozidlo bylo upraveno.\nZavřete a znovu otevřete detail pro zobrazení změn."
            )

    def show_customer(self):
        """Přechod na zákazníka"""
        main_window = self.window()
        if hasattr(main_window, 'switch_module'):
            main_window.switch_module('customers')
            self.accept()

    def create_order(self):
        """Vytvoření nové zakázky"""
        try:
            from modules.orders.order_form import OrderFormDialog

            dialog = OrderFormDialog(
                order_type="Zakázka",
                vehicle_id=self.vehicle_id,
                parent=self
            )

            if dialog.exec():
                QMessageBox.information(
                    self,
                    "Úspěch",
                    "Zakázka byla vytvořena.\nMůžete ji najít v modulu Zakázky."
                )

                main_window = self.window()
                if hasattr(main_window, 'switch_module'):
                    main_window.switch_module('orders')
                    self.accept()
        except ImportError:
            QMessageBox.information(
                self,
                "Informace",
                "Modul zakázek není k dispozici.\nPřejděte prosím do modulu Zakázky."
            )
        except Exception as e:
            QMessageBox.critical(self, "Chyba", f"Nepodařilo se vytvořit zakázku:\n{e}")

    def schedule_service(self):
        """Naplánování servisu"""
        main_window = self.window()
        if hasattr(main_window, 'switch_module'):
            main_window.switch_module('calendar')
            self.accept()
        else:
            QMessageBox.information(
                self,
                "Informace",
                "Funkce plánování servisu bude implementována v modulu Kalendář."
            )
