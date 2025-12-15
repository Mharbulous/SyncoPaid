#!/usr/bin/env python3
"""
Story Tree Explorer v1.2 - PySide6 Implementation
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
        QTreeWidget, QTreeWidgetItem, QSplitter, QFrame, QLabel,
        QPushButton, QCheckBox, QScrollArea, QTextEdit, QDialog,
        QGroupBox, QMessageBox, QFileDialog, QMenu, QStatusBar
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QBrush, QColor, QFont, QAction
except ImportError:
    print("Error: PySide6 is required. Install with: pip install PySide6")
    sys.exit(1)

# Status colors (23-status rainbow system - optimized for visibility)
STATUS_COLORS = {
    'infeasible': '#CC0000',   # Deep Red
    'rejected': '#CC3300',     # Red-Orange
    'wishlist': '#CC6600',     # Pumpkin Orange
    'concept': '#CC9900',      # Goldenrod
    'refine': '#CCCC00',       # Dark Gold / Olive
    'approved': '#99CC00',     # Lime Green
    'epic': '#66CC00',         # Chartreuse
    'planned': '#33CC00',      # Kelly Green
    'blocked': '#00CC00',      # Pure Green
    'deferred': '#00CC33',     # Spring Green
    'queued': '#00CC66',       # Emerald
    'bugged': '#00CC99',       # Teal Green
    'paused': '#00CCCC',       # Dark Cyan
    'active': '#0099CC',       # Cerulean
    'in-progress': '#0066CC',  # Azure
    'reviewing': '#0033CC',    # Cobalt Blue
    'implemented': '#0000CC',  # Pure Blue
    'ready': '#3300CC',        # Electric Indigo
    'polish': '#6600CC',       # Violet
    'released': '#9900CC',     # Purple
    'legacy': '#CC00CC',       # Magenta
    'deprecated': '#CC0099',   # Fuchsia
    'archived': '#CC0066',     # Deep Pink
}

# All possible statuses (23-status rainbow system)
ALL_STATUSES = [
    'infeasible', 'rejected', 'wishlist',
    'concept', 'refine', 'approved', 'epic',
    'planned', 'blocked', 'deferred',
    'queued', 'bugged', 'paused',
    'active', 'in-progress',
    'reviewing', 'implemented',
    'ready', 'polish', 'released',
    'legacy', 'deprecated', 'archived'
]


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
        self.result: Optional[str] = None
        self.mandatory = mandatory
        self.node_id = node_id
        self.new_status = new_status

        self.setWindowTitle(f"Change Status to '{new_status}'")
        self.setFixedSize(400, 250)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_text = f"Changing '{self.node_id}' to status: {self.new_status}"
        header_label = QLabel(header_text)
        header_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        layout.addWidget(header_label)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Prompt text based on status
        if self.new_status == 'approved':
            prompt_text = "Please note how high a priority this story is:"
        elif self.new_status == 'revising':
            prompt_text = "Please explain what needs to be revised (required):"
        else:
            prompt_text = "Add a note about this decision (optional):"

        prompt_label = QLabel(prompt_text)
        layout.addWidget(prompt_label)

        # Text area for notes
        self.notes_text = QTextEdit()
        self.notes_text.setAcceptRichText(False)
        layout.addWidget(self.notes_text)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        confirm_btn = QPushButton("Confirm")
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self._on_cancel)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        # Focus on text area
        self.notes_text.setFocus()

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

        self.result = notes
        self.accept()

    def _on_cancel(self):
        """Handle cancel button click."""
        self.result = None
        self.reject()


class ClickableLabel(QLabel):
    """A label that can be clicked like a link."""
    clicked = Signal(str)

    def __init__(self, text: str, node_id: str, parent=None):
        super().__init__(text, parent)
        self.node_id = node_id
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet("color: #0066CC;")
        self._is_hovered = False

    def enterEvent(self, event):
        self.setStyleSheet("color: #0066CC; text-decoration: underline;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setStyleSheet("color: #0066CC;")
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.clicked.emit(self.node_id)
        super().mouseDoubleClickEvent(event)


class DetailView(QWidget):
    """Detail view panel showing all information about a story node."""
    close_requested = Signal()

    def __init__(self, app: 'StoryTreeExplorer', parent=None):
        super().__init__(parent)
        self.app = app
        self.history: List[str] = []
        self.history_index: int = -1
        self.current_node_id: Optional[str] = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the detail view UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Navigation toolbar
        nav_layout = QHBoxLayout()

        self.back_btn = QPushButton("< Back")
        self.back_btn.setFixedWidth(80)
        self.back_btn.clicked.connect(self._go_back)
        nav_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton("Forward >")
        self.forward_btn.setFixedWidth(80)
        self.forward_btn.clicked.connect(self._go_forward)
        nav_layout.addWidget(self.forward_btn)

        nav_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(80)
        close_btn.clicked.connect(self._close)
        nav_layout.addWidget(close_btn)

        main_layout.addLayout(nav_layout)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)

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
        self._add_field("Status", node.status, color=STATUS_COLORS.get(node.status))

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
            children_label.setStyleSheet("font-weight: bold; font-size: 9pt;")
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
        """Add a horizontal separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        self.content_layout.addWidget(line)

    def _add_field(self, label: str, value: str, color: Optional[str] = None):
        """Add a simple label: value field."""
        row = QHBoxLayout()

        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold; font-size: 9pt;")
        label_widget.setFixedWidth(120)
        row.addWidget(label_widget)

        value_widget = QLabel(value)
        value_widget.setWordWrap(True)
        if color:
            value_widget.setStyleSheet(f"color: {color};")
        row.addWidget(value_widget, 1)

        container = QWidget()
        container.setLayout(row)
        self.content_layout.addWidget(container)

    def _add_link_field(self, label: str, node_id: str):
        """Add a clickable link field."""
        row = QHBoxLayout()

        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold; font-size: 9pt;")
        label_widget.setFixedWidth(120)
        row.addWidget(label_widget)

        node = self.app.nodes.get(node_id)
        link_text = f"{node_id}"
        if node:
            title = node.title[:40] + '...' if len(node.title) > 40 else node.title
            link_text += f" - {title}"

        link = ClickableLabel(link_text, node_id)
        link.clicked.connect(self.show_node)
        row.addWidget(link, 1)

        container = QWidget()
        container.setLayout(row)
        self.content_layout.addWidget(container)

    def _add_child_link(self, child: StoryNode):
        """Add a clickable child link."""
        title = child.title[:50] + '...' if len(child.title) > 50 else child.title
        link_text = f"  {child.id} [{child.status}] - {title}"

        link = ClickableLabel(link_text, child.id)
        link.clicked.connect(self.show_node)
        self.content_layout.addWidget(link)

    def _add_text_field(self, label: str, text: str):
        """Add a multi-line text field."""
        label_widget = QLabel(f"{label}:")
        label_widget.setStyleSheet("font-weight: bold; font-size: 9pt;")
        self.content_layout.addWidget(label_widget)

        text_widget = QTextEdit()
        text_widget.setPlainText(text)
        text_widget.setReadOnly(True)
        text_widget.setMaximumHeight(100)
        text_widget.setStyleSheet("background-color: #f5f5f5;")
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
        self.close_requested.emit()

    def reset_history(self):
        """Reset navigation history."""
        self.history.clear()
        self.history_index = -1
        self.current_node_id = None


class StoryTreeExplorer(QMainWindow):
    """Main application class."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Story Tree Explorer v1.2 (PySide6)")
        self.setGeometry(100, 100, 1000, 700)

        self.db_path: Optional[str] = None
        self.nodes: Dict[str, StoryNode] = {}
        self.status_checkboxes: Dict[str, QCheckBox] = {}
        self.tree_items: Dict[str, QTreeWidgetItem] = {}

        self._setup_ui()
        self._try_auto_detect_db()

    def _setup_ui(self):
        """Set up the user interface."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # Top toolbar
        toolbar = QHBoxLayout()

        open_btn = QPushButton("Open Database...")
        open_btn.clicked.connect(self._open_database)
        toolbar.addWidget(open_btn)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh)
        toolbar.addWidget(refresh_btn)

        self.db_label = QLabel("No database loaded")
        toolbar.addWidget(self.db_label)
        toolbar.addStretch()

        main_layout.addLayout(toolbar)

        # Stacked container for switchable views
        self.view_container = QWidget()
        self.view_layout = QVBoxLayout(self.view_container)
        self.view_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.view_container)

        # Tree view widget
        self.tree_view_widget = QWidget()
        self._setup_tree_view()
        self.view_layout.addWidget(self.tree_view_widget)

        # Detail view widget
        self.detail_view = DetailView(self)
        self.detail_view.close_requested.connect(self.show_tree_view)
        self.view_layout.addWidget(self.detail_view)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        # Show tree view by default
        self.show_tree_view()

    def _setup_tree_view(self):
        """Set up the tree view panel."""
        layout = QVBoxLayout(self.tree_view_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for tree and filters
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: Tree widget
        tree_frame = QFrame()
        tree_layout = QVBoxLayout(tree_frame)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Status", "Title"])
        self.tree.setColumnCount(3)
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 100)
        self.tree.setColumnWidth(2, 400)
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)

        # Connect signals
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.customContextMenuRequested.connect(self._on_right_click)

        tree_layout.addWidget(self.tree)

        splitter.addWidget(tree_frame)

        # Right panel: Filters
        filter_frame = QGroupBox("Status Filters")
        filter_layout = QVBoxLayout(filter_frame)

        # Select All / None buttons
        btn_layout = QHBoxLayout()
        all_btn = QPushButton("All")
        all_btn.setFixedWidth(60)
        all_btn.clicked.connect(self._select_all_statuses)
        btn_layout.addWidget(all_btn)

        none_btn = QPushButton("None")
        none_btn.setFixedWidth(60)
        none_btn.clicked.connect(self._select_no_statuses)
        btn_layout.addWidget(none_btn)
        btn_layout.addStretch()

        filter_layout.addLayout(btn_layout)

        # Status checkboxes (with rainbow colors)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        checkbox_widget = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_widget)
        checkbox_layout.setAlignment(Qt.AlignTop)

        for status in ALL_STATUSES:
            cb = QCheckBox(status)
            cb.setChecked(True)
            color = STATUS_COLORS.get(status, '#000000')
            cb.setStyleSheet(f"color: {color}; font-weight: bold;")
            cb.stateChanged.connect(self._apply_filters)
            self.status_checkboxes[status] = cb
            checkbox_layout.addWidget(cb)

        scroll.setWidget(checkbox_widget)
        filter_layout.addWidget(scroll)

        splitter.addWidget(filter_frame)

        # Set splitter sizes (tree gets more space)
        splitter.setSizes([700, 250])

        layout.addWidget(splitter)

        # Description panel at bottom
        desc_frame = QGroupBox("Description (double-click node for details)")
        desc_layout = QVBoxLayout(desc_frame)

        self.desc_text = QTextEdit()
        self.desc_text.setReadOnly(True)
        self.desc_text.setMaximumHeight(100)
        desc_layout.addWidget(self.desc_text)

        layout.addWidget(desc_frame)

    def show_tree_view(self):
        """Switch to tree view."""
        self.detail_view.hide()
        self.tree_view_widget.show()
        if self.nodes:
            self.status_bar.showMessage(f"Loaded {len(self.nodes)} nodes")
        else:
            self.status_bar.showMessage("Ready")

    def show_detail_view(self, node_id: str):
        """Switch to detail view for a specific node."""
        self.tree_view_widget.hide()
        self.detail_view.show()
        self.detail_view.show_node(node_id)
        node = self.nodes.get(node_id)
        if node:
            self.status_bar.showMessage(f"Viewing: {node_id} - {node.title}")

    def _on_selection_changed(self):
        """Handle tree selection to show description."""
        items = self.tree.selectedItems()
        if not items:
            return

        item = items[0]
        node_id = item.text(0)  # ID is in column 0
        node = self.nodes.get(node_id)

        if node:
            desc = node.description if node.description else '(no description)'
            self.desc_text.setPlainText(desc)
        else:
            self.desc_text.clear()

    def _on_double_click(self, item: QTreeWidgetItem, column: int):
        """Handle double-click to open detail view."""
        node_id = item.text(0)
        if node_id in self.nodes:
            self.detail_view.reset_history()
            self.show_detail_view(node_id)

    def _on_right_click(self, pos):
        """Handle right-click to show context menu."""
        item = self.tree.itemAt(pos)
        if not item:
            return

        node_id = item.text(0)
        node = self.nodes.get(node_id)
        if not node:
            return

        menu = QMenu(self)

        if node.status == 'concept':
            approve_action = menu.addAction("Approve")
            approve_action.triggered.connect(lambda: self._change_node_status(node_id, 'approved'))

            reject_action = menu.addAction("Reject")
            reject_action.triggered.connect(lambda: self._change_node_status(node_id, 'rejected'))

            wishlist_action = menu.addAction("Wishlist")
            wishlist_action.triggered.connect(lambda: self._change_node_status(node_id, 'wishlist'))

            revise_action = menu.addAction("Revise")
            revise_action.triggered.connect(lambda: self._change_node_status(node_id, 'revising'))
        else:
            status_action = menu.addAction(f"Status: {node.status}")
            status_action.setEnabled(False)

        menu.exec_(self.tree.mapToGlobal(pos))

    def _change_node_status(self, node_id: str, new_status: str):
        """Change a node's status with a notes dialog."""
        node = self.nodes.get(node_id)
        if not node:
            return

        mandatory = (new_status == 'revising')

        dialog = StatusChangeDialog(self, node_id, new_status, mandatory=mandatory)
        if dialog.exec_() == QDialog.Accepted:
            notes = dialog.result
            self._update_node_status_in_db(node_id, new_status, notes)

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
            self._refresh()

        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update status:\n{e}")

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
        """Apply status filters and rebuild tree with colors."""
        visible_statuses = {s for s, cb in self.status_checkboxes.items() if cb.isChecked()}

        # Find all nodes that directly match the filter
        matching_nodes = {node_id for node_id, node in self.nodes.items()
                         if node.status in visible_statuses}

        # Collect ancestors of all matching nodes
        ancestor_nodes = set()
        for node_id in matching_nodes:
            ancestor_nodes.update(self._get_ancestors(node_id))

        visible_nodes = matching_nodes | ancestor_nodes
        faded_nodes = ancestor_nodes - matching_nodes

        # Clear tree
        self.tree.clear()
        self.tree_items.clear()

        # Find root nodes
        root_nodes = [n for n in self.nodes.values()
                      if (not n.parent_id or n.parent_id not in self.nodes)
                      and n.id in visible_nodes]
        root_nodes.sort(key=lambda n: self._sort_key(n.id))

        # Build tree
        for node in root_nodes:
            self._add_tree_node(node, None, visible_nodes, faded_nodes)

        # Expand all
        self.tree.expandAll()

    def _add_tree_node(self, node: StoryNode, parent_item: Optional[QTreeWidgetItem],
                       visible_nodes: set, faded_nodes: set):
        """Add a node to the tree with appropriate coloring."""
        if node.id not in visible_nodes:
            return

        # Create tree item
        item = QTreeWidgetItem([node.id, node.status, node.title])

        # Get colors
        status_color = STATUS_COLORS.get(node.status, '#000000')

        if node.id in faded_nodes:
            # Faded ancestor: gray text, italic
            gray = QColor('#999999')
            italic_font = QFont()
            italic_font.setItalic(True)

            for col in range(3):
                item.setForeground(col, QBrush(gray))
                item.setFont(col, italic_font)
        else:
            # Normal node: colored status, black ID and title
            item.setForeground(0, QBrush(QColor('#000000')))  # ID = black
            item.setForeground(1, QBrush(QColor(status_color)))  # Status = colored
            item.setForeground(2, QBrush(QColor('#000000')))  # Title = black

        # Add to tree
        if parent_item is None:
            self.tree.addTopLevelItem(item)
        else:
            parent_item.addChild(item)

        self.tree_items[node.id] = item

        # Add visible children
        visible_children = [c for c in node.children if c.id in visible_nodes]
        visible_children.sort(key=lambda n: self._sort_key(n.id))

        for child in visible_children:
            self._add_tree_node(child, item, visible_nodes, faded_nodes)

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
    window = StoryTreeExplorer()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
