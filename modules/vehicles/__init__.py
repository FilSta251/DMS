# -*- coding: utf-8 -*-
"""
Modul Vozidla - Správa motorek
"""
from .modules_vehicles import VehiclesModule
from .vehicle_form import VehicleFormDialog
from .vehicle_detail import VehicleDetailWindow
from .vehicle_service_history import VehicleServiceHistoryWidget
from .vehicle_documents import VehicleDocumentsWidget
from .vehicle_photos import VehiclePhotosWidget
from .vehicle_reminders import VehicleRemindersWidget
from .vehicle_export import VehicleExporter
from .vehicle_import import VehicleImporter
from .vehicle_analytics import VehicleAnalyticsWidget
from .vehicle_widgets import (
    VehicleDialog,
    VehicleSearchDialog,
    VehicleQuickAddDialog,
    STKReminderWidget,
    VehicleCard,
    VehicleSelector,
    MileageUpdateDialog
)

__all__ = [
    'VehiclesModule',
    'VehicleFormDialog',
    'VehicleDetailWindow',
    'VehicleServiceHistoryWidget',
    'VehicleDocumentsWidget',
    'VehiclePhotosWidget',
    'VehicleRemindersWidget',
    'VehicleExporter',
    'VehicleImporter',
    'VehicleAnalyticsWidget',
    'VehicleDialog',
    'VehicleSearchDialog',
    'VehicleQuickAddDialog',
    'STKReminderWidget',
    'VehicleCard',
    'VehicleSelector',
    'MileageUpdateDialog'
]
