"""Client and matter management dialogs.

This module re-exports classes from decomposed submodules for backward compatibility.
"""
from syncopaid.matter_client_csv import export_matters_csv, import_matters_csv
from syncopaid.matter_client_dialog_clients import ClientDialog, ClientEditDialog
from syncopaid.matter_client_dialog_matters import MatterDialog, MatterEditDialog

__all__ = [
    'export_matters_csv',
    'import_matters_csv',
    'ClientDialog',
    'ClientEditDialog',
    'MatterDialog',
    'MatterEditDialog',
]
