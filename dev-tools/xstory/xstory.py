#!/usr/bin/env python3
"""
Xstory v1.2 - PySide6 Migration
A desktop app to explore story-tree databases.
Uses PySide6 (Qt for Python) under the LGPL v3 license.

PySide6 License: LGPL v3 (https://www.gnu.org/licenses/lgpl-3.0.html)
Qt for Python: https://www.qt.io/qt-for-python
"""

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QTreeWidget, QTreeWidgetItem, QSplitter, QGroupBox, QCheckBox,
        QPushButton, QLabel, QTextEdit, QDialog, QDialogButtonBox,
        QFileDialog, QMessageBox, QScrollArea, QFrame, QStatusBar,
        QMenu, QLineEdit
    )
    from PySide6.QtCore import Qt, Signal, QSize
    from PySide6.QtGui import QBrush, QColor, QFont, QAction, QPixmap, QPainter, QPen, QIcon
except ImportError:
    print("Error: PySide6 is required. Install with: pip install PySide6")
    sys.exit(1)

# Status colors (21-status rainbow system - optimized for visibility)
STATUS_COLORS = {
    'infeasible': '#CC0000',   # Deep Red
    'rejected': '#CC3300',     # Red-Orange
    'wishlist': '#CC6600',     # Pumpkin Orange
    'concept': '#CC9900',      # Goldenrod
    'broken': '#CCCC00',       # Dark Gold / Olive
    'blocked': '#99CC00',      # Lime Green
    'refine': '#66CC00',       # Chartreuse
    'deferred': '#00CC00',     # Pure Green
    'approved': '#00CC33',     # Spring Green
    'planned': '#00CC66',      # Emerald
    'queued': '#00CC99',       # Teal Green
    'paused': '#00CCCC',       # Dark Cyan
    'active': '#0099CC',       # Cerulean
    'reviewing': '#0066CC',    # Azure
    'implemented': '#0000CC',  # Pure Blue
    'ready': '#3300CC',        # Electric Indigo
    'polish': '#6600CC',       # Violet
    'released': '#9900CC',     # Purple
    'legacy': '#CC00CC',       # Magenta
    'deprecated': '#CC0099',   # Fuchsia
    'archived': '#CC0066',     # Deep Pink
}

# All possible statuses (21-status rainbow system - canonical order)
ALL_STATUSES = [
    'infeasible', 'rejected', 'wishlist',
    'concept', 'broken', 'blocked', 'refine',
    'deferred', 'approved', 'planned', 'queued', 'paused',
    'active', 'reviewing',
    'implemented',
    'ready', 'polish', 'released',
    'legacy', 'deprecated', 'archived'
]

# Designer mode transitions (approval, quality, priority, end-of-life decisions)
DESIGNER_TRANSITIONS = {
    'infeasible': ['concept', 'wishlist', 'archived'],
    'rejected': ['concept', 'wishlist', 'archived'],
    'wishlist': ['concept', 'rejected', 'archived'],
    'concept': ['approved', 'rejected', 'wishlist', 'refine'],
    'refine': ['concept', 'rejected', 'wishlist'],
    'deferred': ['approved', 'wishlist', 'rejected'],
    'approved': ['deferred', 'rejected'],
    'blocked': ['deferred'],
    'planned': ['deferred', 'approved'],
    'paused': ['deferred'],
    'reviewing': ['implemented'],
    'implemented': ['ready'],
    'ready': ['released', 'polish'],
    'polish': ['ready', 'released'],
    'released': ['polish', 'legacy'],
    'legacy': ['deprecated', 'released', 'archived'],
    'deprecated': ['archived', 'legacy'],
    'archived': ['deprecated', 'wishlist'],
}

# Engineer mode transitions (workflow, blockers, bugs, progress)
ENGINEER_TRANSITIONS = {
    'approved': ['planned'],
    'blocked': ['planned', 'queued'],
    'planned': ['queued', 'blocked'],
    'queued': ['active', 'blocked', 'paused', 'planned'],
    'broken': ['active', 'paused', 'blocked', 'queued'],
    'paused': ['active', 'queued', 'blocked'],
    'active': ['reviewing', 'paused', 'broken', 'blocked'],
    'reviewing': ['active', 'broken'],
    'implemented': ['reviewing', 'broken'],
    'ready': ['reviewing'],
    'polish': ['reviewing'],
    'released': ['broken'],
}


def create_checkbox_pixmap(color_hex: str, checked: bool) -> QPixmap:
    """Create a custom checkbox pixmap with white checkmark on colored background."""
    size = 18
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    if checked:
        # Draw colored background with border
        painter.setBrush(QBrush(QColor(color_hex)))
        painter.setPen(QPen(QColor(color_hex), 1))
        painter.drawRoundedRect(0, 0, size-1, size-1, 3, 3)

        # Draw white checkmark
        painter.setPen(QPen(QColor(Qt.white), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        # Checkmark path
        painter.drawLine(4, 9, 7, 13)
        painter.drawLine(7, 13, 14, 4)
    else:
        # Draw white background with gray border
        painter.setBrush(QBrush(QColor(Qt.white)))
        painter.setPen(QPen(QColor('#999999'), 1))
        painter.drawRoundedRect(0, 0, size-1, size-1, 3, 3)

    painter.end()
    return pixmap


class ColoredCheckBox(QCheckBox):
    """Custom checkbox with colored background and white checkmark when checked."""

    def __init__(self, text: str, color: str, parent=None):
        super().__init__(text, parent)
        self.status_color = color
        self.checkbox_size = 18
        self.checkbox_margin = 4

    def paintEvent(self, event):
        """Custom paint to draw checkbox with colored background and white checkmark."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate positions
        indicator_y = (self.height() - self.checkbox_size) // 2
        text_x = self.checkbox_margin + self.checkbox_size + 8  # 8px spacing

        # Draw custom checkbox indicator
        if self.isChecked():
            # Draw colored background
            painter.setBrush(QBrush(QColor(self.status_color)))
            painter.setPen(QPen(QColor(self.status_color), 1))
            painter.drawRoundedRect(self.checkbox_margin, indicator_y, self.checkbox_size - 1, self.checkbox_size - 1, 3, 3)

            # Draw white checkmark
            painter.setPen(QPen(QColor(Qt.white), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(self.checkbox_margin + 4, indicator_y + 9,
                           self.checkbox_margin + 7, indicator_y + 13)
            painter.drawLine(self.checkbox_margin + 7, indicator_y + 13,
                           self.checkbox_margin + 14, indicator_y + 4)
        else:
            # Draw white background with gray border
            painter.setBrush(QBrush(QColor(Qt.white)))
            painter.setPen(QPen(QColor('#999999'), 1))
            painter.drawRoundedRect(self.checkbox_margin, indicator_y, self.checkbox_size - 1, self.checkbox_size - 1, 3, 3)

        # Draw text in status color
        painter.setPen(QColor(self.status_color))
        font = self.font()
        painter.setFont(font)
        text_rect = self.rect()
        text_rect.setLeft(text_x)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())

        painter.end()

    def hitButton(self, pos):
        """Override to make the entire widget clickable."""
        return self.rect().contains(pos)

    def sizeHint(self):
        """Calculate proper size for checkbox and text."""
        fm = self.fontMetrics()
        text_width = fm.horizontalAdvance(self.text())
        width = self.checkbox_margin + self.checkbox_size + 8 + text_width + 5
        height = max(self.checkbox_size + 4, fm.height())
        return QSize(width, height)


class StoryNode:
    """Represents a story node from the database."""
    def __init__(self, id: str, title: str, status: str, capacity: Optional[int],
                 description: str = '', depth: int = 0, parent_id: Optional[str] = None,
                 notes: str = '', project_path: str = '', created_at: str = '',
                 updated_at: str = '', last_implemented: str = ''):
        self.id = id
        self.title = title
        self.status = status
        self.capacity = capacity
        self.description = description
        self.depth = depth
        self.parent_id = parent_id
        self.notes = notes
        self.project_path = project_path
        self.created_at = created_at
        self.updated_at = updated_at
        self.last_implemented = last_implemented
        self.children: List['StoryNode'] = []


class StatusChangeDialog(QDialog):
    """Dialog for entering notes when changing story status."""

    def __init__(self, parent, node_id: str, new_status: str, mandatory: bool = False):
        super().__init__(parent)
        self.node_id = node_id
        self.new_status = new_status
        self.mandatory = mandatory
        self.result_notes: Optional[str] = None

        self.setWindowTitle(f"Change Status to '{new_status}'")
        self.setFixedSize(400, 250)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Header
        header_text = f"Changing '{self.node_id}' to status: {self.new_status}"
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(header_label)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Prompt text based on status
        if self.new_status == 'approved':
            prompt_text = "Please note how high a priority this story is:"
        elif self.new_status == 'refine':
            prompt_text = "Please explain what needs to be refined (required):"
        else:
            prompt_text = "Add a note about this decision (optional):"

        layout.addWidget(QLabel(prompt_text))

        # Text area for notes
        self.notes_text = QTextEdit()
        self.notes_text.setPlaceholderText("Enter notes here...")
        layout.addWidget(self.notes_text)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_confirm)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_confirm(self):
        """Handle confirm button click."""
        notes = self.notes_text.toPlainText().strip()

        if self.mandatory and not notes:
            QMessageBox.warning(
                self,
                "Notes Required",
                f"Notes are required when changing status to '{self.new_status}'."
            )
            self.notes_text.setFocus()
            return

        self.result_notes = notes
        self.accept()

    def get_notes(self) -> Optional[str]:
        """Return the entered notes if dialog was accepted."""
        return self.result_notes


class ClickableLabel(QLabel):
    """A QLabel that emits a signal when double-clicked."""
    doubleClicked = Signal(str)

    def __init__(self, text: str, node_id: str, parent=None):
        super().__init__(text, parent)
        self.node_id = node_id
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("color: #0066CC;")

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.node_id)

    def enterEvent(self, event):
        font = self.font()
        font.setUnderline(True)
        self.setFont(font)

    def leaveEvent(self, event):
        font = self.font()
        font.setUnderline(False)
        self.setFont(font)


class DetailView(QWidget):
    """Detail view panel showing all information about a story node."""
    closeRequested = Signal()

    def __init__(self, app: 'XstoryExplorer', parent=None):
        super().__init__(parent)
        self.app = app
        self.history: List[str] = []
        self.history_index: int = -1
        self.current_node_id: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the detail view UI."""
        main_layout = QVBoxLayout(self)

        # Navigation toolbar
        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton("< Back")
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setFixedWidth(80)
        nav_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton("Forward >")
        self.forward_btn.clicked.connect(self._go_forward)
        self.forward_btn.setFixedWidth(80)
        nav_layout.addWidget(self.forward_btn)

        nav_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self._close)
        close_btn.setFixedWidth(80)
        nav_layout.addWidget(close_btn)

        main_layout.addLayout(nav_layout)

        # Scrollable content area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)

        scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(scroll_area)

        self._update_nav_buttons()

    def show_node(self, node_id: str, add_to_history: bool = True):
        """Display details for a specific node."""
        if node_id not in self.app.nodes:
            return

        self.current_node_id = node_id
        node = self.app.nodes[node_id]

        # Update history
        if add_to_history:
            if self.history_index < len(self.history) - 1:
                self.history = self.history[:self.history_index + 1]
            self.history.append(node_id)
            self.history_index = len(self.history) - 1

        self._update_nav_buttons()

        # Clear content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Node ID and Title header
        id_label = QLabel(node.id)
        id_label.setStyleSheet("font-weight: bold; font-size: 14pt;")
        self.content_layout.addWidget(id_label)

        title_label = QLabel(node.title)
        title_label.setStyleSheet("font-size: 12pt;")
        title_label.setWordWrap(True)
        self.content_layout.addWidget(title_label)

        self._add_separator()

        # Status with color
        status_color = STATUS_COLORS.get(node.status, '#000000')
        self._add_field("Status", node.status, color=status_color)

        # Capacity
        capacity_text = str(node.capacity) if node.capacity is not None else "dynamic"
        self._add_field("Capacity", capacity_text)

        # Depth
        self._add_field("Depth", str(node.depth))

        self._add_separator()

        # Parent (clickable)
        if node.parent_id:
            self._add_link_field("Parent", node.parent_id)
        else:
            self._add_field("Parent", "(none)")

        # Children (clickable list)
        if node.children:
            children_label = QLabel("Children:")
            children_label.setStyleSheet("font-weight: bold;")
            self.content_layout.addWidget(children_label)

            for child in node.children:
                self._add_child_link(child)
        else:
            self._add_field("Children", "(none)")

        self._add_separator()

        # Description
        self._add_text_field("Description", node.description or "(no description)")

        # Notes
        if node.notes:
            self._add_text_field("Notes", node.notes)

        # Project path
        if node.project_path:
            self._add_field("Project Path", node.project_path)

        self._add_separator()

        # Timestamps
        if node.created_at:
            self._add_field("Created", node.created_at)
        if node.updated_at:
            self._add_field("Updated", node.updated_at)
        if node.last_implemented:
            self._add_field("Last Implemented", node.last_implemented)

        # Add stretch at the end
        self.content_layout.addStretch()

    def _add_separator(self):
        """Add a horizontal line separator."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.content_layout.addWidget(line)

    def _add_field(self, label: str, value: str, color: Optional[str] = None):
        """Add a simple label: value field."""
        row_layout = QHBoxLayout()
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold;")
        label_widget.setFixedWidth(120)
        row_layout.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setWordWrap(True)
        if color:
            value_widget.setStyleSheet(f"color: {color};")
        row_layout.addWidget(value_widget)
        row_layout.addStretch()

        self.content_layout.addLayout(row_layout)

    def _add_link_field(self, label: str, node_id: str):
        """Add a clickable link field."""
        row_layout = QHBoxLayout()
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold;")
        label_widget.setFixedWidth(120)
        row_layout.addWidget(label_widget)

        node = self.app.nodes.get(node_id)
        link_text = node_id
        if node:
            title = node.title[:40] + '...' if len(node.title) > 40 else node.title
            link_text = f"{node_id} - {title}"

        link = ClickableLabel(link_text, node_id)
        link.doubleClicked.connect(self.show_node)
        row_layout.addWidget(link)
        row_layout.addStretch()

        self.content_layout.addLayout(row_layout)

    def _add_child_link(self, child: StoryNode):
        """Add a clickable child link."""
        title = child.title[:50] + '...' if len(child.title) > 50 else child.title
        link_text = f"  {child.id} [{child.status}] - {title}"

        link = ClickableLabel(link_text, child.id)
        link.doubleClicked.connect(self.show_node)
        self.content_layout.addWidget(link)

    def _add_text_field(self, label: str, text: str):
        """Add a multi-line text field that expands to fit content."""
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold;")
        self.content_layout.addWidget(label_widget)

        text_widget = QLabel(text)
        text_widget.setWordWrap(True)
        text_widget.setTextInteractionFlags(Qt.TextSelectableByMouse)
        text_widget.setStyleSheet(
            "background-color: #f5f5f5; padding: 8px; border-radius: 4px;"
        )
        self.content_layout.addWidget(text_widget)

    def _update_nav_buttons(self):
        """Update the state of navigation buttons."""
        self.back_btn.setEnabled(self.history_index > 0)
        self.forward_btn.setEnabled(self.history_index < len(self.history) - 1)

    def _go_back(self):
        """Navigate to previous node in history."""
        if self.history_index > 0:
            self.history_index -= 1
            self.show_node(self.history[self.history_index], add_to_history=False)

    def _go_forward(self):
        """Navigate to next node in history."""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.show_node(self.history[self.history_index], add_to_history=False)

    def _close(self):
        """Close detail view and return to tree view."""
        self.closeRequested.emit()

    def reset_history(self):
        """Reset navigation history."""
        self.history.clear()
        self.history_index = -1
        self.current_node_id = None


class XstoryExplorer(QMainWindow):
    """Main application class."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Xstory v1.2 (PySide6)")
        self.setGeometry(100, 100, 1000, 700)

        self.db_path: Optional[str] = None
        self.nodes: Dict[str, StoryNode] = {}
        self.status_checkboxes: Dict[str, QCheckBox] = {}
        self.tree_items: Dict[str, QTreeWidgetItem] = {}  # Maps node_id to QTreeWidgetItem
        self.current_role: str = 'designer'  # 'designer' or 'engineer'

        self._setup_ui()
        self._try_auto_detect_db()

    def _setup_ui(self):
        """Set up the user interface."""
        # Central widget with stacked layout for switching views
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        self.open_btn = QPushButton("Open Database...")
        self.open_btn.clicked.connect(self._open_database)
        toolbar_layout.addWidget(self.open_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh)
        toolbar_layout.addWidget(self.refresh_btn)

        self.db_label = QLabel("No database loaded")
        toolbar_layout.addWidget(self.db_label)
        toolbar_layout.addStretch()

        # Role toggle button
        self.role_toggle_btn = QPushButton("Designer")
        self.role_toggle_btn.setCheckable(True)
        self.role_toggle_btn.setFixedWidth(100)
        self.role_toggle_btn.clicked.connect(self._toggle_role)
        self._update_role_button()
        toolbar_layout.addWidget(self.role_toggle_btn)

        self.main_layout.addLayout(toolbar_layout)

        # Container for switchable views
        self.view_container = QWidget()
        self.view_layout = QVBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(0, 0, 0, 0)

        # Tree view frame
        self.tree_view_frame = QWidget()
        tree_view_layout = QVBoxLayout(self.tree_view_frame)
        tree_view_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for tree and filters
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Tree view
        tree_container = QWidget()
        tree_container_layout = QVBoxLayout(tree_container)
        tree_container_layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Status", "Title"])
        self.tree.setColumnCount(3)
        self.tree.setColumnWidth(0, 180)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 400)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_tree_right_click)
        self.tree.itemSelectionChanged.connect(self._on_tree_select)
        self.tree.itemDoubleClicked.connect(self._on_tree_double_click)

        tree_container_layout.addWidget(self.tree)
        splitter.addWidget(tree_container)

        # Right panel: Filters
        filter_group = QGroupBox("Status Filters")
        filter_layout = QVBoxLayout(filter_group)

        # Select All / None buttons
        btn_layout = QHBoxLayout()
        all_btn = QPushButton("All")
        all_btn.clicked.connect(self._select_all_statuses)
        all_btn.setFixedWidth(60)
        btn_layout.addWidget(all_btn)

        none_btn = QPushButton("None")
        none_btn.clicked.connect(self._select_no_statuses)
        none_btn.setFixedWidth(60)
        btn_layout.addWidget(none_btn)
        btn_layout.addStretch()
        filter_layout.addLayout(btn_layout)

        # Status checkboxes (with custom colored indicators)
        for status in ALL_STATUSES:
            color = STATUS_COLORS.get(status, '#000000')

            # Create custom checkbox with colored background
            cb = ColoredCheckBox(status, color)
            cb.setChecked(True)

            # Hide the default indicator since we draw everything custom
            cb.setStyleSheet("""
                QCheckBox::indicator {
                    width: 0px;
                    height: 0px;
                }
            """)

            # Connect state change to trigger repaint and apply filters
            cb.stateChanged.connect(lambda state, checkbox=cb: (checkbox.update(), self._apply_filters()))

            self.status_checkboxes[status] = cb
            filter_layout.addWidget(cb)

        filter_layout.addStretch()
        splitter.addWidget(filter_group)

        # Set splitter proportions (3:1)
        splitter.setSizes([750, 250])
        tree_view_layout.addWidget(splitter)

        # Description panel at bottom of tree view
        desc_group = QGroupBox("Description (double-click node for details)")
        desc_layout = QVBoxLayout(desc_group)
        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(100)
        desc_layout.addWidget(self.desc_text)
        tree_view_layout.addWidget(desc_group)

        self.view_layout.addWidget(self.tree_view_frame)

        # Detail view frame
        self.detail_view = DetailView(self)
        self.detail_view.closeRequested.connect(self.show_tree_view)
        self.view_layout.addWidget(self.detail_view)

        self.main_layout.addWidget(self.view_container)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Show tree view by default
        self.show_tree_view()

    def show_tree_view(self):
        """Switch to tree view."""
        self.detail_view.hide()
        self.tree_view_frame.show()
        # Show toolbar buttons
        self.open_btn.show()
        self.refresh_btn.show()
        self.setWindowTitle("Xstory v1.2 (PySide6)")
        msg = f"Loaded {len(self.nodes)} nodes" if self.nodes else "Ready"
        self.status_bar.showMessage(msg)

    def show_detail_view(self, node_id: str):
        """Switch to detail view for a specific node."""
        self.tree_view_frame.hide()
        # Hide toolbar buttons
        self.open_btn.hide()
        self.refresh_btn.hide()
        self.detail_view.show()
        self.detail_view.show_node(node_id)
        self.setWindowTitle("Feature Details")
        node = self.nodes.get(node_id)
        if node:
            self.status_bar.showMessage(f"Viewing: {node_id} - {node.title}")

    def _on_tree_select(self):
        """Handle tree selection to show description."""
        items = self.tree.selectedItems()
        if not items:
            return

        item = items[0]
        node_id = item.text(0)
        node = self.nodes.get(node_id)

        if node:
            desc = node.description if node.description else '(no description)'
            self.desc_text.setPlainText(desc)

    def _on_tree_double_click(self, item: QTreeWidgetItem, column: int):
        """Handle double-click to open detail view."""
        node_id = item.text(0)
        if node_id in self.nodes:
            self.detail_view.reset_history()
            self.show_detail_view(node_id)

    def _on_tree_right_click(self, position):
        """Handle right-click to show context menu."""
        item = self.tree.itemAt(position)
        if not item:
            return

        node_id = item.text(0)
        node = self.nodes.get(node_id)
        if not node:
            return

        menu = QMenu(self)

        # Header showing current status and role
        header_action = QAction(f"[{node.status}] — {self.current_role.title()} mode", self)
        header_action.setEnabled(False)
        menu.addAction(header_action)
        menu.addSeparator()

        # Get available transitions based on current role
        if self.current_role == 'designer':
            transitions = DESIGNER_TRANSITIONS.get(node.status, [])
        else:
            transitions = ENGINEER_TRANSITIONS.get(node.status, [])

        if transitions:
            for target_status in transitions:
                action = QAction(f"→ {target_status}", self)
                action.triggered.connect(
                    lambda checked, ns=target_status: self._change_node_status(node_id, ns)
                )
                menu.addAction(action)
        else:
            no_options = QAction("(no transitions available)", self)
            no_options.setEnabled(False)
            menu.addAction(no_options)

        menu.exec(self.tree.mapToGlobal(position))

    def _change_node_status(self, node_id: str, new_status: str):
        """Change a node's status with a notes dialog."""
        node = self.nodes.get(node_id)
        if not node:
            return

        # Determine if notes are mandatory
        mandatory = (new_status == 'refine')

        # Show dialog
        dialog = StatusChangeDialog(self, node_id, new_status, mandatory=mandatory)
        if dialog.exec() == QDialog.Accepted:
            notes = dialog.get_notes()
            self._update_node_status_in_db(node_id, new_status, notes or '')

    def _update_node_status_in_db(self, node_id: str, new_status: str, notes: str):
        """Update node status and notes in the database."""
        if not self.db_path:
            QMessageBox.critical(self, "Error", "No database loaded.")
            return

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get current notes to append to
            cursor.execute("SELECT notes FROM story_nodes WHERE id = ?", (node_id,))
            row = cursor.fetchone()
            current_notes = row[0] if row and row[0] else ""

            # Build new notes with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

            if notes:
                new_note_entry = f"[{timestamp}] Status changed to '{new_status}': {notes}"
            else:
                new_note_entry = f"[{timestamp}] Status changed to '{new_status}'"

            if current_notes:
                updated_notes = f"{current_notes}\n{new_note_entry}"
            else:
                updated_notes = new_note_entry

            # Update status and notes
            cursor.execute(
                "UPDATE story_nodes SET status = ?, notes = ?, updated_at = ? WHERE id = ?",
                (new_status, updated_notes, datetime.now().isoformat(), node_id)
            )

            conn.commit()
            conn.close()

            self.status_bar.showMessage(f"Updated '{node_id}' status to '{new_status}'")

            # Refresh the tree to show updated status
            self._refresh()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update status:\n{e}")

    def _toggle_role(self):
        """Toggle between Designer and Engineer modes."""
        if self.current_role == 'designer':
            self.current_role = 'engineer'
        else:
            self.current_role = 'designer'
        self._update_role_button()
        self.status_bar.showMessage(f"Switched to {self.current_role.title()} mode")

    def _update_role_button(self):
        """Update the role toggle button appearance."""
        if self.current_role == 'designer':
            self.role_toggle_btn.setText("Designer")
            self.role_toggle_btn.setChecked(False)
            self.role_toggle_btn.setStyleSheet(
                "QPushButton { background-color: #9900CC; color: white; font-weight: bold; }"
                "QPushButton:hover { background-color: #7700AA; }"
            )
        else:
            self.role_toggle_btn.setText("Engineer")
            self.role_toggle_btn.setChecked(True)
            self.role_toggle_btn.setStyleSheet(
                "QPushButton { background-color: #0099CC; color: white; font-weight: bold; }"
                "QPushButton:hover { background-color: #0077AA; }"
            )

    def _try_auto_detect_db(self):
        """Try to auto-detect the database file."""
        possible_paths = [
            Path(__file__).parent.parent.parent / '.claude' / 'data' / 'story-tree.db',
            Path.cwd() / '.claude' / 'data' / 'story-tree.db',
            Path.cwd().parent / '.claude' / 'data' / 'story-tree.db',
        ]

        for path in possible_paths:
            if path.exists():
                self._load_database(str(path.resolve()))
                return

        self.status_bar.showMessage("No database auto-detected. Use 'Open Database...' to load one.")

    def _open_database(self):
        """Open a database file via file dialog."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Story Tree Database",
            str(Path.cwd()),
            "SQLite Database (*.db);;All Files (*.*)"
        )
        if path:
            self._load_database(path)

    def _load_database(self, path: str):
        """Load a database file."""
        if not os.path.exists(path):
            QMessageBox.critical(self, "Error", f"Database file not found:\n{path}")
            return

        self.db_path = path
        self.db_label.setText(os.path.basename(path))
        self._refresh()

    def _refresh(self):
        """Refresh the tree from the database."""
        if not self.db_path:
            return

        try:
            self._load_nodes_from_db()
            self._apply_filters()
            self.status_bar.showMessage(f"Loaded {len(self.nodes)} nodes from {os.path.basename(self.db_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load database:\n{e}")
            self.status_bar.showMessage(f"Error: {e}")

    def _load_nodes_from_db(self):
        """Load all nodes from the database."""
        self.nodes.clear()

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = """
            SELECT
                s.id, s.title, s.status, s.capacity, s.description,
                s.notes, s.project_path, s.created_at, s.updated_at, s.last_implemented,
                COALESCE(
                    (SELECT MIN(depth) FROM story_paths WHERE descendant_id = s.id AND ancestor_id != s.id),
                    0
                ) as depth,
                (SELECT ancestor_id FROM story_paths WHERE descendant_id = s.id AND depth = 1) as parent_id
            FROM story_nodes s
            ORDER BY s.id
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        for row in rows:
            node = StoryNode(
                id=row['id'],
                title=row['title'] or '',
                status=row['status'] or 'concept',
                capacity=row['capacity'],
                description=row['description'] or '',
                depth=row['depth'] or 0,
                parent_id=row['parent_id'],
                notes=row['notes'] or '',
                project_path=row['project_path'] or '',
                created_at=row['created_at'] or '',
                updated_at=row['updated_at'] or '',
                last_implemented=row['last_implemented'] or ''
            )
            self.nodes[node.id] = node

        conn.close()

        # Build parent-child relationships
        for node in self.nodes.values():
            if node.parent_id and node.parent_id in self.nodes:
                self.nodes[node.parent_id].children.append(node)

        # Sort children by ID
        for node in self.nodes.values():
            node.children.sort(key=lambda n: self._sort_key(n.id))

    def _sort_key(self, node_id: str) -> Tuple:
        """Generate a sort key for node IDs (root first, then numeric order)."""
        if node_id == 'root':
            return (0,)
        try:
            parts = node_id.split('.')
            return (1,) + tuple(int(p) for p in parts)
        except ValueError:
            return (2, node_id)

    def _get_ancestors(self, node_id: str) -> set:
        """Get all ancestor node IDs for a given node."""
        ancestors = set()
        node = self.nodes.get(node_id)
        while node and node.parent_id:
            ancestors.add(node.parent_id)
            node = self.nodes.get(node.parent_id)
        return ancestors

    def _apply_filters(self):
        """Apply status filters and color the tree."""
        visible_statuses = {s for s, cb in self.status_checkboxes.items() if cb.isChecked()}

        # Step 1: Find all nodes that directly match the filter
        matching_nodes = {node_id for node_id, node in self.nodes.items()
                         if node.status in visible_statuses}

        # Step 2: Collect ancestors of all matching nodes
        ancestor_nodes = set()
        for node_id in matching_nodes:
            ancestor_nodes.update(self._get_ancestors(node_id))

        # Nodes to show = matching nodes + their ancestors
        visible_nodes = matching_nodes | ancestor_nodes
        # Ancestor-only nodes (shown faded)
        faded_nodes = ancestor_nodes - matching_nodes

        # Clear the tree
        self.tree.clear()
        self.tree_items.clear()

        # Find root nodes that are visible
        root_nodes = [n for n in self.nodes.values()
                     if (not n.parent_id or n.parent_id not in self.nodes)
                     and n.id in visible_nodes]
        root_nodes.sort(key=lambda n: self._sort_key(n.id))

        # Build filtered tree
        for node in root_nodes:
            self._add_filtered_node(node, None, visible_nodes, faded_nodes)

        # Expand all nodes
        self.tree.expandAll()

    def _add_filtered_node(self, node: StoryNode, parent_item: Optional[QTreeWidgetItem],
                           visible_nodes: set, faded_nodes: set):
        """Add a node to the filtered tree with appropriate coloring."""
        if node.id not in visible_nodes:
            return

        # Create tree item
        item = QTreeWidgetItem([node.id, node.status, node.title])

        # Get status color
        status_color = STATUS_COLORS.get(node.status, '#000000')

        if node.id in faded_nodes:
            # Faded ancestor: gray text for ID and Title, keep status color
            gray_brush = QBrush(QColor('#999999'))
            status_brush = QBrush(QColor(status_color))

            item.setForeground(0, gray_brush)  # ID column
            item.setForeground(1, status_brush)  # Status column
            item.setForeground(2, gray_brush)  # Title column

            # Set italic font for faded items
            italic_font = QFont()
            italic_font.setItalic(True)
            item.setFont(0, italic_font)
            item.setFont(2, italic_font)
        else:
            # Normal node: colored status, black ID and title
            black_brush = QBrush(QColor('#000000'))
            status_brush = QBrush(QColor(status_color))

            item.setForeground(0, black_brush)  # ID column
            item.setForeground(1, status_brush)  # Status column
            item.setForeground(2, black_brush)  # Title column

        # Add to tree
        if parent_item:
            parent_item.addChild(item)
        else:
            self.tree.addTopLevelItem(item)

        # Store reference
        self.tree_items[node.id] = item

        # Add visible children
        visible_children = [c for c in node.children if c.id in visible_nodes]
        visible_children.sort(key=lambda n: self._sort_key(n.id))

        for child in visible_children:
            self._add_filtered_node(child, item, visible_nodes, faded_nodes)

    def _select_all_statuses(self):
        """Select all status filters."""
        for cb in self.status_checkboxes.values():
            cb.setChecked(True)

    def _select_no_statuses(self):
        """Deselect all status filters."""
        for cb in self.status_checkboxes.values():
            cb.setChecked(False)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = XstoryExplorer()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
