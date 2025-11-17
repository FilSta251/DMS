# -*- coding: utf-8 -*-
"""
Widget pro číselník typů vozidel
Zatím jen jednoduchý základ, aby aplikace běžela.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class VehicleTypesWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        label = QLabel("Tady budou typy vozidel (zatím prázdné).")
        layout.addWidget(label)

    def refresh(self):
        """Obnovení dat – zatím nic nedělá."""
        pass

    def get_count(self):
        """Počet položek – zatím 0, protože nic nemáme."""
        return 0

    def export_data(self):
        """Export dat – zatím prázdný seznam."""
        return []

    def import_data(self, data):
        """Import dat – zatím nic nedělá."""
        pass
